import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env.local from backend directory
backend_dir = Path(__file__).resolve().parents[3]
sys.path.append(str(backend_dir / "src"))
load_dotenv(backend_dir / ".env.local")

from livekit import rtc, api
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
    get_job_context,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db  # SQLite memory database manager

logger = logging.getLogger("outbound-agent")

OUTBOUND_PROMPT = """You are Raksha, an empathetic AI voice agent built for digital banking safety in India. You are making a proactive OUTBOUND call to a citizen over the phone.

MANDATORY FIRST TWO SENTENCES ON CALL CONNECT:
You MUST start the conversation with EXACTLY this opening:
"नमस्ते! मैं डिजिटल बैंकिंग सुरक्षा सहायक रक्षा बोल रही हूँ। यह कॉल आपको PMJJBY बीमा योजना के नवीनीकरण की याद दिलाने के लिए है। यदि आप यह कॉल समाप्त करना चाहते हैं, तो कृपया 'बंद करो' कहें।"

OBJECTIVES:
1. Remind the user to renew their PMJJBY scheme before the deadline.
2. If they engage, answer their questions briefly.
3. If they say "stop", "बंद करो", or "don't call me", immediately call `opt_out_and_end_call` to log the preference and confirm politely.

LANGUAGE & SCRIPT:
- Always speak and write in Devanagari Hindi (e.g., "नमस्ते"). 
- Keep responses short, concise, and conversational (under 12 words per turn).

GUARDRAILS:
- NEVER ask for, accept, or process OTPs, passwords, bank account numbers, or government card IDs.
- If provided, refuse immediately and instruct them to call 1930.
"""

async def hangup_call():
    ctx = get_job_context()
    if ctx and ctx.room.name:
        logger.info("Ending call and deleting room...")
        await ctx.api.room.delete_room(api.DeleteRoomRequest(room=ctx.room.name))

class OutboundAssistant(Agent):
    def __init__(self, target_phone: str) -> None:
        super().__init__(instructions=OUTBOUND_PROMPT)
        self.target_phone = target_phone

    async def _delayed_hangup(self):
        # Allow 4.5 seconds for Murf TTS confirmation speech to play out before deleting the room
        await asyncio.sleep(4.5)
        await hangup_call()

    @function_tool()
    async def opt_out_and_end_call(self, context: RunContext) -> str:
        """Call this tool IMMEDIATELY if the user asks to stop receiving calls, says 'band karo', or wants to hang up."""
        db.save_user(
            user_id=self.target_phone,
            name="Linphone User",
            language_preference="Hindi",
            facts={"opted_out_of_outbound": True}
        )
        
        asyncio.create_task(self._delayed_hangup())
        return "Preference saved. Speak this exact short confirmation to the user now: 'ठीक है, आपकी कॉल प्राथमिकता दर्ज कर ली गई है। अब आपको कॉल नहीं किया जाएगा। सुरक्षित रहें!'"


server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()

server.setup_fnc = prewarm

@server.rtc_session(agent_name="outbound-agent")
async def my_agent(ctx: JobContext):
    dial_info = json.loads(ctx.job.metadata)
    phone_number = dial_info.get("phone_number")
    
    if not phone_number:
        logger.error("No target address or phone number provided in metadata.")
        ctx.shutdown()
        return

    trunk_id = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID")
    if not trunk_id:
        logger.error("LIVEKIT_SIP_OUTBOUND_TRUNK_ID is missing or empty in .env.local!")
        ctx.shutdown()
        return

    # Event listener to prevent my_agent from exiting until the caller disconnects
    done_event = asyncio.Event()

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        if participant.identity == phone_number:
            logger.info("Callee disconnected from room.")
            done_event.set()

    # 1. Initiate the SIP call
    try:
        logger.info(f"Initiating SIP call to target '{phone_number}'...")
        await ctx.api.sip.create_sip_participant(api.CreateSIPParticipantRequest(
            room_name=ctx.room.name,
            sip_trunk_id=trunk_id,
            sip_call_to=phone_number,
            participant_identity=phone_number,
            wait_until_answered=True,
        ))
        logger.info(f"Call picked up by {phone_number}")
    except Exception as e:
        logger.error(f"SIP Call failed: {e}")
        ctx.shutdown()
        return

    # 2. Connect worker session to LiveKit room
    await ctx.connect()

    # 3. Wait for callee participant to join
    await ctx.wait_for_participant(identity=phone_number)

    # 4. Initialize Agent Session
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

    # 5. Start session
    await session.start(
        agent=OutboundAssistant(target_phone=phone_number),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony(),
            ),
        ),
    )

    # 6. Trigger initial greeting immediately
    logger.info("Call connected. Triggering initial greeting...")
    await session.generate_reply(
        instructions="Speak the mandatory opening greeting right now."
    )

    # 7. Keep entrypoint alive so the agent listens continuously
    logger.info("Greeting delivered. Keeping session open for user response...")
    await done_event.wait()

if __name__ == "__main__":
    cli.run_app(server)