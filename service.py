import os
from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from main import MeetingAgent
from src.common.logger import agent_logger as logger

# Load environment variables (if any .env file exists)
load_dotenv()

API_KEY = os.getenv("API_KEY", "secret")

app = FastAPI(title="WeMeet Automated Service")

# Single global instance of agent
agent = MeetingAgent()

class JoinRequest(BaseModel):
    meeting_id: str

def verify_api_key(x_api_key: str = Header(default="", alias="x-api-key")):
    """Dependency to verify API Key."""
    if x_api_key != API_KEY:
        logger.warning("Unauthorized access attempt with invalid API Key.")
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return x_api_key

@app.post("/meeting/join", status_code=202)
def join_meeting(request: JoinRequest, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Endpoint to trigger joining a meeting.
    Expects JSON: {"meeting_id": "123456"}
    Header: x-api-key: secret
    """
    # Check if this meeting is already being processed
    state = agent.get_meeting_state(request.meeting_id)
    if state.get("status") in ["in_progress", "joining"]:
        return JSONResponse(status_code=400, content={"message": f"Meeting {request.meeting_id} is already in progress."})

    # Dispatch to background task
    background_tasks.add_task(agent.process_meeting, request.meeting_id)
    
    logger.info(f"Accepted request to join meeting: {request.meeting_id}")
    return {"message": f"Join request for meeting {request.meeting_id} accepted.", "status": "joining"}

@app.get("/meeting/download/{meeting_id}")
def download_meeting(meeting_id: str, api_key: str = Depends(verify_api_key)):
    """
    Check status of meeting recording or download completed MP3 file.
    Header: x-api-key: secret
    """
    state = agent.get_meeting_state(meeting_id)
    status = state.get("status")

    if status == "not_found":
        raise HTTPException(status_code=404, detail="Meeting ID not found in history or current session.")
    elif status in ["in_progress", "joining"]:
        return {"status": "in progress"}
    elif status == "failed":
        # Additional context could be parsed if we saved reasons, but returning failed is standard
        return {"status": "failed", "message": "Failed to join or record the meeting."}
    elif status == "completed":
        file_path = state.get("file")
        if file_path and os.path.exists(file_path):
            logger.info(f"Serving download for meeting {meeting_id} via {file_path}")
            return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type="audio/mpeg")
        else:
            logger.error(f"Recording marked completed but file missing: {file_path}")
            raise HTTPException(status_code=500, detail="Recording marked as completed but file not found on disk.")
    
    return {"status": status}
