import os
import time
import random
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


app = FastAPI()

START_TIME = time.time()

MODE = os.getenv("MODE", "stable")
APP_VERSION = os.getenv("APP_VERSION", "1.0")
APP_PORT = int(os.getenv("APP_PORT", 3000))

# Chaos State
chaos_mode = None
chaos_config = {}

@app.middleware("http")
async def chaos_middleware(request: Request, call_next):
    response = await call_next(request)
    if MODE == "canary":
        response.headers["X-Mode"] = "canary"
    return response

@app.get("/")
async def root():
    return {
        "message": "Welcome to SwiftDeploy API",
        "mode": MODE,
        "app_version": APP_VERSION,
        "timestamp": int(time.time())
    }


@app.get("/healthz")
async def health():
    uptime = int(time.time() - START_TIME)
    return {
        "status": "ok",
        "app_version": APP_VERSION,
        "uptime_seconds": uptime
    }
    
    
class ChaosBody(BaseModel):
    mode: str
    duration: Optional[float] = None
    rate: Optional[float] = None
    

@app.post("/chaos")
async def chaos(body: ChaosBody):
    global chaos_mode, chaos_config
    
    if MODE != "canary":
        return JSONResponse(
            status_code=403,
            content={
                "error": "Chaos only in canary mode"
            }
        )
    
    
    if body.mode == "slow":
        if body.duration is None or body.duration <= 0:
            return JSONResponse(
                status_code=400, 
                content={"error": "'duration' required for slow mode"}
            )
        chaos_mode = "slow"
        chaos_config = {"duration": body.duration}
        
    elif body.mode == "error":
        if body.rate is None or not (0 < body.rate <= 1):
            return JSONResponse(
                status_code=400, 
                content={"error": "'rate' between 0 and 1 required for error mode"}
            )
        chaos_mode = "error"
        chaos_config = {"rate": body.rate}
    
    elif body.mode == "recover":
        chaos_mode = None
        chaos_config = {}
    
    else:
        return JSONResponse(
            status_code=400, 
            content={"error": f"unknown mode '{body.mode}'. valid: slow, error, recover"}
        )
          
    return {
        "status": "Chaos mode updated"
    }
    
@app.middleware("http")
async def apply_chaos(request: Request, call_next):
    global chaos_mode, chaos_config 
    
    if request.url.path == "/chaos":
        return await call_next(request)     
    
    if MODE == "canary":               
        if chaos_mode == "slow":
            time.sleep(chaos_config.get("duration", 1))

        elif chaos_mode == "error":
            if random.random() < chaos_config.get("rate", 0.5):
                return JSONResponse(
                    status_code=500, 
                    content={"error": "Injected failure"}
                )

    return await call_next(request)