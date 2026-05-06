import os
import time
import random
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST



app = FastAPI()

START_TIME = time.time()

MODE = os.getenv("MODE", "stable")
APP_VERSION = os.getenv("APP_VERSION", "1.0")
APP_PORT = int(os.getenv("APP_PORT", 3000))

# Metrics
# Counts every request
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"]
)

# Tracks how long requests take which is used to calculate P99 latency
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# How long the app has been running
app_uptime_seconds = Gauge(
    "app_uptime_seconds",
    "Application uptime in seconds"
)

# Current mode: 0 = stable, 1 = canary
app_mode_gauge = Gauge(
    "app_mode",
    "Deployment mode (0=stable, 1=canary)"
)

# Current chaos: 0 = none, 1 = slow, 2 = error
chaos_active = Gauge(
    "chaos_active",
    "Chaos state (0=none, 1=slow, 2=error)"
)

# Set initial values on startup
app_mode_gauge.set(1 if MODE == "canary" else 0)
chaos_active.set(0)

# Chaos State
chaos_mode = None
chaos_config = {}

@app.middleware("http")
async def chaos_middleware(request: Request, call_next):
    # Don't track the /metrics endpoint itself
    if request.url.path == "/metrics":
        return await call_next(request)

    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    # Update uptime on every request
    app_uptime_seconds.set(time.time() - START_TIME)

    # Record request count with labels
    http_requests_total.labels(
        method=request.method,
        path=request.url.path,
        status_code=str(response.status_code)
    ).inc()

    # Record how long this request took
    http_request_duration_seconds.labels(
        method=request.method,
        path=request.url.path
    ).observe(duration)

    return response


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
    

@app.get("/metrics")
async def metrics():
    # Update state metrics before serving
    app_uptime_seconds.set(time.time() - START_TIME)
    app_mode_gauge.set(1 if MODE == "canary" else 0)

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )    
    
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
        chaos_active.set(1)
        
    elif body.mode == "error":
        if body.rate is None or not (0 < body.rate <= 1):
            return JSONResponse(
                status_code=400, 
                content={"error": "'rate' between 0 and 1 required for error mode"}
            )
        chaos_mode = "error"
        chaos_config = {"rate": body.rate}
        chaos_active.set(2)
    
    elif body.mode == "recover":
        chaos_mode = None
        chaos_config = {}
        chaos_active.set(0)
    
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
    
    if request.url.path in ("/chaos", "/metrics"):
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