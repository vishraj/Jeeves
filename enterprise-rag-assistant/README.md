# Enterprise Document AI Assistant

A clean, modular Python application implementing an enterprise-style Retrieval Augmented Generation (RAG) system using AWS Services.

## 🏗️ Architecture

- **Frontend**: Streamlit
- **Orchestration**: Python with Boto3
- **RAG Engine**: Amazon Bedrock Knowledge Bases
- **LLM**: Anthropic Claude 3.5 Sonnet
- **Storage**: Amazon S3
- **Vector DB**: Amazon OpenSearch Serverless

### How it Works
1. **Ingestion**: Documents uploaded to S3 are processed by Bedrock Knowledge Base (chunking, embedding, and storage in OpenSearch).
2. **Retrieval**: User queries are sent to the `retrieve_and_generate` API.
3. **Generation**: Claude generates a response based *only* on the retrieved document context.
4. **Visualization**: If the user requests data visualization, the system prompts the LLM to extract structured data and renders interactive charts using Plotly.

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- AWS Account with Bedrock, S3, and OpenSearch permissions.
- Configured Bedrock Knowledge Base.

### Setup
1. Clone the repository and navigate to the project folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory (using `.env.example` as a template):
   ```env
   AWS_REGION=us-east-1
   KNOWLEDGE_BASE_ID=your-kb-id
   MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
   ```

### Execution
Run the application locally:
```bash
streamlit run app.py
```

## 📁 Project Structure
```text
enterprise-rag-assistant/
├── app.py              # Main application entry point
├── rag/
│   ├── rag_interface.py # Abstract RAG class
│   ├── knowledgebase_rag.py # AWS Knowledge Base implementation
│   └── manual_rag.py    # Stub for custom RAG
├── utils/
│   ├── aws_clients.py   # Boto3 client management
│   └── config.py        # Configuration manager
├── ui/
│   └── components.py    # Reusable Streamlit components
└── requirements.txt     # Python dependencies
```

## 🔧 AWS Configuration Guide

1. **S3 Bucket**: Create a bucket and upload your PDF/Word/Excel docs.
2. **Vector Store**: Create an Amazon OpenSearch Serverless collection (Vector search type).
3. **Knowledge Base**: 
   - Go to Bedrock Console -> Knowledge Bases.
   - Link S3 as the data source.
   - Link OpenSearch Serverless as the vector store.
   - Note down the **Knowledge Base ID**.
4. **Cloud Shell / Local Auth**: Ensure your local environment has active AWS credentials (via `aws configure` or environment variables).

## 📊 Visualization Capabilities
The assistant can generate:
- Bar Charts
- Line Charts
- Pie Charts
- Histograms

Simply ask: *"Show me a bar chart of the sales by region"* or *"Visualize the distribution of market share."*
