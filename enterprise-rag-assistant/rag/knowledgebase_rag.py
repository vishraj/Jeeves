import json
from .rag_interface import RAGInterface
from utils.aws_clients import aws_manager
from utils.config import Config

class KnowledgeBaseRAG(RAGInterface):
    def __init__(self):
        self.kb_id = Config.KNOWLEDGE_BASE_ID
        self.model_arn = f"arn:aws:bedrock:{Config.AWS_REGION}::foundation-model/{Config.MODEL_ID}"
        # If the model ID is already an ARN, a versioned model ID (contains ':'),
        # or a cross-region inference profile (starts with a region prefix), use it directly
        _inference_profile_prefixes = ("global.", "us.", "eu.", "ap.")
        if ":" in Config.MODEL_ID or Config.MODEL_ID.startswith(_inference_profile_prefixes):
            self.model_arn = Config.MODEL_ID

    def ask(self, question: str) -> dict:
        if not self.kb_id:
            return {
                "answer": "Error: KNOWLEDGE_BASE_ID is not configured.",
                "citations": []
            }

        try:
            response = aws_manager.bedrock_agent_runtime.retrieve_and_generate(
                input={'text': question},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': self.model_arn
                    }
                }
            )

            answer = response.get('output', {}).get('text', "")
            citations = self._parse_citations(response.get('citations', []))

            # Logic to detect visualization request could be added here or in the UI layer
            # For a cleaner separation, we'll keep it simple here and handle extraction 
            # as a secondary step if needed.
            
            return {
                "answer": answer,
                "citations": citations
            }
        except Exception as e:
            return {
                "answer": f"An error occurred: {str(e)}",
                "citations": []
            }

    def _parse_citations(self, citations_raw: list) -> list:
        parsed_citations = []
        for citation in citations_raw:
            text_context = citation.get('generatedResponsePart', {}).get('textResponsePart', {}).get('span', {}).get('text', "")
            for ref in citation.get('retrievedReferences', []):
                location = ref.get('location', {})
                source_uri = ""
                if location.get('type') == 'S3':
                    source_uri = location.get('s3Location', {}).get('uri', "Unknown S3 Source")
                
                # Extract filename from URI
                source_name = source_uri.split('/')[-1] if source_uri else "Unknown Source"
                
                parsed_citations.append({
                    "source": source_name,
                    "uri": source_uri,
                    "text": ref.get('content', {}).get('text', "")
                })
        return parsed_citations
