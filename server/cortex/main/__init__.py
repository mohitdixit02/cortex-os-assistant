import asyncio
from sensory.STT import STTClient
from sensory.TTS import TTSClient
from cortex.main.model import CortexMainModel
from logger import logger
# keep listening and processing until the program is terminated


async def listen_and_respond(audio_bytes: bytes):
    logger.info("Starting Cortex Main Server...")
    stt_client = STTClient()
    tts_client = TTSClient()
    model = CortexMainModel()
     
    text = await stt_client.transcribe(audio_bytes)
    if not text:
        return

    print("Transcribed Text:", text)
    model_response = await model.generate(query=text)
    print("Model Response:", model_response)
    
    async for audio_chunk in tts_client.get_audio_stream(model_response):
        yield audio_chunk
        
    
    
    # while True:
    #     logger.info("Listening for audio input...")
    #     text = stt_client.listen()
    #     if text:
    #         res = model.generate(
    #             query=text,
    #         )
    #         print("Response:", res)
            

            