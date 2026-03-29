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
        # Session ID for maintaining conversation context across multiple questions
        self.session_id = None

    def reset_session(self):
        """Clear the current session so the next question starts a fresh conversation."""
        self.session_id = None

    def ask(self, question: str, history=None) -> dict:
        """
        Submits a question to the Knowledge Base. 
        If 'history' is provided, we prepend the contextual summary to ensure continuity 
        across sessions (important when session_id expires).
        """
        if not self.kb_id:
            return {
                "answer": "Error: KNOWLEDGE_BASE_ID is not configured.",
                "citations": []
            }

        # 1. Build context-aware prompt if history is present
        # Note: Bedrock's retrieve_and_generate handles multi-turn naturally IF session_id is active.
        # However, if we're resuming an old session, session_id may be dead.
        # We handle this by injecting context manually when history is available.
        final_question = question
        if history and len(history) > 0:
            # Simple context injector: provide last 4 turns (2 user-assistant pairs)
            recent_context = "\n".join([f"{m['role'].capitalize()}: {m['content'][:200]}..." 
                                         for m in history[-4:]])
            final_question = (
                "## CONVERSATION HISTORY\n"
                f"{recent_context}\n\n"
                "## INSTRUCTION\n"
                "Answer the user's question based on the above context and your knowledge base. "
                "Adhere to any formatting requirements (like JSON blocks) mentioned in the prompt below.\n\n"
                "## USER QUESTION\n"
                f"{question}"
            )

        # Define a custom prompt template to ensure visualization requirements are respected
        # The '$search_results$' and '$input_text$' placeholders are required by Bedrock.
        prompt_template = (
            "You are Jeeves, a professional enterprise AI assistant. "
            "Answer the user's question based strictly on the following source snippets. "
            "If the information is not in the snippets, clearly state that you don't know.\n\n"
            "## SOURCE SNIPPETS\n"
            "$search_results$\n\n"
            "## USER REQUEST\n"
            "$input_text$\n\n"
            "--- MANDATORY FORMATTING ---\n"
            "If the user asks for a chart, graph, visualization, or trend (line, bar, pie, histogram), "
            "you MUST provide the structured data at the end of your response in a hidden JSON block.\n"
            "Format precisely like this:\n"
            "```json\n"
            "{\n"
            "  \"chart_type\": \"bar|line|pie|histogram\",\n"
            "  \"x_axis\": \"label_x\",\n"
            "  \"y_axis\": \"label_y\",\n"
            "  \"data\": [{\"label_x\": \"Value A\", \"label_y\": 10}]\n"
            "}\n"
            "```\n"
            "Assistant:"
        )

        try:
            request_params = {
                'input': {'text': final_question},
                'retrieveAndGenerateConfiguration': {
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': self.model_arn,
                        'generationConfiguration': {
                            'promptTemplate': {
                                'textPromptTemplate': prompt_template
                            }
                        }
                    }
                }
            }
            # Pass session ID if we have one to maintain conversation context
            if self.session_id:
                request_params['sessionId'] = self.session_id

            response = aws_manager.bedrock_agent_runtime.retrieve_and_generate(**request_params)

            # Capture the session ID for the next turn
            self.session_id = response.get('sessionId')

            answer = response.get('output', {}).get('text', "")
            citations = self._parse_citations(response.get('citations', []))
            
            return {
                "answer": answer,
                "citations": citations,
                "session_id": self.session_id
            }
        except Exception as e:
            # If session is expired, try one more time without the session_id
            if "expired" in str(e).lower() and self.session_id:
                self.session_id = None
                return self.ask(question, history=history)
            
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
