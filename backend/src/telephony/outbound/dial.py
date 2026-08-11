import asyncio
import os
import re
import uuid
import argparse
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest

load_dotenv(".env.local")

async def dial(phone_number: str):
    livekit_api = api.LiveKitAPI(
        os.getenv("LIVEKIT_URL"),
        os.getenv("LIVEKIT_API_KEY"),
        os.getenv("LIVEKIT_API_SECRET"),
    )

    # Sanitize name and append unique short ID to prevent room conflict / dispatch queueing
    safe_target = re.sub(r'[^a-zA-Z0-9_-]', '_', phone_number)
    unique_suffix = uuid.uuid4().hex[:6]
    room_name = f"outbound-{safe_target}-{unique_suffix}"
    
    print(f"Dispatching outbound-agent to unique room '{room_name}' for target '{phone_number}'...")
    
    await livekit_api.agent_dispatch.create_dispatch(
        CreateAgentDispatchRequest(
            agent_name="outbound-agent",
            room=room_name,
            metadata=f'{{"phone_number": "{phone_number}"}}',
        )
    )
    
    print("Dispatch created! The agent worker will now initiate the SIP call.")
    await livekit_api.aclose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dial a phone number or Linphone username via LiveKit Agents")
    parser.add_argument("--to", required=True, help="Target phone number (+91...) or Linphone username (e.g. prakhidhachawdhury)")
    args = parser.parse_args()
    
    asyncio.run(dial(args.to))