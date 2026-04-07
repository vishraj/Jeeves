# 🏢 Jeeves: Enterprise RAG Assistant

Jeeves is a professional, session-aware AI assistant designed for the enterprise. Built with **Streamlit**, **Amazon Bedrock**, and **AWS DynamoDB**, it provides a secure and persistent conversational experience over your private business documents.

Inspired by the impeccable valet from P.G. Wodehouse's stories, Jeeves offers refined, context-aware assistance with an enterprise-grade UI.

---

## ✨ Key Features

- **🔐 Secure Authentication**: Integrated `streamlit-authenticator` with cookie-based persistence and `bcrypt` password hashing.
- **🖥️ Unified Wide Layout**: A consistent, full-width dashboard experience initialized at the entry point for immersive data analysis.
- **🎯 Responsive Centered Login**: A custom-ratio centering system (`3:2:3`) ensures the login card remains perfectly sized and centered on any display, from standard laptops to ultra-wide monitors.
- **📚 Intelligent RAG**: Leverages a custom 2-step retrieval and generation process via Amazon Bedrock for maximum citation accuracy.
- **💾 Persistent Chat History**: Full conversation persistence using AWS DynamoDB, allowing users to resume chats seamlessly.
- **📊 Automatic Data Visualization**: Detects numerical trends in document data and automatically renders interactive **Plotly** visualizations.
- **🎨 Premium UI/UX**: Custom CSS-enhanced "Glassmorphism" design with a blurred sidebar and sleek dark-mode aesthetics.

---

## 🎨 Design Philosophy

Jeeves is crafted to feel like a high-end enterprise tool rather than a generic chat bot.
1. **Consistency**: The "Wide" layout is set globally at the start of the application lifecycle to prevent visual shifting during navigation.
2. **Visual Hierarchy**: Critical actions (New Conversation, Profiles) are isolated in a blur-effect sidebar, keeping the main focus on the data and the conversation.
3. **Clarity**: Citations are rendered in collapsible containers to keep the UI clean while maintaining full transparency of source materials.

---

## 🏗️ Architecture

```mermaid
graph TD
    User((User)) -->|HTTPS| StreamlitUI[Streamlit UI]
    StreamlitUI -->|Auth| Authenticator[Streamlit Authenticator]
    
    subgraph "Logic Layer"
        StreamlitUI -->|Query| RAGEngine[KnowledgeBaseRAG]
        RAGEngine -->|Retrieve & Gen| Bedrock[Amazon Bedrock KB]
        StreamlitUI -->|Persist| ChatStore[DynamoDB ChatStore]
    end
    
    subgraph "Data Layer"
        Bedrock -->|Sources| S3Bucket[S3 Document Store]
        ChatStore -->|Save/Load| DDB[(JeevesChatHistory Table)]
    end
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.9+**
- **AWS Account** with Bedrock Knowledge Base and DynamoDB access.
- **AWS CLI** configured (via `aws configure` or SSO).

### 2. AWS Resources
Create the following resources in your AWS account:
- **DynamoDB Table**: `JeevesChatHistory`
  - Partition Key: `user_id` (String)
  - Sort Key: `conversation_id` (String)
- **Bedrock Knowledge Base**: Note your `KNOWLEDGE_BASE_ID` and `MODEL_ID`.

### 3. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd Jeeves

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory:
```env
KNOWLEDGE_BASE_ID=your_id_here
MODEL_ID=anthropic.claude-3-5-sonnet-v2:0
AWS_DEFAULT_REGION=us-east-1
```

Configure your users in `auth/config.yaml`.

### 5. Running the App
```bash
streamlit run app.py
```

---

## 🛠️ Tech Stack
- **Frontend**: [Streamlit](https://streamlit.io/)
- **Large Language Model**: [Anthropic Claude 3.5 Sonnet](https://www.anthropic.com/) via Amazon Bedrock.
- **Persistence**: [AWS DynamoDB](https://aws.amazon.com/dynamodb/)
- **Visualizations**: [Plotly Express](https://plotly.com/python/plotly-express/)
- **Authentication**: [Streamlit-Authenticator](https://github.com/mkhorasani/Streamlit-Authenticator)

---

## 🎩 Branding
The project uses custom branding located in `assets/logo.png`. To change the logo, simply replace this file with your own 200x200 pixel PNG.
