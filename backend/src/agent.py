import json
import logging
import sys
import os
import random
import re
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Ensure local module imports work seamlessly across LiveKit child processes
sys.path.append(str(Path(__file__).parent.resolve()))

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    ChatContext,
    cli,
    function_tool,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db  # SQLite database manager

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# ==========================================
# 1. IRONCLAD SYSTEM PROMPTS
# ==========================================

def get_raksha_prompt(user_name: str) -> str:
    return f"""You are Raksha, a highly empathetic AI voice agent for digital banking safety. The caller's name is {user_name}.

IDENTITY & TONE:
1. You are RAKSHA. You are a FEMALE security expert. You are NEVER Samar.
2. Speak Hindi natively in Devanagari script. Pronounce English URLs phonetically (e.g., "cyber crime dot gov dot in").
3. Speak like a warm, helpful friend (e.g., "जी बिलकुल", "घबराइए मत").
4. Keep answers to 2-3 spoken sentences. NEVER use bullet points, asterisks, or markdown.

ROUTING LOGIC (STRICT):
- If the user asks about ANY government schemes (PMJJBY, PMSBY) or explicitly asks for Samar, you MUST call `transfer_to_scheme_specialist`. Do not answer the scheme question yourself.
- If you are answering a security question, do NOT call any transfer tools. Answer it directly.
"""

def get_samar_prompt(user_name: str) -> str:
    return f"""You are Samar, a warm, patient Government Scheme Specialist. The caller's name is {user_name}.

IDENTITY & TONE:
1. You are SAMAR. You are a MALE scheme specialist. You are NEVER Raksha.
2. Speak Hindi natively in Devanagari script. 
3. Speak like a professional, friendly consultant (e.g., "जी, मैं बताता हूँ").
4. Keep answers to 2-3 spoken sentences. NEVER use bullet points, asterisks, or markdown.

ROUTING LOGIC (STRICT):
- If the user asks about fraud, scams, OTPs, or reporting crimes, YOU CANNOT HELP THEM. You MUST immediately call `transfer_back_to_raksha`.
- If the user asks about a scheme, you MUST ask for their age FIRST, then call `check_scheme_eligibility`.
"""

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def sanitize_summary(text: str) -> str:
    text = re.sub(r'\b\d{4,6}\b', '[OTP/PIN Redacted]', text)
    text = re.sub(r'\b\d{10,16}\b', '[Aadhaar/Account Redacted]', text)
    return text

