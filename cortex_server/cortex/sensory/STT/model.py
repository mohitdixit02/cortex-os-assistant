from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from cortex_cm.utility.logger import get_logger
from cortex_cm.utility.huggingface.config import models
from cortex_cm.utility.sensory.config import STT_CONFIG
from cortex_cm.utility.models import get_stt_model
import io
import soundfile as sf
import numpy as np
import torch
import torch.nn.functional as F
from typing import List

# For Self Reference
# https://huggingface.co/docs/transformers/model_doc/whisper?usage=AutoModel
from cortex_cm.utility.models import get_stt_model

class STTModel:
    """
    ### Speech-to-Text (STT) Model \n
    Main interface for handling Speech-to-Text transcription using LLM Model. \n
    **Methods:** \n
    - `transcribe_chunks`: Transcribes a list of audio chunks using the model, with optional batching for improved efficiency. \n
    - `decode_wav_bytes`: Converts incoming PCM audio bytes to a numpy array of dimensions (n_samples,) required for the Hugging Face processor. \n
    """
    def __init__(self):
        self.logger = get_logger("SENSORY")
        self.model_cfg = models.get("stt", {})
        self.np_dtype = np.dtype(self.model_cfg.get("model_np_dtype", "float32"))
        self.model, self.processor = get_stt_model()
        self.sample_rate = STT_CONFIG.get("sample_rate")
        self.max_source_positions = int(self.model_cfg.get("max_source_positions"))

    def _normalize_input_features(self, input_features: torch.Tensor) -> torch.Tensor:
        """
        Pad mel frames to model's required fixed length. \n
        Throw Error if input exceeds max frames to avoid silent truncation and degraded transcription quality. \n
        """
        current_frames = int(input_features.shape[-1])
        target_frames = self.max_source_positions

        if current_frames < target_frames:
            input_features = F.pad(input_features, (0, target_frames - current_frames))
        elif current_frames > target_frames:
            self.logger.error(
                "Input mel features exceed model limit: got %s, max %s. "
                "Reduce chunk duration or split audio before transcription.",
                current_frames,
                target_frames,
            )
            raise ValueError(
                f"Input mel features too long for Whisper: {current_frames} > {target_frames}"
            )

        return input_features

    def decode_wav_bytes(self, audio_bytes: bytes) -> np.ndarray:
        """
            Convert Incoming PCM audio bytes to numpy array of dimensions (n_samples,) \n
            Required for Hugging Face processor, which expects a noramalized 1D numpy array of audio samples.
        """
        audio, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=False)

        # Channel Averaging if multi-channel
        if isinstance(audio, np.ndarray) and audio.ndim > 1:
            audio = audio.mean(axis=1)

        # Warn if sample rate doesn't match expected config (model can still process but quality may degrade)
        if sr != self.sample_rate:
            self.logger.warning(
                "Incoming sample rate %s does not match STT_CONFIG sample rate %s. "
                "Transcription quality may degrade unless you resample.",
                sr,
                self.sample_rate,
            )

        if not isinstance(audio, np.ndarray):
            audio = np.asarray(audio, dtype=self.np_dtype)

        # contiguous array of float32 for processor
        return np.ascontiguousarray(audio, dtype=self.np_dtype)
    
    def transcribe_chunks(
            self, 
            audio_chunks: List[np.ndarray], 
            batch_size: int = 1
        ) -> tuple[List[str], str | None]:
        """
        ### Transcribe Audio Chunks using Model (in Batches if specified) \n
        Transcribe a list of audio chunks using Model. \n
        For multiple batches,
        - If `batch_size` > 1, transcribe in batches for improved efficiency. \n
        - If `batch_size` = 1, transcribe sequentially, which can help prevent overflow for model window but may be slower. \n
        
        **Input**: \n
        - `audio_chunks`: List of audio chunks as numpy arrays to be transcribed. \n
        - `batch_size`: Number of chunks to transcribe in a single batch. Default is 1 (no batching). \n

        **Output**: \n
        - `Tuple` containing:
            1. `List of transcribed texts` corresponding to each audio chunk (in order).
            2. `Detected language` as a string (e.g., "en") or None if not detected.
        """
        if not audio_chunks:
            return [], None

        safe_batch_size = max(1, int(batch_size))
        outputs: List[str] = []
        detected_language = None

        for i in range(0, len(audio_chunks), safe_batch_size):
            batch = audio_chunks[i:i + safe_batch_size]
            
            # Expects Normalized 1D array
            inputs = self.processor(
                audio=batch,
                sampling_rate=self.sample_rate,
                return_tensors=self.model_cfg.get("processor_return_tensors"),
                padding=(len(batch) > 1)
            )
            input_features = inputs.input_features.to(
                self.model_cfg.get("device"),
                dtype=self.model_cfg.get("dtype")
            )
            input_features = self._normalize_input_features(input_features)

            with torch.inference_mode():
                # For Whisper, we can get the language by looking at the first predicted token
                # when forced_decoder_ids is not set to a specific language.
                generation_outputs = self.model.generate(
                    input_features=input_features,
                    task=self.model_cfg.get("task"),
                    return_timestamps=self.model_cfg.get("return_timestamps"),
                    return_dict_in_generate=True,
                    output_scores=True,
                )
                generated_ids = generation_outputs.sequences

            # Detect language from the first batch if not already detected
            if detected_language is None and generated_ids.shape[0] > 0:
                # In HuggingFace, generated_ids usually starts with the decoder_start_token_id
                # The language token is the first token actually "generated" by the model
                # if it's not forced.
                
                # Let's look at the generated sequence and decode everything including special tokens
                full_tokens = self.processor.tokenizer.convert_ids_to_tokens(generated_ids[0])
                self.logger.info("Raw Whisper tokens: %s", full_tokens)
                
                for token in full_tokens:
                    # Whisper language tokens are in the format '<|en|>', '<|fr|>', etc.
                    if token.startswith("<|") and token.endswith("|>") and len(token) == 6:
                        detected_language = token.strip("<|>")
                        break
                
                if detected_language:
                    self.logger.info("Detected language from Whisper tokens: %s", detected_language)
                else:
                    self.logger.warning("Could not find language token in Whisper tokens.")

            texts = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=self.model_cfg.get("skip_special_tokens")
            )
            outputs.extend([t.strip() for t in texts])

        return outputs, detected_language
