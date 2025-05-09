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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session,sessionmaker
import sqlalchemy as sa

# Database setup
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

# Initialize database connection
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
            st.error(f"Unsupported method: {method}")
            return None
        
        if response.status_code in (200, 201):
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# Chat with smart agent
def chat_with_smart_agent(agent_id, message, lead_data=None, next_lead_data=None, user_id=None):
    data = {
        "user_id": user_id or st.session_state.user_id,
        "message": message,
        "lead_data": lead_data,
        "next_lead_data": next_lead_data,
        "chat_history": st.session_state.chat_messages
    }
    
    return api_request("POST", f"smart-conversation/{agent_id}", data=data)

# Initialize session state
def init_session_state():
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "current_lead_data" not in st.session_state:
        st.session_state.current_lead_data = {}
    
    if "next_lead_data" not in st.session_state:
        st.session_state.next_lead_data = {}
    
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent = None

# Get all smart agents
def get_all_smart_agents():
    db = init_db()
    agents = db.query(SmartAgent).filter(SmartAgent.is_active == True).all()
    return agents

# Get smart agent by ID
def get_smart_agent(agent_id):
    db = init_db()
    return db.query(SmartAgent).filter(SmartAgent.id == agent_id).first()

def check_collection_status(collection_id):
    """Check the status of a FAQ collection ingestion job"""
    response = api_request("GET", f"smart-conversation/collection/{collection_id}")
    return response

def create_smart_agent(agent_data):
    db = init_db()
    agent_id = str(uuid.uuid4())
    
    try:
        # Create the agent in the database
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
        
        # If FAQ job IDs are provided, trigger the ingest-faqs API
        faq_job_ids = agent_data.get("faq_job_ids", [])
        if faq_job_ids:
            ingest_data = {
                "agent_id": agent_id,
                "user_id": agent_data["user_id"],
                "faq_job_ids": faq_job_ids
            }
            
            # Call the ingest-faqs API
            ingest_response = api_request("POST", "smart-conversation/ingest-faqs", data=ingest_data)
            
            if ingest_response and "job_id" in ingest_response:
                # Store the collection ID for tracking
                st.session_state.collection_id = ingest_response["job_id"]
            else:
                st.warning("FAQ ingestion was triggered but returned an unexpected response.")
        
        return agent_id
    except Exception as e:
        db.rollback()
        st.error(f"Error creating smart agent: {str(e)}")
        return None
    finally:
        db.close()

