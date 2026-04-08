from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from cortex.memory.embedding import EmbeddingModel

# Minimum relevance of a doc with the query
ACCEPTABLE_RELEVANCE_SCORE = 0.6

# Relevance of every doc with the most relevant doc
RELEVANCE_SCORE_THRESHOLD = 0.5

# Chunking configuration for large documents
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Embedding throughput tuning
EMBED_BATCH_SIZE = 32
EMBED_MAX_WORKERS = 4

def retrieve_relevant_docs_utility(
    target_query: str,
    relevant_docs: list[Document],
    model: EmbeddingModel,
) -> list[Document]:
    """
    ### Utility function to retrieve relevant documents based on a target query. \n
    `relevant_docs` can contain docs from any source (web search results, vector database, etc.) and this function will filter those docs based on their relevance with the target query. \n
    Args:
        target_query (str): The query for which relevant documents are to be retrieved.
        relevant_docs (list[Document]): A list of Document objects containing document information.
        model (any): The model to be used for generating embeddings and calculating relevance scores.

    Returns:
        list[Document]: A list of Document objects containing the relevant documents.
    """
    
    if not target_query or not relevant_docs:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    query_embedding = model.generate_embeddings(target_query)
    
    relevance_score_filter_docs = []
    top_relevance_score = 0.0

    chunk_docs: list[Document] = []
    for doc in relevant_docs:
        chunks = splitter.split_documents([doc])

        for idx, chunk in enumerate(chunks):
            chunk_text = (chunk.page_content or "").strip()
            if not chunk_text:
                continue

            enriched_metadata = dict(chunk.metadata or {})
            enriched_metadata["chunk_index"] = idx
            enriched_metadata["chunk_size"] = len(chunk_text)
            chunk_docs.append(Document(page_content=chunk_text, metadata=enriched_metadata))

    if not chunk_docs:
        return []

    chunk_embeddings = model.generate_embeddings_batch(
        [doc.page_content for doc in chunk_docs],
        batch_size=EMBED_BATCH_SIZE,
        max_workers=EMBED_MAX_WORKERS,
    )

    for chunk_doc, doc_embedding in zip(chunk_docs, chunk_embeddings):
        relevance_score = model.get_cosine_similarity(query_embedding, doc_embedding)
        top_relevance_score = max(top_relevance_score, relevance_score)

        if relevance_score >= ACCEPTABLE_RELEVANCE_SCORE:
            print(f"Chunk {chunk_doc.metadata.get('chunk_index', '')} from '{chunk_doc.metadata.get('source', '')}' has relevance score {relevance_score} with the query.")
            relevance_score_filter_docs.append({
                "doc": chunk_doc,
                "relevance_score": relevance_score
            })
            
    final_relevant_docs = []
    for item in relevance_score_filter_docs:
        if item["relevance_score"] >= top_relevance_score * RELEVANCE_SCORE_THRESHOLD:
            print(f"Doc '{item['doc'].metadata.get('source', '')}' is selected as relevant with relevance score {item['relevance_score']}.")
            final_relevant_docs.append(item["doc"])
    return final_relevant_docs
