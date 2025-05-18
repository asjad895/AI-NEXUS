from app.Voice.multi_agents import entrypoint, prewarm
from livekit.agents import cli, WorkerOptions
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    required_vars = ['LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET', 'CEREBRAS_API_KEY', 'DEEPGRAM_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file or set these variables before running.")
        exit(1)
        
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint, 
        prewarm_fnc=prewarm,
        api_key=os.getenv('LIVEKIT_API_KEY'),
        api_secret=os.getenv('LIVEKIT_API_SECRET'),
    ))
