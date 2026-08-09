import json
import logging
import sys
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

# System Prompt tailored for Financial Services track (#VoiceForBharat Challenge - Day 4)
SYSTEM_PROMPT = """You are Raksha, an empathetic AI voice agent built for digital banking safety in India.

OBJECTIVES:
1. Educate citizens on safe digital banking and scam prevention.
2. Provide immediate escalation steps for cyber fraud victims.
3. Remember returning callers and their past banking safety checks.

LANGUAGE & SCRIPT (MANDATORY):
- Always write every language in its own native script.
- Hindi -> Devanagari (e.g., "नमस्ते"), NEVER use romanized Hindi (NEVER "namaste").
- Keep responses short, concise, and conversational (under 15 words per turn).

MEMORY & CONSENT RULES (HARD REQUIREMENT):
1. At the start of a call, use `lookup_caller` to see if you remember the user.
2. If returning user, greet them by name in Devanagari script (e.g., "नमस्ते रमेशजी! वापसी पर आपका स्वागत है।").
3. BEFORE saving any new facts, ASK for explicit user consent (e.g., "क्या मैं आपकी सुरक्षा प्राथमिकताओं को याद रख सकती हूँ?").
4. If user says NO/declines consent, DO NOT save anything.
5. If YES, call `save_caller_memory`.

GUARDRAILS (HARD REFUSAL):
- NEVER ask for, accept, or store OTPs, PINs, passwords, bank account numbers, or government card IDs.
- If provided, REFUSE IMMEDIATELY: "मैं OTP या व्यक्तिगत बैंकिंग विवरण प्रोसेस नहीं कर सकती। धोखाधड़ी की रिपोर्ट के लिए तुरंत 1930 पर कॉल करें।"
"""


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
            voice="Anisha",  # explicit locale so Hindi is spoken natively, not with an English accent
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Tools now live directly on the Assistant agent instance — no fnc_ctx needed.
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