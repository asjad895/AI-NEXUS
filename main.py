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
from app.api_routes import faq, finetune, chat, compare, health

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

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the FAQ Pipeline API! Check the documentation for available endpoints."}

# Startup event
# @app.on_event("startup")
# async def startup_event():
#     logger.info("Starting FAQ Pipeline API")
#     # Initialize database if needed
#     from middleware.database import init_db
#     init_db()
#     logger.info("Database initialized")

# Shutdown event
# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("Shutting down FAQ Pipeline API")
#     # Close any open connections
#     SessionLocal().close()
#     logger.info("Database connections closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
