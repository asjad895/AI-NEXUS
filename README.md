# AI NEXUS
A Scalabale, distrubuted, backend, services with streamlit as frontend. Finetuning, RAG, Strategy pattern, Evaluation,  etc


### Video Examples
https://www.loom.com/share/1570b5357ed74abc993caa785b61d752?sid=6699a918-dcd2-4159-8549-a247ec397eff

https://www.loom.com/share/77dce91803f34bb9bb58f7eb703ab698?sid=813b8ca3-107d-4dfc-be92-1d89f612e2e3

### Key Components and Decision Points
Frontend (Streamlit)
Home.py: Entry point with navigation to different features
FAQ Page: Document upload and FAQ extraction
Finetune Page: Model fine-tuning, chat with models, and comparison
Smart Agent Page: Conversational agents with lead data extraction
Backend (FastAPI)
API Routes: Organized by feature (faq, finetune, chat, compare, rag_chat, smart_conversation)
Decision Points:
Document Processing: Extracts FAQs from uploaded documents using LLMs
Fine-tuning: Selects base models and configures parameters based on user input
Chat Routing: Routes messages to appropriate models and manages history
Comparison Logic: Parallel processing to compare fine-tuned model vs RAG responses
Smart Agent: Processes user messages, extracts lead data, and retrieves relevant information
Services
FAQ Service: Processes documents and extracts question-answer pairs
Finetune Service: Manages fine-tuning jobs and model interactions
RAG Agent: Implements retrieval-augmented generation for knowledge-based responses
Smart Conversation Agent: Advanced agent with lead data extraction capabilities
Storage
SQL Database: Stores user data, job information, and chat history
Vector Databases: Multiple options (ChromaDB, Milvus, Qdrant, FAISS, Weaviate) for storing embeddings
File Storage: Manages uploaded documents and processed outputs
Tech Stack
Frontend: Streamlit, Python
Backend: FastAPI, Python, Pydantic
LLM Integration: Support for multiple providers (OpenAI, Mistral, Llama, Gemma, Phi)
Vector Databases: ChromaDB, Milvus, Qdrant, FAISS, Weaviate
Pattern Implementation: Strategy pattern for different agent implementations

https://www.mermaidchart.com/raw/1043809e-2734-438a-b227-20cf32851f08?theme=light&version=v0.1&format=svg