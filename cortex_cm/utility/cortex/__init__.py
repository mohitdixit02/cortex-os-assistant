from cortex_cm.utility.cortex.models import models
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from langchain_huggingface import HuggingFacePipeline, HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings
from cortex_cm.utility.logger import get_logger
from cortex_cm.utility.config import env
from kokoro import KPipeline
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import os
from huggingface_hub import errors as hf_errors

logger = get_logger("MODELS_LOADER")

def _hf_call_with_local_cache(callable_fn, *args, local_files_only: bool = False, **kwargs):
    if local_files_only:
        kwargs["local_files_only"] = True
    try:
        return callable_fn(*args, **kwargs)
    except (hf_errors.LocalEntryNotFoundError, OSError) as e:
        if local_files_only:
            logger.error("Hugging Face local cache lookup failed with local_files_only=True. Error: %s", e)
            raise
        logger.error("Hugging Face load failed. Error: %s", e)
        raise

_STT_MODEL = None
_STT_PROCESSOR = None
def get_stt_model():
    global _STT_MODEL, _STT_PROCESSOR
    if _STT_MODEL is None:
        logger.info("Initializing STTModel...")
        stt_model_cfg = models.get("stt", {})
        _STT_PROCESSOR = _hf_call_with_local_cache(
            AutoProcessor.from_pretrained,
            stt_model_cfg.get("name"),
            local_files_only=env.TRANSFORMERS_CHECK_LOCAL_CACHE,
        )
        _STT_MODEL = _hf_call_with_local_cache(
            AutoModelForSpeechSeq2Seq.from_pretrained,
            stt_model_cfg.get("name"),
            torch_dtype=stt_model_cfg.get("dtype"),
            low_cpu_mem_usage=True,
            use_safetensors=True,
            local_files_only=env.TRANSFORMERS_CHECK_LOCAL_CACHE,
        ).to(stt_model_cfg.get("device"))
        logger.info("STT model loaded..")
    return _STT_MODEL, _STT_PROCESSOR

_TTS_PIPELINE = None
def get_tts_pipeline():
    global _TTS_PIPELINE
    if _TTS_PIPELINE is None:
        tts_model_cfg = models.get("tts", {})
        logger.info("Initializing TTS Pipeline...")
        _TTS_PIPELINE = KPipeline(lang_code="a", repo_id=tts_model_cfg.get("name"))
        logger.info("TTS Pipeline loaded..")
    return _TTS_PIPELINE

def _load_chat_hf_model(config_key, display_name):
    config = models.get(config_key, {})
    logger.info(f"Initializing {display_name}...")
    model = ChatHuggingFace(llm=HuggingFaceEndpoint(
        repo_id=config.get("name"),
        task=config.get("task", "conversational"),
        max_new_tokens=config.get("max_new_tokens", 200),
        temperature=config.get("temperature", 0.2),
        huggingfacehub_api_token=env.HF_TOKEN
    ))
    logger.info(f"{display_name} loaded..")
    return model

_MAIN_MODEL = None
def get_main_model():
    global _MAIN_MODEL
    if _MAIN_MODEL is None:
        _MAIN_MODEL = _load_chat_hf_model("main", "Main Model")
    return _MAIN_MODEL

_PLANNER_MODEL = None
def get_planner_model():
    global _PLANNER_MODEL
    if _PLANNER_MODEL is None:
        _PLANNER_MODEL = _load_chat_hf_model("planner", "Planner Model")
    return _PLANNER_MODEL

_MAIN_ORCHESTRATOR_MODEL = None
def get_main_orchestrator_model():
    global _MAIN_ORCHESTRATOR_MODEL
    if _MAIN_ORCHESTRATOR_MODEL is None:
        _MAIN_ORCHESTRATOR_MODEL = _load_chat_hf_model("main_orchestrator", "Main Orchestrator Model")
    return _MAIN_ORCHESTRATOR_MODEL

_HEAVY_PLANNER_MODEL = None
def get_heavy_planner_model():
    global _HEAVY_PLANNER_MODEL
    if _HEAVY_PLANNER_MODEL is None:
        _HEAVY_PLANNER_MODEL = _load_chat_hf_model("heavy_planner", "Heavy Planner Model")
    return _HEAVY_PLANNER_MODEL

_HEAVY_RESPONSE_MODEL = None
def get_heavy_response_model():
    global _HEAVY_RESPONSE_MODEL
    if _HEAVY_RESPONSE_MODEL is None:
        _HEAVY_RESPONSE_MODEL = _load_chat_hf_model("heavy_response_model", "Heavy Response Model")
    return _HEAVY_RESPONSE_MODEL

_VOICE_EMOTION_PIPELINE = None
def get_voice_emotion_pipeline():
    global _VOICE_EMOTION_PIPELINE
    if _VOICE_EMOTION_PIPELINE is None:
        logger.info("Initializing Voice Emotion Model...")
        emotion_model_config = models.get("voice_emotion", {})
        emotion_model_name = emotion_model_config.get("name")
        emotion_model = _hf_call_with_local_cache(
            AutoModelForSequenceClassification.from_pretrained,
            emotion_model_name,
            local_files_only=env.TRANSFORMERS_CHECK_LOCAL_CACHE,
        )
        emotion_tokenizer = _hf_call_with_local_cache(
            AutoTokenizer.from_pretrained,
            emotion_model_name,
            local_files_only=env.TRANSFORMERS_CHECK_LOCAL_CACHE,
        )
        _VOICE_EMOTION_PIPELINE = _hf_call_with_local_cache(
            pipeline,
            emotion_model_config.get("task"),
            model=emotion_model,
            tokenizer=emotion_tokenizer,
        )
        logger.info("Voice Emotion model loaded..")
    return _VOICE_EMOTION_PIPELINE

_EMBEDDING_MODEL = None
def get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        logger.info("Initializing Embeddings Model...")
        embd_model_config = models.get("embedding", {})
        _EMBEDDING_MODEL = _hf_call_with_local_cache(
            HuggingFaceEmbeddings,
            model_name=embd_model_config.get("name"),
            model_kwargs={"local_files_only": env.TRANSFORMERS_CHECK_LOCAL_CACHE},
        )
        logger.info("Embeddings model loaded..")
    return _EMBEDDING_MODEL

def warmup_all_models():
    """
    Eagerly load all models into memory. 
    This is intended to be called at application startup inside the event loop.
    """
    logger.info("Starting eager model loading (warmup)...")
    get_stt_model()
    get_tts_pipeline()
    get_main_model()
    get_planner_model()
    get_main_orchestrator_model()
    get_heavy_planner_model()
    get_heavy_response_model()
    get_voice_emotion_pipeline()
    get_embedding_model()
    logger.info("All models loaded successfully into memory.")
