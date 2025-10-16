"""
Logs API endpoints
"""
import os
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from typing import Optional

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_FILE = BASE_DIR / 'logs' / 'app.log'


@router.get("/logs/tail")
async def get_logs(lines: int = 100):
    """
    Get last N lines from log file
    """
    if not LOG_FILE.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    
    try:
        # Use async file reading to not block
        loop = asyncio.get_event_loop()
        
        def read_file():
            with open(LOG_FILE, 'r') as f:
                all_lines = f.readlines()
                tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return {
                    "lines": tail_lines,
                    "total_lines": len(all_lines),
                    "returned_lines": len(tail_lines)
                }
        
        return await loop.run_in_executor(None, read_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/download", response_class=PlainTextResponse)
async def download_logs():
    """
    Download complete log file
    """
    if not LOG_FILE.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    
    try:
        loop = asyncio.get_event_loop()
        
        def read_file():
            with open(LOG_FILE, 'r') as f:
                return f.read()
        
        return await loop.run_in_executor(None, read_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/logs/clear")
async def clear_logs():
    """
    Clear log file
    """
    if not LOG_FILE.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    
    try:
        loop = asyncio.get_event_loop()
        
        def clear_file():
            with open(LOG_FILE, 'w') as f:
                f.write("")
        
        await loop.run_in_executor(None, clear_file)
        return {"message": "Log file cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/logs/stream")
async def stream_logs(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log streaming
    """
    await websocket.accept()
    
    try:
        last_position = 0
        
        while True:
            if LOG_FILE.exists():
                try:
                    loop = asyncio.get_event_loop()
                    
                    def read_new_lines():
                        nonlocal last_position
                        with open(LOG_FILE, 'r') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            last_position = f.tell()
                            return new_lines
                    
                    new_lines = await loop.run_in_executor(None, read_new_lines)
                    
                    if new_lines:
                        await websocket.send_json({
                            "type": "logs",
                            "lines": new_lines
                        })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
            
            # Wait before checking again
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"WebSocket error: {str(e)}"
            })
        except:
            pass
