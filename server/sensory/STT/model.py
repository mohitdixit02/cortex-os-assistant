from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from logger import logger
from utility.huggingface.config import models
import io
import soundfile as sf
import numpy as np
import torch
from typing import List

# For Self Reference
# https://huggingface.co/docs/transformers/model_doc/whisper?usage=AutoModel

class STTModel:
    def __init__(self):
        logger.info("Initializing STTModel...")
        self.model_cfg = models.get("stt", {})
        self.np_dtype = np.dtype(self.model_cfg.get("model_np_dtype", "float32"))
        self.processor = AutoProcessor.from_pretrained(self.model_cfg.get("name"))
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_cfg.get("name"),
            torch_dtype=self.model_cfg.get("dtype"),
            low_cpu_mem_usage=True,
            use_safetensors=True,
        ).to(self.model_cfg.get("device"))
        logger.info("STT model loaded..")

    def decode_wav_bytes(self, audio_bytes: bytes) -> np.ndarray:
        """
            Convert Incoming PCM audio bytes to numpy array. \n
            Required for Hugging Face processor, which expects a noramalized 1D numpy array of audio samples.
        """
        audio, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=False)

        # Channel Averaging if multi-channel
        if isinstance(audio, np.ndarray) and audio.ndim > 1:
            audio = audio.mean(axis=1)

        # Warn if sample rate doesn't match expected config (model can still process but quality may degrade)
        if sr != self.model_cfg.get("sample_rate"):
            logger.warning(
                "Incoming sample rate %s does not match STT_CONFIG sample rate %s. "
                "Transcription quality may degrade unless you resample.",
                sr,
                self.model_cfg.get("sample_rate"),
            )

        if not isinstance(audio, np.ndarray):
            audio = np.asarray(audio, dtype=self.np_dtype)

        # contiguous array of float32 for processor
        return np.ascontiguousarray(audio, dtype=self.np_dtype)
    
    def transcribe_chunk(self, audio_chunk: np.ndarray) -> str:
        """
            Transcribe a single chunk of audio using the Hugging Face model and processor. \n
            Expects a normalized 1D numpy array of audio samples.
        """
        # Expects Normalized 1D array
        inputs = self.processor(
            audio=audio_chunk,
            sampling_rate=self.model_cfg.get("sample_rate"),
            return_tensors=self.model_cfg.get("processor_return_tensors")
        )

        input_features = inputs.input_features.to(self.model_cfg.get("device"), dtype=self.model_cfg.get("dtype"))

        with torch.inference_mode():
            generated_ids = self.model.generate(
                input_features=input_features,
                task=self.model_cfg.get("task"),
                return_timestamps=self.model_cfg.get("return_timestamps"),
            )

        text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=self.model_cfg.get("skip_special_tokens")
        )[0].strip()
        return text

    def transcribe_chunks_batched(self, audio_chunks: List[np.ndarray], batch_size: int = 1) -> List[str]:
        """Transcribe a list of audio chunks in mini-batches for better throughput."""
        if not audio_chunks:
            return []

        safe_batch_size = max(1, int(batch_size))
        outputs: List[str] = []

        for i in range(0, len(audio_chunks), safe_batch_size):
            batch = audio_chunks[i:i + safe_batch_size]
            if len(batch) == 1:
                outputs.append(self.transcribe_chunk(batch[0]))
                continue

            inputs = self.processor(
                audio=batch,
                sampling_rate=self.model_cfg.get("sample_rate"),
                return_tensors=self.model_cfg.get("processor_return_tensors"),
                padding=True,
            )
            input_features = inputs.input_features.to(
                self.model_cfg.get("device"),
                dtype=self.model_cfg.get("dtype")
            )

            with torch.inference_mode():
                generated_ids = self.model.generate(
                    input_features=input_features,
                    task=self.model_cfg.get("task"),
                    return_timestamps=self.model_cfg.get("return_timestamps"),
                )

            texts = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=self.model_cfg.get("skip_special_tokens")
            )
            outputs.extend([t.strip() for t in texts])

        return outputs


    