def main():
    st.set_page_config(
        page_title="Smart Conversation Agent",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize session state
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("Smart Agent Dashboard")
        
        # Tabs for Create/Select
        tab1, tab2 = st.tabs(["Create Agent", "Select Agent"])
        
        with tab1:
            st.header("Create New Smart Agent")
            
            # Agent details
            agent_name = st.text_input("Agent Name", placeholder="My Smart Agent")
            agent_description = st.text_area("Description", placeholder="This agent helps with...")
            
            # LLM Configuration
            st.subheader("LLM Configuration")
            llm_provider = st.selectbox(
                "LLM Provider", 
                options=["openai", "anthropic", "google", "custom"],
                help="Select the LLM provider"
            )
            
            model = st.text_input(
                "Model", 
                value="gpt-4-turbo" if llm_provider == "openai" else "",
                placeholder="Model name (e.g., gpt-4-turbo, claude-3-opus)"
            )
            
            base_url = st.text_input(
                "Base URL (Optional)", 
                placeholder="https://api.openai.com/v1",
                help="Leave empty for default provider URL"
            )
            
            api_key = st.text_input(
                "API Key", 
                type="password",
                placeholder="Your API key"
            )
            
            # Vector DB Configuration
            st.subheader("Vector Database")
            vector_db = st.selectbox(
                "Vector Database",
                options=["chromadb", "pinecone", "qdrant"],
                help="Select the vector database for knowledge retrieval"
            )
            
            # Generation Parameters
            st.subheader("Generation Parameters")
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher values make output more random, lower values more deterministic"
            )
            
            max_tokens = st.number_input(
                "Max Tokens (Optional)",
                min_value=0,
                value=0,
                help="Maximum tokens to generate (0 for model default)"
            )
            
            # FAQ Job IDs
            st.subheader("Knowledge Base")
            faq_job_ids = st.text_input(
                "FAQ Job IDs (comma-separated)",
                placeholder="job1,job2,job3",
                help="IDs of FAQ jobs to use for knowledge retrieval"
            )
            
            user_id = st.text_input(
                "User ID",
                value=st.session_state.user_id,
                help="User ID associated with this agent"
            )
            
            # Lead Data Fields
            st.subheader("Lead Data Fields")
            st.info("Define the lead data fields your agent should collect")
            
            # Default lead data fields
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
            
            # Create a dataframe for editing lead data fields
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
            
            # Create button
            if st.button("Create Smart Agent"):
                if not agent_name:
                    st.error("Agent name is required")
                elif not model:
                    st.error("Model name is required")
                elif not api_key:
                    st.error("API key is required")
                else:
                    # Process lead data fields
                    lead_data_fields = {}
                    for _, row in edited_df.iterrows():
                        if row["Include"]:
                            lead_data_fields[row["Field"]] = row["Description"]
                    
                    # Create agent data
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
                    
                    # Create agent
                    agent_id = create_smart_agent(agent_data)
                    if agent_id:
                        st.success(f"Smart Agent created successfully! ID: {agent_id}")
                        st.session_state.selected_agent = agent_id
                        time.sleep(2)
                        st.rerun()
        
        with tab2:
            st.header("Select Smart Agent")
            
            # Get all agents
            agents = get_all_smart_agents()
            
            if not agents:
                st.info("No smart agents found. Create one first!")
            else:
                # Create a selectbox with agent names
                agent_options = {f"{agent.name} ({agent.id})": agent.id for agent in agents}
                selected_agent_name = st.selectbox(
                    "Select Agent",
                    options=list(agent_options.keys()),
                    index=0 if st.session_state.selected_agent is None else list(agent_options.values()).index(st.session_state.selected_agent)
                )
                
                if selected_agent_name:
                    selected_agent_id = agent_options[selected_agent_name]
                    st.session_state.selected_agent = selected_agent_id
                    
                    # Get agent details
                    agent = get_smart_agent(selected_agent_id)
                    if agent:
                        st.subheader("Agent Details")
                        st.write(f"**Name:** {agent.name}")
                        st.write(f"**Description:** {agent.description}")
                        st.write(f"**LLM Provider:** {agent.llm_provider}")
                        st.write(f"**Model:** {agent.model}")
                        st.write(f"**Vector DB:** {agent.vector_db}")
                        
                        # Set next lead data from agent configuration
                        st.session_state.next_lead_data = agent.lead_data_fields
        
        # Refresh chat button
        if st.button("Refresh Chat"):
            st.session_state.chat_messages = []
            st.session_state.current_lead_data = {}
            st.rerun()
    
    # Main content area
    st.title("Smart Conversation Agent")
    
    if st.session_state.selected_agent:
        agent = get_smart_agent(st.session_state.selected_agent)
        if agent:
            st.subheader(f"Chatting with: {agent.name}")
            
            # Chat interface
            chat_container = st.container()
            
            # Display chat messages
            with chat_container:
                for message in st.session_state.chat_messages:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])
            
            # User input
            user_input = st.chat_input("Type your message here...")
            
            if user_input:
                # Add user message to UI
                with st.chat_message("user"):
                    st.write(user_input)
                
                # Add to session state
                st.session_state.chat_messages.append({"role": "user", "content": user_input})
                
                # Call API
                with st.spinner("Agent is thinking..."):
                    response = chat_with_smart_agent(
                        agent_id=st.session_state.selected_agent,
                        message=user_input,
                        lead_data=st.session_state.current_lead_data,
                        next_lead_data=st.session_state.next_lead_data,
                        user_id=st.session_state.user_id
                    )
                    
                    if response:
                        # Update lead data
                        if response.get("lead_data"):
                            for key, value in response["lead_data"].items():
                                if value:  # Only update if value is not None
                                    st.session_state.current_lead_data[key] = value
                        
                        # Update next lead data
                        if response.get("next_lead_data"):
                            st.session_state.next_lead_data = response["next_lead_data"]
                        
                        # Display assistant response
                        with st.chat_message("assistant"):
                            st.write(response["response"])
                            
                            # If there are cited chunks, show them in an expander
                            if response.get("cited_chunks"):
                                with st.expander("View Sources"):
                                    for i, chunk in enumerate(response["cited_chunks"]):
                                        st.markdown(f"**Source {i+1}:**")
                                        st.markdown(chunk["text"])
                                        st.markdown("---")
                        
                        # Add to session state
                        st.session_state.chat_messages.append({"role": "assistant", "content": response["response"]})
                    else:
                        st.error("Failed to get response from agent.")
    else:
        st.info("Please create or select a Smart Agent from the sidebar to start chatting.")

if __name__ == "__main__":
    main()




