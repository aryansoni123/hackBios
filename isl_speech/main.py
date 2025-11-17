# main.py
import asyncio
import whisperflow.streaming as st
import whisperflow.transcriber as ts

async def transcribe_file(audio_path: str):
    model = ts.get_model()         # if library uses get_model()
    result = await ts.transcribe_pcm_chunks_async(model, [audio_path])
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(transcribe_file("help.wav"))