import asyncio
import re
from typing import AsyncGenerator, Any
from nltk.tokenize import sent_tokenize
from cortex_cm.utility.main import iterate_tokens_async
import logging

def get_stream_ready_text(buffer: str) -> tuple[str, str]:
    """
    Determines when the accumulated text buffer has reached a point where it can be sent for TTS generation, based on sentence boundaries.
    """
    if not buffer:
        return "", ""
    stripped = buffer.strip()
    if not stripped:
        return "", ""
    if stripped.endswith((".", "!", "?")):
        return stripped, ""
    sentences = sent_tokenize(stripped)
    if len(sentences) <= 1:
        return "", buffer
    return " ".join(sentences[:-1]), sentences[-1]

async def stream_tts(
    text: str,
    tts_client: Any,
    stream_event: Any,
    logger: logging.Logger,
    cancel_event: asyncio.Event | None = None
) -> AsyncGenerator[bytes, None]:
    """
    Helper function to stream TTS audio chunks for a given text segment, with support for cancellation.
    """
    if cancel_event is None and stream_event:
        cancel_event = stream_event.response_cancel_event
    async for audio_chunk in tts_client.get_audio_stream(text):
        if stream_event and stream_event.isUserSpeaking():
            logger.info("Stopping TTS stream because user started speaking")
            return
        if cancel_event and cancel_event.is_set():
            logger.info("Cancelling TTS stream due to interruption")
            return
        yield audio_chunk

async def generate_audio_stream(
    input_data: str | Any,
    tts_client: Any,
    stream_event: Any,
    logger: logging.Logger,
    cancel_event: asyncio.Event | None = None
) -> AsyncGenerator[bytes, None]:
    """
    Unified utility function to stream audio chunks from text or text tokens.
    """
    if isinstance(input_data, str):
        tokens_callback = lambda: re.split(r'(\s+)', input_data)
    else:
        tokens_callback = input_data

    pending_text = ""
    async for token in iterate_tokens_async(
        generator_callback=tokens_callback,
        cancel_event=cancel_event,
    ):
        if stream_event and stream_event.isUserSpeaking():
            logger.info("Stopping token stream because user started speaking")
            return
        if cancel_event and cancel_event.is_set():
            logger.info("Cancelling token stream due to interruption")
            return

        pending_text += token
        segment, pending_text = get_stream_ready_text(pending_text)

        if segment:
            async for audio_chunk in stream_tts(segment, tts_client, stream_event, logger, cancel_event):
                yield audio_chunk

    remaining = pending_text.strip()
    if remaining and not (cancel_event and cancel_event.is_set()):
        async for audio_chunk in stream_tts(remaining, tts_client, stream_event, logger, cancel_event):
            yield audio_chunk