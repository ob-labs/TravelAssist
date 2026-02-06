"""
FastAPI REST API for OBMMS Travel Assistant.

Provides HTTP endpoints for the travel planning chat interface
with streaming response support.
"""

import asyncio
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agents import TravelWorkflow
from src.common.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Travel Assistant API",
    description="API for intelligent travel planning powered by OceanBase",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    """
    Request model for chat endpoint.

    Contains the conversation history and user's current state.
    """

    messages: List[dict] = Field(
        description="Conversation history between user and assistant"
    )
    new_input: str = Field(
        description="User's latest input message"
    )
    departure: Optional[str] = Field(
        default=None,
        description="Saved departure/destination location"
    )
    distance: Optional[str] = Field(
        default=None,
        description="Saved travel distance/range"
    )
    score: Optional[int] = Field(
        default=None,
        description="Saved minimum attraction score"
    )
    season: Optional[str] = Field(
        default=None,
        description="Saved season preference"
    )


async def _convert_stream_to_async(streamer):
    """
    Convert synchronous stream to async generator.

    Args:
        streamer: The synchronous response streamer.

    Yields:
        Formatted server-sent event strings.
    """
    for response in streamer:
        content = response.output.choices[0].message.content
        yield await asyncio.to_thread(lambda c=content: f"data:{c}\n\n")


async def _generate_stream_response(streamer, metadata_json: str):
    """
    Generate streaming response with metadata header.

    Args:
        streamer: The response streamer (may be None).
        metadata_json: JSON string with response metadata.

    Yields:
        Server-sent event formatted strings.
    """
    # Send metadata first
    yield f"meta:{metadata_json}\n\n"

    # Stream content if available
    if streamer is not None:
        async for chunk in _convert_stream_to_async(streamer):
            yield chunk


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Process a chat message and return streaming response.

    This endpoint handles the travel planning conversation flow,
    managing state across multiple turns and returning responses
    as server-sent events for real-time streaming.

    Args:
        request: The chat request containing conversation state.

    Returns:
        StreamingResponse with server-sent events.
    """
    logger.info(f"[API] Received chat request: {request.new_input[:100]}...")
    logger.debug(f"[API] Request state: departure={request.departure}, distance={request.distance}, score={request.score}, season={request.season}")
    logger.debug(f"[API] Chat history length: {len(request.messages)}")
    
    try:
        # Create workflow with request state
        logger.info("[API] Creating TravelWorkflow...")
        workflow = TravelWorkflow(
            chat_history=request.messages,
            departure=request.departure,
            distance=request.distance,
            score=request.score,
            season=request.season,
        )

        # Process the chat asynchronously
        logger.info("[API] Processing chat...")
        streamer, response = await workflow.arun(request.new_input)
        
        logger.info(f"[API] Chat processed successfully, success={response.success}")
        logger.debug(f"[API] Response: need_reset={response.need_reset}, has_sql={response.sql is not None}")

        # Return streaming response
        return StreamingResponse(
            _generate_stream_response(streamer, response.model_dump_json()),
            media_type="text/event-stream",
        )

    except Exception as e:
        logger.error(f"[API] Chat processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status object.
    """
    return {"status": "healthy", "service": "obmms-api"}


@app.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
        API information object.
    """
    return {
        "name": "Travel Assistant API",
        "version": "0.2.0",
        "docs": "/docs",
    }
