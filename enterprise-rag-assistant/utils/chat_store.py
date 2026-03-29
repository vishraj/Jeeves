from decimal import Decimal
from datetime import datetime
from botocore.exceptions import ClientError
from .aws_clients import aws_manager

def convert_floats_to_decimals(obj):
    """Recursively convert float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, list):
        return [convert_floats_to_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj

class ChatStore:
    def __init__(self, table_name="JeevesChatHistory"):
        self.table_name = table_name
        self.table = aws_manager.dynamodb.Table(self.table_name)

    def list_conversations(self, user_id):
        """List all conversations for a user, sorted by updated_at Desc."""
        try:
            response = self.table.query(
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": user_id}
            )
            items = response.get('Items', [])
            # Sort locally since DynamoDB sorts by sort key (conversation_id) only by default
            return sorted(items, key=lambda x: x.get('updated_at', ""), reverse=True)
        except ClientError as e:
            print(f"Error listing conversations: {e}")
            return []

    def load_conversation(self, user_id, conversation_id):
        """Retrieve a specific conversation."""
        try:
            # Note: conversation_id is string. user_id is string.
            response = self.table.get_item(
                Key={
                    'user_id': user_id,
                    'conversation_id': conversation_id
                }
            )
            return response.get('Item')
        except ClientError as e:
            print(f"Error loading conversation: {e}")
            return None

    def save_conversation(self, user_id, conversation_id, title, messages, bedrock_session_id=None):
        """Create or update a conversation record."""
        now = datetime.utcnow().isoformat()
        
        # Convert floats to Decimals for DynamoDB
        safe_messages = convert_floats_to_decimals(messages)
        
        item = {
            'user_id': user_id,
            'conversation_id': conversation_id,
            'title': title[:100],  # Truncate title
            'messages': safe_messages,
            'updated_at': now,
            'bedrock_session_id': bedrock_session_id
        }

        # If it's a brand new conversation, add created_at
        existing = self.load_conversation(user_id, conversation_id)
        if not existing:
            item['created_at'] = now
        else:
            item['created_at'] = existing.get('created_at', now)

        try:
            self.table.put_item(Item=item)
            return True
        except ClientError as e:
            print(f"Error saving conversation: {e}")
            return False

    def delete_conversation(self, user_id, conversation_id):
        """Permanently delete a conversation."""
        try:
            self.table.delete_item(
                Key={
                    'user_id': user_id,
                    'conversation_id': conversation_id
                }
            )
            return True
        except ClientError as e:
            print(f"Error deleting conversation: {e}")
            return False

# Global instance
chat_store = ChatStore()
