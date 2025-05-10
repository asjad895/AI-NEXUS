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

graph TD
    %% Client Side (Streamlit)
    subgraph "Frontend (Streamlit)"
        A[Home.py] --> B[FAQ Page]
        A --> C[Finetune Page]
        A --> D[Smart Agent Page]
        
        B -->|"upload_file()"| B1[API Request]
        C -->|"create_finetune_job()"| C1[API Request]
        C -->|"chat_with_model()"| C2[API Request]
        C -->|"compare_answers()"| C3[API Request]
        D -->|"create_smart_agent()"| D0[API Request]
        D -->|"chat_with_smart_agent()"| D1[API Request]
        
        %% Smart Agent Creation Logic
        D0 -->|"On Success"| D0a["Auto-call /ingest endpoint"]
    end
    
    %% API Layer
    subgraph "FastAPI Backend"
        E[main.py] --> F[faq.router]
        E --> G[finetune.router]
        E --> H[chat.router]
        E --> I[compare.router]
        E --> J[rag_chat.router]
        E --> K[smart_conversation.router]
        
        %% Decision Points
        F -->|"POST /faq/upload"| F1{{"Process Document"}}
        G -->|"POST /finetune"| G1{{"Create Fine-tuning Job"}}
        H -->|"POST /chat"| H1{{"Chat with Model"}}
        I -->|"POST /compare"| I1{{"Compare Model vs RAG"}}
        K -->|"POST /smart_chat/chat"| K1{{"Smart Agent Processing"}}
        K -->|"POST /ingest"| K2{{"FAQ Ingestion"}}
        J -->|"POST /rag-chat"| J1{{"RAG Processing"}}
    end
    
    %% Services Layer
    subgraph "Services & Agents"
        L[FAQ Service]
        M[Finetune Service]
        N[Chat Service]
        O[RAG Agent]
        P[Smart Conversation Agent]
        
        F1 --> L
        G1 --> M
        H1 --> N
        I1 -->|"Model Answer"| N
        I1 -->|"RAG Answer"| O
        J1 --> O
        K1 --> P
        K2 --> P
    end
    
    %% Data Layer
    subgraph "Data & Storage"
        Q[(SQL Database)]
        R[(Vector Database)]
        S[File Storage]
        
        L --> S
        L --> Q
        M --> Q
        N --> Q
        O --> R
        P --> R
        P --> Q
    end
    
    %% MLOps Layer
    subgraph "MLOps (OPIK)"
        T[Tracking]
        U[Logging]
        V[Metrics]
        
        T -->|"@track decorator"| T1[Function Tracking]
        U -->|"logger.info/error"| U1[Log Management]
        V -->|"Prometheus"| V1[Performance Metrics]
    end
    
    %% Connect Services to MLOps
    L --> T
    M --> T
    N --> T
    O --> T
    P --> T
    
    %% Tech Stack Labels
    classDef techstack fill:#f9f,stroke:#333,stroke-width:2px
    classDef algorithm fill:#cfe,stroke:#333,stroke-width:1px
    
    class A,B,C,D techstack
    note_frontend[Frontend: Streamlit, Python]:::techstack
    
    class E,F,G,H,I,J,K techstack
    note_backend[Backend: FastAPI, Python, Pydantic]:::techstack
    
    class L,M,N,O,P techstack
    note_services[Services: LLM Integration, RAG, Smart Agents]:::techstack
    
    class Q,R,S techstack
    note_data[Storage: SQL, Vector DBs-ChromaDB, Milvus, etc., File System]:::techstack
    
    class T,U,V techstack
    note_mlops[MLOps: OPIK Tracking, Prometheus Metrics]:::techstack
    
    %% Pseudo-Algorithm Details
    F1 -.- note_F1["ALGORITHM: FAQ Upload
    1. Validate input with Pydantic
    2. Save file to storage
    3. Create job record in DB (PENDING)
    4. Start background task
    5. Track with OPIK
    6. Return job ID
    7. Handle errors with try/catch
    8. Rollback on failure"]
    
    G1 -.- note_G1["ALGORITHM: Create Fine-tune Job
    1. Validate request model
    2. Create job with UUID
    3. Set status PENDING
    4. Start async background job
    5. Implement retry logic
    6. Update job status
    7. Track with OPIK
    8. Return job details"]
    
    H1 -.- note_H1["ALGORITHM: Chat with Model
    1. Validate chat request
    2. Route to model type (finetune/rag)
    3. Create appropriate agent
    4. Generate response
    5. Save to chat history
    6. Fallback to default on error
    7. Track with OPIK
    8. Return formatted response"]
    
    I1 -.- note_I1["ALGORITHM: Compare Answers
    1. Validate comparison request
    2. Create parallel async tasks
    3. Get model response
    4. Get RAG response
    5. Wait with timeout
    6. Combine results
    7. Track performance metrics
    8. Return both responses"]
    
    J1 -.- note_J1["ALGORITHM: RAG Processing
    1. Validate RAG request
    2. Create LLM agent
    3. Connect to vector DB
    4. Query for relevant chunks
    5. Generate response with context
    6. Save to chat history
    7. Track with OPIK
    8. Return response with citations"]
    
    K1 -.- note_K1["ALGORITHM: Smart Agent Chat
    1. Validate request
    2. Get agent config from DB
    3. Create smart agent
    4. Extract lead data from message
    5. Retrieve relevant FAQs
    6. Generate contextual response
    7. Update lead database
    8. Track with OPIK
    9. Return response with lead data"]
    
    K2 -.- note_K2["ALGORITHM: FAQ Ingestion
    1. Validate ingest request
    2. Create collection with UUID
    3. Initialize vector DB
    4. Start background task
    5. Process FAQs in chunks
    6. Generate embeddings
    7. Store in vector DB
    8. Update collection status
    9. Track with OPIK"]
    
    %% Agent Factory Pattern
    subgraph "Agent Factory Pattern"
        AF[Agent Factory]
        AF1[OpenAI Agent]
        AF2[Anthropic Agent]
        AF3[Custom Agent]
        
        AF -->|"create_agent()"| AF1
        AF -->|"create_agent()"| AF2
        AF -->|"create_agent()"| AF3
    end
    
    P --> AF
    O --> AF
    
    AF -.- note_AF["ALGORITHM: Create Agent
    1. Select provider based on input
    2. Configure API keys from env
    3. Set model parameters
    4. Apply Strategy pattern
    5. Return concrete agent
    6. Track creation with OPIK
    7. Handle provider-specific logic
    8. Implement fallback mechanism"]
    
    %% Smart Agent Creation
    D0 -.- note_D0["ALGORITHM: Create Smart Agent
    1. Generate agent UUID
    2. Save agent config to DB
    3. If FAQs provided:
       a. Prepare ingest data
       b. Call /ingest endpoint
       c. Save collection ID
    4. Handle errors with try/catch
    5. Return agent ID or error"]