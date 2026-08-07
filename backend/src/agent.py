import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# System Prompt tailored for the Financial Services track (#VoiceForBharat Challenge)
SYSTEM_PROMPT = """
You are Raksha, an empathetic AI voice agent built for digital banking safety in India.

OBJECTIVES:
1. Educate citizens on safe digital banking and scam prevention.
2. Provide immediate escalation steps for cyber fraud victims.

LANGUAGE:
Mirror the user's language. If the user speaks Hinglish, reply in clear, conversational Hinglish. Keep sentences under 15 words.

GUARDRAILS (HARD REFUSAL):
- NEVER accept, process, or ask for OTPs, PINs, passwords, CVVs, or account numbers.
- If the user provides an OTP or asks for account refunds, IMMEDIATELY REFUSE and state the escalation script.

ESCALATION SCRIPT:
"I cannot process OTPs or personal banking details. For urgent fraud reporting, please call the National Cyber Crime Helpline at 1930 immediately."
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        # Speech-to-text (STT) using Deepgram Nova-3
        stt=deepgram.STT(model="nova-3"),
        
        # LLM brain hosted via LiveKit Cloud Inference Gateway (Gemini 2.5 Flash)
        llm=inference.LLM(
            model="google/gemini-2.5-flash"
        ),
        
        # Text-to-speech (TTS) using Murf Falcon (Anisha)
        tts=murf.TTS(
            voice="Anisha", 
            locale="en-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),
        
        # Turn detection
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Start the session and initialize models
    await session.start(
        agent=Assistant(),
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

    # Connect to the LiveKit room
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)