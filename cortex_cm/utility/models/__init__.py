from cortex_cm.utility.huggingface.config import models
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from langchain_huggingface import HuggingFacePipeline, HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings
from cortex_cm.utility.logger import get_logger
from kokoro import KPipeline
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

logger = get_logger("MODELS_LOADER")

_STT_MODEL = None
_STT_PROCESSOR = None
def get_stt_model():
    global _STT_MODEL, _STT_PROCESSOR
    if _STT_MODEL is None:
        logger.info("Initializing STTModel...")
        stt_model_cfg = models.get("stt", {})
        _STT_PROCESSOR = AutoProcessor.from_pretrained(stt_model_cfg.get("name"))
        _STT_MODEL = AutoModelForSpeechSeq2Seq.from_pretrained(
            stt_model_cfg.get("name"),
            torch_dtype=stt_model_cfg.get("dtype"),
            low_cpu_mem_usage=True,
            use_safetensors=True,
        ).to(stt_model_cfg.get("device"))
        logger.info("STT model loaded..")
    return _STT_MODEL, _STT_PROCESSOR

_TTS_PIPELINE = None
def get_tts_pipeline():
    global _TTS_PIPELINE
    if _TTS_PIPELINE is None:
        logger.info("Initializing TTS Pipeline...")
        _TTS_PIPELINE = KPipeline(lang_code="a")
        logger.info("TTS Pipeline loaded..")
    return _TTS_PIPELINE

def _load_chat_hf_model(config_key, display_name):
    config = models.get(config_key, {})
    logger.info(f"Initializing {display_name}...")
    model = ChatHuggingFace(llm=HuggingFaceEndpoint(
        repo_id=config.get("name"),
        task=config.get("task", "conversational"),
        max_new_tokens=config.get("max_new_tokens", 200),
        temperature=config.get("temperature", 0.2)
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
        emotion_model = AutoModelForSequenceClassification.from_pretrained(emotion_model_name)
        emotion_tokenizer = AutoTokenizer.from_pretrained(emotion_model_name)
        _VOICE_EMOTION_PIPELINE = pipeline(
            emotion_model_config.get("task"), 
            model=emotion_model, 
            tokenizer=emotion_tokenizer
        )
        logger.info("Voice Emotion model loaded..")
    return _VOICE_EMOTION_PIPELINE

_EMBEDDING_MODEL = None
def get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        logger.info("Initializing Embeddings Model...")
        _EMBEDDING_MODEL = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        logger.info("Embeddings model loaded..")
    return _EMBEDDING_MODEL
