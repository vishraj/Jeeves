import json
import uuid
from .rag_interface import RAGInterface
from utils.aws_clients import aws_manager
from utils.config import Config

class KnowledgeBaseRAG(RAGInterface):
    def __init__(self):
        self.kb_id = Config.KNOWLEDGE_BASE_ID
        self.model_id = Config.MODEL_ID
        # Model info for direct invocation
        self.model_arn = f"arn:aws:bedrock:{Config.AWS_REGION}::foundation-model/{Config.MODEL_ID}"
        _inference_profile_prefixes = ("global.", "us.", "eu.", "ap.")
        if ":" in Config.MODEL_ID or Config.MODEL_ID.startswith(_inference_profile_prefixes):
            self.model_arn = Config.MODEL_ID
            
        # Session ID for continuity (though we'll rely on manual history injection too)
        self.session_id = None

    def reset_session(self):
        """Clear the current session."""
        self.session_id = None

    def ask(self, question: str, history=None) -> dict:
        """
        Custom 2-step RAG: 
        1. Retrieve relevant snippets manually.
        2. Generate answer using Claude directly with history + snippets.
        This bypasses Bedrock's internal refusal logic.
        """
        if not self.kb_id:
            return {"answer": "Error: KNOWLEDGE_BASE_ID is not configured.", "citations": []}

        # Step 1: Manual Retrieval from Knowledge Base
        snippets = []
        try:
            retrieve_response = aws_manager.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={'text': question}
            )
            snippets = self._parse_retrieval_results(retrieve_response.get('retrievalResults', []))
        except Exception as e:
            print(f"DEBUG: Retrieval failed: {e}. Proceeding with history only.")

        # Step 2: Build Custom Prompt and Invoke Model
        # Format snippets for the prompt
        snippet_text = "\n\n".join([f"SOURCE {i+1}:\n{s['content']}" for i, s in enumerate(snippets)])
        if not snippet_text:
            snippet_text = "No relevant source snippets found for this turn."

        # Format history
        history_text = ""
        if history:
            history_text = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history[-6:]])

        system_prompt = (
            "You are Jeeves, a professional enterprise AI assistant. "
            "Answer the user's question based on the provided SOURCE SNIPPETS and the CONVERSATION HISTORY.\n\n"
            "--- INSTRUCTIONS ---\n"
            "1. If the information is in the SOURCE SNIPPETS, use it.\n"
            "2. If the user asks for a chart, plot, or visualization of data ALREADY mentioned in the history, "
            "you MUST fulfill it using that history context, even if the snippets are empty.\n"
            "3. If the data is not in either the history or snippets, say you don't know.\n\n"
            "--- VISUALIZATION FORMATTING ---\n"
            "If asked for a chart, graph, or visualization, provide it as a JSON block at the end:\n"
            "```json\n"
            "{\n"
            "  \"chart_type\": \"bar|line|pie|histogram\",\n"
            "  \"x_axis\": \"label_x\",\n"
            "  \"y_axis\": \"label_y\",\n"
            "  \"data\": [{\"label_x\": \"A\", \"label_y\": 10}]\n"
            "}\n"
            "```"
        )

        user_input = (
            f"## CONVERSATION HISTORY\n{history_text or 'No previous history.'}\n\n"
            f"## SOURCE SNIPPETS\n{snippet_text}\n\n"
            f"## USER REQUEST\n{question}"
        )

        try:
            # Claude 3 Messages API payload
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0
            })

            response = aws_manager.bedrock_runtime.invoke_model(
                modelId=self.model_arn,
                body=body
            )

            response_body = json.loads(response.get('body').read())
            answer = response_body.get('content', [{}])[0].get('text', "")

            # If this is the first turn and we don't have a session ID, create one for consistency
            if not self.session_id:
                self.session_id = str(uuid.uuid4())

            return {
                "answer": answer,
                "citations": snippets,
                "session_id": self.session_id
            }

        except Exception as e:
            return {
                "answer": f"An error occurred during generation: {str(e)}",
                "citations": snippets
            }

    def _parse_retrieval_results(self, results_raw: list) -> list:
        parsed = []
        for res in results_raw:
            location = res.get('location', {})
            source_uri = location.get('s3Location', {}).get('uri', "Unknown S3 Source") if location.get('type') == 'S3' else ""
            source_name = source_uri.split('/')[-1] if source_uri else "Unknown Source"
            
            parsed.append({
                "source": source_name,
                "uri": source_uri,
                "content": res.get('content', {}).get('text', ""),
                "text": res.get('content', {}).get('text', "") # for compat with parser
            })
        return parsed