def send_discord_alert(payload: dict):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url: return
    discord_data = {
        "embeds": [{
            "title": f"🚨 Human Escalation: {payload['ticket_id']}",
            "color": 15158332 if payload['urgency'].lower() == 'emergency' else 3447003,
            "fields": [
                {"name": "Caller", "value": payload['caller_id'], "inline": True},
                {"name": "Urgency", "value": payload['urgency'].upper(), "inline": True},
                {"name": "Summary", "value": payload['issue_summary'], "inline": False},
                {"name": "AI Checks Completed", "value": payload['checks_completed'], "inline": False},
            ],
            "footer": {"text": "Raksha Safety Escalation Desk"}
        }]
    }
    try:
        req = urllib.request.Request(
            webhook_url, data=json.dumps(discord_data).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        urllib.request.urlopen(req)
    except Exception as e:
        logger.error(f"Discord webhook failed: {e}")


# ==========================================
# 3. AGENT CLASSES & ROUTING ARCHITECTURE
# ==========================================

class RakshaAgent(Agent):
    def __init__(self, user_id: str = "caller_001", user_name: str = "दोस्त", room_id: str = "", chat_ctx: ChatContext = None) -> None:
        super().__init__(
            instructions=get_raksha_prompt(user_name),
            chat_ctx=chat_ctx
        )
        self.user_id = user_id
        self.user_name = user_name
        self.room_id = room_id

    async def on_enter(self) -> None:
        # Triggers Raksha to instantly read the context and speak when taking the mic
        await self.session.generate_reply()

    @function_tool()
    async def lookup_caller(self, context: RunContext) -> str:
        profile = db.get_user(self.user_id)
        if profile:
            self.user_name = profile.get("name", "दोस्त")
            self.update_instructions(get_raksha_prompt(self.user_name))
            return json.dumps(profile, ensure_ascii=False)
        return "New caller. No prior memory recorded."

    @function_tool()
    async def save_caller_memory(self, context: RunContext, name: str, language_preference: str, scheme_checked: str, risk_noted: str) -> str:
        facts = {"scheme_checked": scheme_checked, "risk_noted": risk_noted}
        db.save_user(user_id=self.user_id, name=name, language_preference=language_preference, facts=facts)
        self.user_name = name
        self.update_instructions(get_raksha_prompt(self.user_name))
        return f"Successfully saved memory for {name}."

    @function_tool()
    async def create_escalation(self, context: RunContext, issue_summary: str, urgency: str, checks_completed: str) -> str:
        db.log_call(self.room_id, "success")
        ticket_id = f"ESC-{random.randint(10000, 99999)}"
        send_discord_alert({
            "ticket_id": ticket_id, "caller_id": self.user_id,
            "issue_summary": sanitize_summary(issue_summary),
            "urgency": urgency, "checks_completed": checks_completed,
        })
        return f"Ticket {ticket_id} created successfully."

    @function_tool()
    async def transfer_to_scheme_specialist(self, context: RunContext) -> tuple[Agent, str]:
        """Routes the call to Samar. Injects a system firewall to prevent identity bleeding."""
        new_ctx = self.chat_ctx.copy(exclude_instructions=True)
        new_ctx.append(
            role="system",
            text=f"[SYSTEM FIREWALL]: The call has been transferred. YOU ARE NOW SAMAR. You are Male. Greet {self.user_name} and ask how you can help with their scheme inquiry."
        )
        
        samar = SamarAgent(
            user_id=self.user_id,
            user_name=self.user_name,
            room_id=self.room_id,
            chat_ctx=new_ctx
        )
        return samar, "जी बिल्कुल, योजनाओं की सही जानकारी के लिए मैं आपको हमारे विशेषज्ञ समर जी से बात कराती हूँ।"


class SamarAgent(Agent):
    def __init__(self, user_id: str, user_name: str = "दोस्त", room_id: str = "", chat_ctx: ChatContext = None) -> None:
        super().__init__(
            instructions=get_samar_prompt(user_name),
            chat_ctx=chat_ctx,
            tts=murf.TTS(
                voice="Samar",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True,
            ),
        )
        self.user_id = user_id
        self.user_name = user_name
        self.room_id = room_id

    async def on_enter(self) -> None:
        # Triggers Samar to instantly read the system firewall and speak
        await self.session.generate_reply()

    @function_tool()
    async def check_scheme_eligibility(self, context: RunContext, scheme_key: str, user_age: int = 25) -> str:
        db.log_call(self.room_id, "success")
        try:
            scheme_data = db.get_scheme_info(scheme_key)
            if not scheme_data:
                return "Scheme not found. Politely tell the user you don't have that information right now."

            is_eligible = scheme_data["min_age"] <= user_age <= scheme_data["max_age"]
            return f"User is {'eligible' if is_eligible else 'NOT eligible'}. Cost is ₹{scheme_data['cost']} per year. Requirements: savings bank account and auto-debit consent."
        except Exception as e:
            logger.error(f"Error fetching scheme data: {e}")
            return "Database connection failed. Ask them to check with their local bank branch."

    @function_tool()
    async def transfer_back_to_raksha(self, context: RunContext) -> tuple[Agent, str]:
        """Routes the call back to Raksha. Injects a system firewall to prevent identity bleeding."""
        new_ctx = self.chat_ctx.copy(exclude_instructions=True)
        new_ctx.append(
            role="system",
            text=f"[SYSTEM FIREWALL]: The call has been transferred back to you. YOU ARE NOW RAKSHA. You are Female. Warmly announce you are back, and immediately answer {self.user_name}'s security question."
        )
        
        raksha = RakshaAgent(
            user_id=self.user_id,
            user_name=self.user_name,
            room_id=self.room_id,
            chat_ctx=new_ctx
        )
        return raksha, "सुरक्षा से जुड़ी इस जानकारी के लिए, मैं आपको वापस रक्षा जी के पास भेज रहा हूँ।"


# ==========================================
# 4. SERVER SETUP & ORCHESTRATION
# ==========================================

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()

server.setup_fnc = prewarm

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-3.5-flash-lite"),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=RakshaAgent(user_id="caller_001", user_name="Suresh", room_id=ctx.room.name),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    await ctx.connect()
    db.log_call(ctx.room.name, "failed")

if __name__ == "__main__":
    cli.run_app(server)