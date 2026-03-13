from .rag_interface import RAGInterface

class ManualRAG(RAGInterface):
    """
    Stub implementation for a future manual RAG pipeline using 
    LangChain, FAISS, or other custom orchestration.
    """
    def ask(self, question: str) -> dict:
        return {
            "answer": "Manual RAG pipeline is not yet implemented. Please use KnowledgeBaseRAG.",
            "citations": []
        }
