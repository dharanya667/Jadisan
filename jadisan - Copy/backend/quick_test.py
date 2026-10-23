import asyncio
from transcriber import transcribe_audio, load_model

async def main():
    load_model()  # explicit init, per the error message
    text = await transcribe_audio("test_complaint.wav")
    print("TRANSCRIBED TEXT:", text)

asyncio.run(main())