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

# System Prompt tailored for Financial Services track (#VoiceForBharat Challenge)
SYSTEM_PROMPT = """You are Raksha, an empathetic AI voice agent built for digital banking safety and financial scheme guidance in India.

OBJECTIVES:
1. Educate citizens on safe digital banking and scam prevention.
2. Check eligibility and required document checklists for official government banking/insurance schemes.
3. Provide immediate escalation steps for cyber fraud victims.
4. Remember returning callers and their past banking safety checks.

LANGUAGE & SCRIPT (MANDATORY):
- Always write every language in its own native script.
- Hindi -> Devanagari (e.g., "नमस्ते"), NEVER use romanized Hindi (NEVER "namaste").
- Same rule for all non-English languages.
- Keep responses short, concise, and conversational (under 15 words per turn).

MEMORY & CONSENT RULES (HARD REQUIREMENT):
1. At the start of a call, use `lookup_caller` to see if you remember the user.
2. If returning user, greet them by name in Devanagari script (e.g., "नमस्ते रमेशजी! वापसी पर आपका स्वागत है।").
3. BEFORE saving any new facts, ASK for explicit user consent.
4. If user says NO/declines consent, DO NOT save anything.
5. If YES, call `save_caller_memory`.

TOOLS & REAL-TIME DATA (DAY 5 MANDATORY):
- When a user asks about scheme eligibility or document requirements, call `check_scheme_eligibility`.
- Always mention when the data is from (e.g., "अगस्त 2026 के दिशानिर्देशों के अनुसार...").
- If data retrieval fails, communicate the fallback out loud gracefully.

HUMAN ESCALATION RULES (DAY 7 MANDATE):
You must ask for human help if:
1. The caller reports active financial fraud or a compromised device (e.g., money actively missing, suspicious APK installed).
2. The caller needs a complex financial decision, dispute resolution, or refund that you cannot make.

MANDATORY CONSENT PROTOCOL BEFORE ESCALATION:
- When an escalation situation occurs, you MUST FIRST explain to the caller what information you will share (their issue summary, urgency) and explicitly ask for their permission.
- EXAMPLE: "क्या मैं आपकी शिकायत हमारी मानव सुरक्षा टीम को भेज सकती हूँ?" (Can I forward your complaint to our human security team?)
- DO NOT call `create_escalation` UNTIL the user explicitly says YES/Haan/Sure.
- IF THE USER SAYS NO: Politely respect their decision, do NOT call the tool, and advise them to call 1930 directly.

GUARDRAILS (HARD REFUSAL):
- NEVER ask for, accept, or store OTPs, PINs, passwords, bank account numbers, Aadhaar numbers, or government card IDs.
- If provided, REFUSE IMMEDIATELY: "मैं OTP या व्यक्तिगत बैंकिंग विवरण प्रोसेस नहीं कर सकती। धोखाधड़ी की रिपोर्ट के लिए तुरंत 1930 पर कॉल करें।"
- Do not include passwords, OTPs, PINs, account numbers, or Aadhaar numbers in your summary.
"""

# --- Privacy Sanitizer ---
def sanitize_summary(text: str) -> str:
    """Removes sensitive details before sending to the human dashboard."""
    # Redact 4-6 digit codes (OTPs/PINs)
    text = re.sub(r'\b\d{4,6}\b', '[OTP/PIN Redacted]', text)
    # Redact 10-16 digit numbers (Aadhaar, Account Numbers, Cards)
    text = re.sub(r'\b\d{10,16}\b', '[Aadhaar/Account Redacted]', text)
    return text

# --- Discord Notification Helper ---
def send_discord_alert(payload: dict):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL not set in .env.local. Skipping Discord alert.")
        return

    # Discord's webhook format expects application/json
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
            webhook_url,
            data=json.dumps(discord_data).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        urllib.request.urlopen(req)
        logger.info(f"Discord escalation alert posted for {payload['ticket_id']}")
    except Exception as e:
        logger.error(f"Discord webhook failed: {e}")


class Assistant(Agent):
    def __init__(self, user_id: str = "caller_001") -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.user_id = user_id

    @function_tool()
    async def lookup_caller(self, context: RunContext) -> str:
        """Look up the current caller's saved profile and remembered facts."""
        profile = db.get_user(self.user_id)
        if profile:
            return json.dumps(profile, ensure_ascii=False)
        return "New caller. No prior memory recorded."

    @function_tool()
    async def save_caller_memory(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        scheme_checked: str,
        risk_noted: str,
    ) -> str:
        """Save caller details after receiving explicit user consent. Do not call this
        if the user declines. Never pass account numbers, PINs, or government ID numbers.

        Args:
            name: The caller's name.
            language_preference: e.g. "Hindi", "English", "Hinglish".
            scheme_checked: Which scheme(s) were discussed this call.
            risk_noted: Short note on any fraud-risk topic covered.
        """
        facts = {
            "scheme_checked": scheme_checked,
            "risk_noted": risk_noted,
        }
        db.save_user(
            user_id=self.user_id,
            name=name,
            language_preference=language_preference,
            facts=facts,
        )
        return f"Successfully saved memory for {name}."

    @function_tool()
    async def check_scheme_eligibility(
        self,
        context: RunContext,
        scheme_key: str,
        user_age: int = 25,
    ) -> str:
        """Fetch real-time official scheme eligibility, document checklist, and updated rates.

        Args:
            scheme_key: The target scheme identifier, e.g., 'pmjjby' (life insurance), 'pmsby' (accident insurance), or 'cyber_claim'.
            user_age: The caller's age to verify eligibility rules.
        """
        try:
            scheme_data = db.get_scheme_info(scheme_key)
            if not scheme_data:
                return "क्षमा करें, इस योजना की ताज़ा जानकारी अभी उपलब्ध नहीं है। कृपया अपनी बैंक शाखा से संपर्क करें।"

            is_eligible = scheme_data["min_age"] <= user_age <= scheme_data["max_age"]
            as_of_date = datetime.now().strftime("%B %Y")

            result = {
                "scheme_name": scheme_data["name"],
                "as_of": as_of_date,
                "is_eligible": is_eligible,
                "annual_cost": scheme_data["cost"],
                "required_documents": scheme_data["documents"],
            }
            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error fetching scheme data: {e}")
            return "सर्वर से जुड़ने में समस्या आ रही है। जानकारी के लिए कृपया 1930 या निकटतम बैंक शाखा में संपर्क करें।"

    @function_tool()
    async def create_escalation(
        self,
        context: RunContext,
        issue_summary: str,
        urgency: str,
        checks_completed: str,
    ) -> str:
        """Call this tool ONLY AFTER the user explicitly grants permission to share their issue with a human coordinator.
        
        Args:
            issue_summary: Concise description of what happened (no private PINs/OTPs).
            urgency: Urgency level ('low', 'medium', 'high', 'emergency').
            checks_completed: Brief summary of what the AI agent already advised or checked.
        """
        ticket_id = f"ESC-{random.randint(10000, 99999)}"
        safe_summary = sanitize_summary(issue_summary)

        escalation_data = {
            "ticket_id": ticket_id,
            "caller_id": self.user_id,
            "issue_summary": safe_summary,
            "urgency": urgency,
            "checks_completed": checks_completed,
        }

        # Dispatch real-time Discord notification
        send_discord_alert(escalation_data)

        return f"Escalation ticket created successfully. Tell the user their reference ID is {ticket_id}. Explain that a human security coordinator will review their case within 24 hours. Do NOT promise an instant response."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
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
        agent=Assistant(user_id="caller_001"),
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


if __name__ == "__main__":
    cli.run_app(server)