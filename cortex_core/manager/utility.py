from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from cortex_core.memory.embedding import EmbeddingModel

# Max word limit
MAX_WORD_LIMIT = 750

# Chunking configuration for large documents
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# Embedding throughput tuning
EMBED_BATCH_SIZE = 32
EMBED_MAX_WORKERS = 4

def retrieve_relevant_docs_utility(
    target_query: str,
    relevant_docs: list[Document],
    model: EmbeddingModel,
    is_diversified: bool = False,
    is_mmr_enabled: bool = True
) -> list[Document]:
    """
    ### Utility function to retrieve relevant documents based on a target query. \n
    `relevant_docs` can contain docs from any source (web search results, vector database, etc.) and this function will filter those docs based on their relevance with the target query. \n
    Args:
        target_query (str): The query for which relevant documents are to be retrieved.
        relevant_docs (list[Document]): A list of Document objects containing document information.
        model (any): The model to be used for generating embeddings and calculating relevance scores.
        is_diversified (bool): A flag indicating whether the retrieved documents should be diversified.
        is_mmr_enabled (bool): A flag indicating whether MMR (Maximal Marginal Relevance) should be enabled for document selection.
    Returns:
        list[Document]: A list of Document objects containing the relevant documents.
    """
    
    if not target_query or not relevant_docs:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    
    # Minimum relevance of a doc with the query
    ACCEPTABLE_RELEVANCE_SCORE = 0.45 if is_diversified else 0.6
    # Relevance of every doc with the most relevant doc
    RELEVANCE_SCORE_THRESHOLD = 0.3 if is_diversified else 0.5
    # Diversity vs relevance tradeoff in MMR (if diversified, give more importance to diversity)
    MMR_LAMBDA = 0.5 if is_diversified else 0.75

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
                "embedding": doc_embedding,
                "relevance_score": relevance_score
            })
            
    
    
    sorted_docs = sorted(relevance_score_filter_docs, key=lambda x: x["relevance_score"], reverse=True)
    final_relevant_docs = []
    current_word_count = 0
    selected_embs = []
    
    if is_mmr_enabled:
        print(f"MMR enabled. Selecting documents based on relevance and diversity with MMR_LAMBDA={MMR_LAMBDA} and RELEVANCE_SCORE_THRESHOLD={RELEVANCE_SCORE_THRESHOLD}.")
        while sorted_docs and current_word_count < MAX_WORD_LIMIT:
            mmr_selected_idx = -1
            best_mmr_score = float("-inf")
            
            for i, item in enumerate(sorted_docs):
                if not selected_embs:
                    mmr_score = item["relevance_score"]
                else:
                    redundancy = max([model.get_cosine_similarity(item["embedding"], sel_emb) 
                                    for sel_emb in selected_embs])
                    mmr_score = (MMR_LAMBDA * item["relevance_score"]) - ((1 - MMR_LAMBDA) * redundancy)
                
                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    mmr_selected_idx = i
            
            next_relv_doc = sorted_docs.pop(mmr_selected_idx)
            
            if next_relv_doc["relevance_score"] < (top_relevance_score * RELEVANCE_SCORE_THRESHOLD):
                print(f"Stopping MMR selection as the best candidate's relevance score {next_relv_doc['relevance_score']} is below the threshold.")
                break
                
            final_relevant_docs.append(next_relv_doc["doc"])
            selected_embs.append(next_relv_doc["embedding"])
            current_word_count += len(next_relv_doc["doc"].page_content.split())
            
            print(f"Selected chunk {next_relv_doc['doc'].metadata.get('chunk_index', '')} from '{next_relv_doc['doc'].metadata.get('source', '')}' with relevance score {next_relv_doc['relevance_score']} and MMR score {best_mmr_score}.")
    else:
        print(f"MMR not enabled. Selecting documents based solely on relevance with RELEVANCE_SCORE_THRESHOLD={RELEVANCE_SCORE_THRESHOLD}.")
        for item in sorted_docs:
            if current_word_count >= MAX_WORD_LIMIT:
                print(f"Reached max word limit of {MAX_WORD_LIMIT}. Stopping selection.")
                break
            
            if item["relevance_score"] < (top_relevance_score * RELEVANCE_SCORE_THRESHOLD):
                print(f"Stopping selection as the candidate's relevance score {item['relevance_score']} is below the threshold.")
                break
            
            final_relevant_docs.append(item["doc"])
            current_word_count += len(item["doc"].page_content.split())
            print(f"Selected chunk {item['doc'].metadata.get('chunk_index', '')} from '{item['doc'].metadata.get('source', '')}' with relevance score {item['relevance_score']}.")

    return final_relevant_docs
