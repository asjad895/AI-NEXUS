"""
Main module for the FAQ Pipeline REST API.
This file integrates all components and starts the FastAPI application.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.logger import logger
from app.middleware.database import SessionLocal
from metrics import PrometheusMiddleware
from app.middleware.exceptions import register_exception_handlers

# Import routers
from app.api_routes import faq, finetune, chat, compare, health, rag_chat, smart_conversation

# Create FastAPI app
app = FastAPI(
    title="GEN-AI Pipeline API",
    description="API for end to end faq, fine-tuning, rag, chat and analysis",
    version="1.0.0"
)

# Register middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(PrometheusMiddleware)

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(faq.router)
app.include_router(finetune.router)
app.include_router(chat.router)
app.include_router(compare.router)
app.include_router(health.router)
app.include_router(rag_chat.router)
app.include_router(smart_conversation.router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the FAQ Pipeline API! Check the documentation for available endpoints."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
