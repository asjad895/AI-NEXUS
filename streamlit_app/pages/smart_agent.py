import streamlit as st
import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import os
from sqlalchemy import create_engine, Column, String, JSON, DateTime, Boolean, Integer, Float, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session, sessionmaker
import sqlalchemy as sa

Base = declarative_base()

class SmartAgent(Base):
    __tablename__ = "smart_agents"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    llm_provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    base_url = Column(String, nullable=True)
    api_key = Column(String, nullable=True)
    vector_db = Column(String, nullable=False, default="chromadb")
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=True)
    faq_job_ids = Column(String, nullable=True) 
    collection_name = Column(String, nullable=True) 
    lead_data_fields = Column(JSON, nullable=False)  
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, nullable=False, default=True)

def init_db():
    engine = create_engine("sqlite:///smart_agents.db")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def api_request(method, endpoint, data=None, params=None):
    base_url = st.session_state.get("api_base_url", "http://localhost:8000")
    url = f"{base_url}/{endpoint}"

    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, params=params, headers=headers)
        else:
            st.error(f"❌ Unsupported method: {method}")
            return None
        
        if response.status_code in (200, 201):
            return response.json()
        else:
            st.error(f"❌ API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"❌ Error connecting to API: {str(e)}")
        return None

def chat_with_smart_agent(agent_id, message, lead_data=None, missing_lead_data=None, user_id=None):
    data = {
        "user_id": user_id or st.session_state.user_id,
        "message": message,
        "agent_id": agent_id,
        "lead_data": lead_data,
        "missing_lead_data": missing_lead_data,
        "chat_history": st.session_state.chat_messages
    }
    
    return api_request("POST", f"smart_chat/chat", data=data)

def init_session_state():
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "current_lead_data" not in st.session_state:
        st.session_state.current_lead_data = {}
    
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent = None
        
    if "theme" not in st.session_state:
        st.session_state.theme = "light"

def get_all_smart_agents():
    db = init_db()
    agents = db.query(SmartAgent).filter(SmartAgent.is_active == True).all()
    return agents

def get_smart_agent(agent_id):
    db = init_db()
    return db.query(SmartAgent).filter(SmartAgent.id == agent_id).first()

def check_collection_status(collection_id):
    """Check the status of a FAQ collection ingestion job"""
    response = api_request("GET", f"/collection/{collection_id}")
    return response

def create_smart_agent(agent_data):
    db = init_db()
    agent_id = str(uuid.uuid4())
    
    try:
        new_agent = SmartAgent(
            id=agent_id,
            name=agent_data["name"],
            user_id=agent_data["user_id"],
            description=agent_data.get("description", ""),
            llm_provider=agent_data["llm_provider"],
            model=agent_data["model"],
            base_url=agent_data.get("base_url"),
            api_key=agent_data.get("api_key"),
            vector_db=agent_data.get("vector_db", "chromadb"),
            temperature=agent_data.get("temperature", 0.7),
            max_tokens=agent_data.get("max_tokens"),
            lead_data_fields=agent_data["lead_data_fields"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        
        db.add(new_agent)
        db.commit()
        
        faq_job_ids = agent_data.get("faq_job_ids", [])
        if faq_job_ids:
            ingest_data = {
                "agent_id": agent_id,
                "user_id": agent_data["user_id"],
                "faq_job_ids": faq_job_ids
            }
            print(f"Ingest data: {ingest_data}")
            ingest_response = api_request("POST", "/ingest", data=ingest_data)
            
            if ingest_response and "job_id" in ingest_response:
                st.session_state.collection_id = ingest_response["job_id"]
            else:
                st.warning("⚠️ FAQ ingestion was triggered but returned an unexpected response.")
        
        return agent_id
    except Exception as e:
        db.rollback()
        st.error(f"❌ Error creating smart agent: {str(e)}")
        return None
    finally:
        db.close()

def display_lead_data_card(lead_data):
    if not lead_data:
        return
        
    st.markdown("### 📋 Collected Information")
    cols = st.columns(2)
    
    icons = {
        "name": "👤", "email": "📧", "phone": "📱",
        "company": "🏢", "role": "👔", "requirements": "📝",
        "budget": "💰", "timeline": "⏱️",
        "location": "📍", "skills": "🛠️", "expected_ctc": "💸",
        "current_company": "🏭", "current_ctc": "💵"
    }
    
    i = 0
    for key, value in lead_data.items():
        col = cols[i % 2]
        with col:
            field_icon = icons.get(key, "ℹ️")
            st.markdown(f"""
            <div style="
                background-color: {'#f0f7ff' if st.session_state.theme == 'light' else '#1e2c3a'}; 
                padding: 10px; 
                border-radius: 8px; 
                margin-bottom: 10px;
                border-left: 4px solid {'#4361ee' if st.session_state.theme == 'light' else '#7289da'};
            ">
                <span style="font-size: 1.2em; font-weight: bold;">{field_icon} {key.title()}</span><br>
                <span style="color: {'#2c3e50' if st.session_state.theme == 'light' else '#e0e0e0'};">{value}</span>
            </div>
            """, unsafe_allow_html=True)
        i += 1
    st.markdown("---")

def display_missing_lead_data(missing_data):
    if not missing_data:
        return
        
    st.markdown("### 🔍 Information Needed")
    
    icons = {
        "name": "👤", "email": "📧", "phone": "📱",
        "company": "🏢", "role": "👔", "requirements": "📝",
        "budget": "💰", "timeline": "⏱️",
        "location": "📍", "skills": "🛠️", "expected_ctc": "💸",
        "current_company": "🏭", "current_ctc": "💵" 
    }
    
    missing_items = []
    for key, desc in missing_data.items():
        field_icon = icons.get(key, "ℹ️")
        missing_items.append(f"- {field_icon} **{key.title()}**: {desc}")
    
    if missing_items:
        st.markdown("\n".join(missing_items))
    st.markdown("---")

def main():
    st.set_page_config(
        page_title="Smart Conversation Agent",
        page_icon="🤖",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
    }
    .stSidebar {
        background-color: #F5F7F9;
    }
    .css-1d391kg, .css-1544g2n {
        padding-top: 2rem;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e6e6e6;
        border-radius: 6px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    
    with st.sidebar:
        st.title("🤖 Smart Agent Dashboard")
        
        theme_col1, theme_col2 = st.columns([3, 1])
        with theme_col1:
            st.write("Theme:")
        with theme_col2:
            if st.button("🌙" if st.session_state.theme == "light" else "☀️"):
                st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
                st.rerun()
        
        tab1, tab2 = st.tabs(["✨ Create Agent", "🔄 Select Agent"])
        
        with tab1:
            st.header("✨ Create New Smart Agent")
            
            agent_name = st.text_input("🏷️ Agent Name", placeholder="My Smart Agent")
            agent_description = st.text_area("📝 Description", placeholder="This agent helps with...")
            
            st.subheader("🧠 LLM Configuration")
            
            llm_options = {
                "openai": "OpenAI 🔄",
                "anthropic": "Anthropic 🧠",
                "google": "Google 🌐",
                "custom": "Custom 🛠️"
            }
            
            llm_provider = st.selectbox(
                "LLM Provider", 
                options=list(llm_options.keys()),
                format_func=lambda x: llm_options[x],
                help="Select the LLM provider"
            )
            
            model_placeholder = ""
            if llm_provider == "openai":
                model_placeholder = "gpt-4-turbo"
            elif llm_provider == "anthropic":
                model_placeholder = "claude-3-opus"
            elif llm_provider == "google":
                model_placeholder = "gemini-1.5-pro"
                
            model = st.text_input(
                "🤖 Model", 
                value="gpt-4-turbo" if llm_provider == "openai" else "",
                placeholder=model_placeholder
            )
            
            base_url = st.text_input(
                "🔗 Base URL (Optional)", 
                placeholder="https://api.openai.com/v1",
                help="Leave empty for default provider URL"
            )
            
            api_key = st.text_input(
                "🔑 API Key", 
                type="password",
                placeholder="Your API key"
            )
            
            st.subheader("🗃️ Vector Database")
            
            vector_db_options = {
                "chromadb": "ChromaDB 🟣",
                "milvus": "Milvus 🟠",
                "qdrant": "Qdrant 🔵",
                "faiss": "FAISS 🟢",
                "weaviate": "Weaviate 🟡"
            }
            
            vector_db = st.selectbox(
                "Vector Database",
                options=list(vector_db_options.keys()),
                format_func=lambda x: vector_db_options[x],
                help="Select the vector database for knowledge retrieval"
            )
            
            st.subheader("⚙️ Generation Parameters")
            
            temperature = st.slider(
                "🌡️ Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher values make output more random, lower values more deterministic"
            )
            
            max_tokens = st.number_input(
                "📏 Max Tokens (Optional)",
                min_value=0,
                value=0,
                help="Maximum tokens to generate (0 for model default)"
            )
            
            st.subheader("📚 Knowledge Base")
            
            faq_job_ids = st.text_input(
                "🔢 FAQ Job IDs (comma-separated)",
                placeholder="job1,job2,job3",
                help="IDs of FAQ jobs to use for knowledge retrieval"
            )
            
            user_id = st.text_input(
                "👤 User ID",
                value=st.session_state.user_id,
                help="User ID associated with this agent"
            )
            
            st.subheader("📊 Lead Data Fields")
            st.info("🔍 Define the lead data fields your agent should collect")
            
            default_fields = {
                "name": "Ask for the user's name",
                "email": "Ask for the user's email address",
                "phone": "Ask for the user's phone number",
                "company": "Ask for the user's company name",
                "role": "Ask for the user's role or position",
                "requirements": "Ask about the user's requirements or needs",
                "budget": "Ask about the user's budget",
                "timeline": "Ask about the user's timeline or deadline"
            }
            
            lead_data_df = pd.DataFrame({
                "Field": list(default_fields.keys()),
                "Description": list(default_fields.values()),
                "Include": [True] * len(default_fields)
            })
            
            edited_df = st.data_editor(
                lead_data_df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Field": st.column_config.TextColumn("Field Name"),
                    "Description": st.column_config.TextColumn("Prompt Description"),
                    "Include": st.column_config.CheckboxColumn("Include")
                }
            )
            
            if st.button("✨ Create Smart Agent", type="primary"):
                if not agent_name:
                    st.error("❌ Agent name is required")
                elif not model:
                    st.error("❌ Model name is required")
                elif not api_key:
                    st.error("❌ API key is required")
                else:
                    with st.spinner("🔄 Creating agent..."):
                        lead_data_fields = {}
                        for _, row in edited_df.iterrows():
                            if row["Include"]:
                                lead_data_fields[row["Field"]] = row["Description"]
                        agent_data = {
                            "name": agent_name,
                            "user_id": user_id,
                            "description": agent_description,
                            "llm_provider": llm_provider,
                            "model": model,
                            "base_url": base_url if base_url else None,
                            "api_key": api_key,
                            "vector_db": vector_db,
                            "temperature": temperature,
                            "max_tokens": max_tokens if max_tokens > 0 else None,
                            "faq_job_ids": faq_job_ids.split(",") if faq_job_ids else [],
                            "lead_data_fields": lead_data_fields
                        }
                        agent_id = create_smart_agent(agent_data)
                        if agent_id:
                            st.success(f"✅ Smart Agent created successfully!")
                            st.session_state.selected_agent = agent_id
                            time.sleep(2)
                            st.rerun()
        
        with tab2:
            st.header("🔄 Select Smart Agent")
            agents = get_all_smart_agents()
            
            if not agents:
                st.info("🔍 No smart agents found. Create one first!")
            else:
                agent_options = {f"{agent.name} ({agent.id})": agent.id for agent in agents}
                
                # Find the index of the currently selected agent
                selected_index = 0
                if st.session_state.selected_agent is not None:
                    values_list = list(agent_options.values())
                    if st.session_state.selected_agent in values_list:
                        selected_index = values_list.index(st.session_state.selected_agent)
                
                selected_agent_name = st.selectbox(
                    "🤖 Select Agent",
                    options=list(agent_options.keys()),
                    index=selected_index
                )
                
                if selected_agent_name:
                    selected_agent_id = agent_options[selected_agent_name]
                    st.session_state.selected_agent = selected_agent_id
                    agent = get_smart_agent(selected_agent_id)
                    if agent:
                        st.subheader("📋 Agent Details")
                        
                        # Create a card-style display for agent details
                        st.markdown(f"""
                        <div style="
                            background-color: {'#f8f9fa' if st.session_state.theme == 'light' else '#2d3748'}; 
                            padding: 15px; 
                            border-radius: 10px; 
                            border-left: 5px solid {'#4361ee' if st.session_state.theme == 'light' else '#7289da'};
                            margin-bottom: 20px;
                        ">
                            <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 10px;">📝 Details</div>
                            <div><b>Name:</b> {agent.name}</div>
                            <div><b>Description:</b> {agent.description or 'No description'}</div>
                            <div><b>LLM:</b> {agent.llm_provider} / {agent.model}</div>
                            <div><b>Vector DB:</b> {agent.vector_db}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.session_state.missing_lead_data = agent.lead_data_fields
        
        chat_control_col1, chat_control_col2 = st.columns(2)
        with chat_control_col1:
            if st.button("🔄 Refresh Chat", type="primary"):
                st.session_state.chat_messages = []
                st.session_state.current_lead_data = {}
                st.rerun()
        with chat_control_col2:
            if st.button("❌ Clear Data"):
                st.session_state.current_lead_data = {}
                st.rerun()
    
    if st.session_state.selected_agent:
        agent = get_smart_agent(st.session_state.selected_agent)
        if agent:
            st.markdown(f"""
            <h1 style="
                text-align: center; 
                padding: 10px; 
                background-color: {'#f0f7ff' if st.session_state.theme == 'light' else '#1e2c3a'}; 
                border-radius: 10px;
                margin-bottom: 20px;
            ">
                🤖 Chatting with: {agent.name}
            </h1>
            """, unsafe_allow_html=True)
            
            # Display current lead data if available
            if st.session_state.current_lead_data:
                col1, col2 = st.columns([3, 1])
                with col1:
                    display_lead_data_card(st.session_state.current_lead_data)
                with col2:
                    if st.session_state.missing_lead_data:
                        display_missing_lead_data(st.session_state.missing_lead_data)
            
            # Chat interface
            chat_container = st.container()
            
            with chat_container:
                for message in st.session_state.chat_messages:
                    role_icon = "👤" if message["role"] == "user" else "🤖"
                    role_color = "#e6f7ff" if message["role"] == "user" else "#f0f0f0"
                    if st.session_state.theme == "dark":
                        role_color = "#2d3748" if message["role"] == "user" else "#1e2c3a"
                    
                    with st.chat_message(message["role"], avatar=role_icon):
                        st.write(message["content"])
            
            user_input = st.chat_input("✍️ Type your message here...")
            
            if user_input:
                with st.chat_message("user", avatar="👤"):
                    st.write(user_input)
                
                st.session_state.chat_messages.append({"role": "user", "content": user_input})
                
                with st.spinner("🔄 Agent is thinking..."):
                    response = chat_with_smart_agent(
                        agent_id=st.session_state.selected_agent,
                        message=user_input,
                        lead_data=st.session_state.current_lead_data,
                        missing_lead_data=st.session_state.missing_lead_data,
                        user_id=st.session_state.user_id
                    )
                    
                    if response:
                        lead_data_updated = False
                        
                        if response.get("lead_data"):
                            for key, value in response["lead_data"].items():
                                if value:
                                    st.session_state.current_lead_data[key] = value
                                    lead_data_updated = True
                                    
                                    if key in st.session_state.missing_lead_data:
                                        del st.session_state.missing_lead_data[key]
                        
                        with st.chat_message("assistant", avatar="🤖"):
                            st.write(response["response"])
                            
                            if response.get("cited_chunks"):
                                with st.expander("📚 View Sources"):
                                    for i, chunk in enumerate(response["cited_chunks"]):
                                        st.markdown(f"""
                                        <div style="
                                            background-color: {'#f8f9fa' if st.session_state.theme == 'light' else '#2d3748'}; 
                                            padding: 10px; 
                                            border-radius: 5px; 
                                            margin-bottom: 10px;
                                            border-left: 3px solid {'#4361ee' if st.session_state.theme == 'light' else '#7289da'};
                                        ">
                                            <div style="font-weight: bold;">Source {i+1}:</div>
                                            <div>{chunk['text']}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                        st.session_state.chat_messages.append({"role": "assistant", "content": response["response"]})
                        
                        # If lead data was updated, rebuild the UI to show the changes
                        if lead_data_updated:
                            st.rerun()
                    else:
                        st.error("❌ Failed to get response from agent.")
    else:
        # Welcome screen when no agent is selected
        st.markdown("""
        <div style="text-align:center; padding:50px;">
            <h1>👋 Welcome to Smart Conversation Agent</h1>
            <p style="font-size:1.2em;">Please create or select a Smart Agent from the sidebar to start chatting.</p>
            <div style="margin-top:30px;">
                <img src="https://www.svgrepo.com/show/295345/robot.svg" width="200" height="200">
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()