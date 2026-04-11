from utility.huggingface.config import models
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from langchain_huggingface import HuggingFacePipeline, HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings
from utility.logger import get_logger
from kokoro import KPipeline
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

logger = get_logger("MODELS_LOADER")

# ************** STT Model *******************
logger.info("Initializing STTModel...")
stt_model_cfg = models.get("stt", {})
STT_PROCCESSOR = AutoProcessor.from_pretrained(stt_model_cfg.get("name"))
STT_MODEL = AutoModelForSpeechSeq2Seq.from_pretrained(
    stt_model_cfg.get("name"),
    torch_dtype=stt_model_cfg.get("dtype"),
    low_cpu_mem_usage=True,
    use_safetensors=True,
).to(stt_model_cfg.get("device"))
logger.info("STT model loaded..")

# ************** TTS Model *******************
logger.info("Initializing TTS Pipeline...")
TTS_PIPELINE = KPipeline(lang_code="a")
logger.info("TTS Pipeline loaded..")

# *************** Main Model *******************
logger.info("Initializing Main Model...")
main_model_config = models.get("main", {})
MAIN_MODEL = ChatHuggingFace(llm=HuggingFaceEndpoint(
    repo_id=main_model_config.get("name"),
    task=main_model_config.get("task", "conversational"),
    max_new_tokens=main_model_config.get("max_new_tokens", 200),
    temperature=main_model_config.get("temperature", 0.2)
))
logger.info("Main model loaded..")

# *************** Planner Model *******************
logger.info("Initializing Planner Model...")
planner_model_config = models.get("planner", {})
PLANNER_MODEL = ChatHuggingFace(llm=HuggingFaceEndpoint(
    repo_id=planner_model_config.get("name"),
    task=planner_model_config.get("task", "conversational"),
    max_new_tokens=planner_model_config.get("max_new_tokens", 200),
    temperature=planner_model_config.get("temperature", 0.2)
))
logger.info("Planner model loaded..")

# *************** Voice Emotion Model *******************
logger.info("Initializing Voice Emotion Model...")
emotion_model_config = models.get("voice_emotion", {})
emotion_model_name = emotion_model_config.get("name")
emotion_model = AutoModelForSequenceClassification.from_pretrained(emotion_model_name)
emotion_tokenizer = AutoTokenizer.from_pretrained(emotion_model_name)
VOICE_EMOTION_PIPELINE = pipeline(
    emotion_model_config.get("task"), 
    model=emotion_model, 
    tokenizer=emotion_tokenizer
)
logger.info("Voice Emotion model loaded..")

# ****************** Embeddings Model *******************
logger.info("Initializing Embeddings Model...")
EMBEDDING_MODEL = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
logger.info("Embeddings model loaded..")
