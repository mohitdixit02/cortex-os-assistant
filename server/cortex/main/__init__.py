from sensory.STT import STTClient
from cortex.main.model import CortexMainModel
from logger import logger
# keep listening and processing until the program is terminated


def main():
    logger.info("Starting Cortex Main Server...")
    stt_client = STTClient()
    model = CortexMainModel()
    
    while True:
        logger.info("Listening for audio input...")
        text = stt_client.listen()
        if text:
            res = model.generate(
                query=text,
            )
            print("Response:", res)
            

            