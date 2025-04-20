from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from custom_agents import orchestrator
from openai.types.responses import ResponseInputImageParam, ResponseInputTextParam
from openai.types.responses.response_input_item_param import Message
from agents import Runner
import asyncio
import json

app = FastAPI()

# Define the request models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str  # Current message
    history: List[ChatMessage]  # Chat history
    image: Optional[str] = None  # Optional base64 encoded image

# Async generator for streaming responses
async def stream_response(result_gen):
    try:
        async for chunk in result_gen:
            if isinstance(chunk, str):
                yield chunk
            else:
                # If it's not a string, it might be a structured data piece
                yield json.dumps({"content": chunk}) + "\n"
    except Exception as e:
        yield json.dumps({"error": str(e)}) + "\n"

# Function to process the chat request
async def process_chat_request(message: str, history: List[ChatMessage], image: Optional[str] = None):
    # Prepare message content
    text = f"""
        current_message : {message},
        conversation_history : {history}
    """
    content = [ResponseInputTextParam(text=text, type="input_text")]
    
    # Add image if provided
    if image:
        # Extract the base64 image without metadata if present
        if "base64," in image:
            image = image.split("base64,")[1]
        
        # Add image parameter
        content.append(
            ResponseInputImageParam(
                detail="low",
                image_url=f"data:image/jpeg;base64,{image}",
                type="input_image"
            )
        )
    
    # Create a message object
    user_message = Message(
        content=content,
        role="user"
    )
    
    # Run through your orchestrator
    result = await Runner.run(orchestrator, input=[user_message])
    
    # Assume result.final_output is the response we want to stream
    # If it's a string, yield it directly
    if isinstance(result.final_output, str):
        for chunk in result.final_output.split():  # Simple splitting for demo
            yield chunk + " "
            await asyncio.sleep(0.05)  # Simulated delay for streaming effect
    # If it's an async generator already
    elif hasattr(result.final_output, "__aiter__"):
        async for chunk in result.final_output:
            yield chunk
    # Otherwise, yield the entire result
    else:
        yield str(result.final_output)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint that accepts a message, history, and optional image.
    Returns a streaming response from the LLM.
    """
    # Process the request and get a streaming response
    response_generator = process_chat_request(
        message=request.message,
        history=request.history,
        image=request.image
    )
    
    # Return a streaming response
    return StreamingResponse(
        stream_response(response_generator),
        media_type="text/event-stream"
    )

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)