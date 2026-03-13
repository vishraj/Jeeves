from abc import ABC, abstractmethod

class RAGInterface(ABC):
    @abstractmethod
    def ask(self, question: str) -> dict:
        """
        Processes a natural language question and returns a dictionary 
        containing the answer, citations, and any structured data for visualization.
        
        Returns:
            dict: {
                "answer": str,
                "citations": list,
                "visualization_data": dict (optional),
                "suggested_chart": str (optional)
            }
        """
        pass
