from cortex_cm.pg import engine

_model = None
_memory_saver = None

def _get_model():
    global _model
    if _model is None:
        from cortex_core.memory.embedding import EmbeddingModel
        _model = EmbeddingModel()
    return _model

def _get_memory_saver():
    global _memory_saver, _model
    if _memory_saver is None:
        from cortex_core.memory.service.saver import MemorySaver
        if _model is None:
            _model = _get_model()
        _memory_saver = MemorySaver(engine=engine, model=_model)
    return _memory_saver

__all__ = [
    "_get_memory_saver",
    "_get_model"
]
