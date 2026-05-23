"""
Conifguration Parameters for Cortex Operations
"""

""" 
Orchestration iteration limit
"""
ORCHESTRATION_MAX_ITERATIONS_LIMIT = 3

"""
Parameters for `retrieve_relevant_docs_utility`
"""
# Max word limit
MAX_WORD_LIMIT = 750

# Chunking configuration for large documents
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# Embedding throughput tuning
EMBED_BATCH_SIZE = 32
EMBED_MAX_WORKERS = 4

"""
Configuration for Memory Retriever
"""
MINIMUM_CONVERSATION_HISTORY_COUNT = 2 # Must be less than what is going to summarize
CONVERSATION_HISTORY_SUMMARIZATION_THRESHOLD = 5 # Can't be zero as summarization is must (>= 1)

MESSAGES_REJECTION_THRESHOLD = 0.1 # Messages only similar more than 10% will be kept.
MESSAGES_MAX_LIMIT = 15 # Max messages to send to Cortex
