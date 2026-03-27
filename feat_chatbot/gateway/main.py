"""
Aarogyini – API Gateway
Single entry point on port 8000 for the Flutter app.

CHANGE FROM PREVIOUS VERSION:
  Added Pydantic request/response schemas to all POST endpoints so
  Swagger shows the full body schema and "Try it out" works correctly.
  The proxy logic is completely unchanged.
"""

import json
import httpx
from datetime import date
from typing import Optional, List, Any, Dict
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Aarogyini API Gateway",
    description="Single entry point — routes to Chatbot (:8001) and Tracker (:8002) services",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CHATBOT_URL = "http://chatbot:8001"
TRACKER_URL = "http://tracker:8002"
# Ollama running locally can be slow, especially on first request.
# Connect timeout is kept short; read timeout is set high for LLM generation.
TIMEOUT = httpx.Timeout(timeout=300.0, connect=10.0)


# ── Pydantic schemas (for Swagger docs + request validation) ──────────

class ChatMessageSchema(BaseModel):
    role:    str   # "user" | "assistant"
    content: str

class ChatMessageRequest(BaseModel):
    user_id:    str = Field(...,  example="user_123")
    session_id: str = Field(...,  example="session_abc")
    message:    str = Field(...,  example="What cycle phase am I in?")
    history:    List[ChatMessageSchema] = Field(default_factory=list)

class ChatMessageResponse(BaseModel):
    session_id:            str
    response:              str
    doctor_recommendation: Optional[str]       = None
    urgency_level:         Optional[str]       = None
    follow_up_questions:   Optional[List[str]] = None
    tips:                  Optional[List[str]] = None


class TrackerProfileSchema(BaseModel):
    age:              int       = Field(..., ge=10, le=60, example=28)
    weight:           float     = Field(..., example=62.0)
    height:           float     = Field(..., example=165.0)
    lifestyle:        str       = Field(..., example="lightly_active",
                                       description="sedentary | lightly_active | highly_active")
    stress_level:     str       = Field(..., example="low",
                                       description="low | medium | high")
    sleep_hours:      str       = Field(..., example="7-8h",
                                       description="4-5h | 5-6h | 6-7h | 7-8h | 8h+")
    period_duration:  str       = Field(..., example="4-5d",
                                       description="3-4d | 4-5d | 5-6d | 6d+")
    cycle_regularity: str       = Field(..., example="regular",
                                       description="regular | irregular")
    past_diagnosis:   List[str] = Field(default_factory=list, example=[])

class DailyLogSchema(BaseModel):
    log_date:       str       = Field(..., example="2026-03-27")
    period_status:  str       = Field("not_on_period", example="not_on_period",
                                      description="on_period | not_on_period")
    flow_intensity: str       = Field("low", example="medium",
                                      description="low | medium | high | very_high")
    daily_stress:   str       = Field("low", example="low",
                                      description="low | medium | high")
    daily_sleep:    str       = Field("7-8h", example="7-8h",
                                      description="4-5h | 5-6h | 6-7h | 7-8h | 8h+")
    symptoms:       List[str] = Field(
        default_factory=list,
        example=["Cramps", "Fatigue", "Bloating"],
        description=(
            "Multi-select from: Bloating, Headache, Acne, Craving, Breast Tenderness, "
            "Nipple Discharge, Frequent Urination, Fatigue, Vaginal Itching, "
            "Vaginal Dryness, Vaginal Pain, Cramps, Insomnia, Dizziness, Odour, Back Pain"
        ),
    )
    discharge: str = Field(
        "No Discharge",
        example="No Discharge",
        description=(
            "One of: No Discharge, Thick Discharge, Yellow or Green, "
            "Unusual Texture, Sticky, Egg White, Watery, Grayish"
        ),
    )

class TrackerInsightResponse(BaseModel):
    cycle_health:          str
    health_score:          int
    risks:                 List[str]
    recommendations:       List[str]
    predicted_next_period: Optional[str]
    cycle_phase:           str
    flags:                 List[str]

class GatewayHealthResponse(BaseModel):
    gateway:  str
    services: Dict[str, str]
    overall:  str


# ── Generic proxy helper ──────────────────────────────────────────────

async def _proxy(request: Request, target_url: str) -> Response:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        body = await request.body()
        upstream = await client.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            content=body,
            params=request.query_params,
        )
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(upstream.headers),
    )


# ── Tracker routes ────────────────────────────────────────────────────

@app.post(
    "/tracker/profile",
    tags=["tracker"],
    summary="Save or update user health profile",
    response_model=Dict[str, str],
)
async def tracker_save_profile(body: TrackerProfileSchema, request: Request):
    return await _proxy(request, f"{TRACKER_URL}/profile")


@app.get(
    "/tracker/profile",
    tags=["tracker"],
    summary="Fetch current user health profile",
    response_model=TrackerProfileSchema,
)
async def tracker_get_profile(request: Request):
    return await _proxy(request, f"{TRACKER_URL}/profile")


@app.post(
    "/tracker/log",
    tags=["tracker"],
    summary="Submit a daily health log entry",
    response_model=Dict[str, str],
)
async def tracker_submit_log(body: DailyLogSchema, request: Request):
    return await _proxy(request, f"{TRACKER_URL}/log")


@app.get(
    "/tracker/log/{log_date}",
    tags=["tracker"],
    summary="Fetch log for a specific date (YYYY-MM-DD)",
    response_model=DailyLogSchema,
)
async def tracker_get_log(log_date: str, request: Request):
    return await _proxy(request, f"{TRACKER_URL}/log/{log_date}")


@app.get(
    "/tracker/analyse",
    tags=["tracker"],
    summary="Run the 20-rule engine and get a full health insight",
    response_model=TrackerInsightResponse,
)
async def tracker_analyse(request: Request):
    return await _proxy(request, f"{TRACKER_URL}/analyse")


@app.get(
    "/tracker/history",
    tags=["tracker"],
    summary="Get all past daily log entries",
    response_model=List[DailyLogSchema],
)
async def tracker_history(request: Request):
    return await _proxy(request, f"{TRACKER_URL}/history")


# ── Chat routes ───────────────────────────────────────────────────────

@app.post(
    "/chat/message",
    tags=["chat"],
    summary="Send a chat message — auto-enriched with live tracker health data",
    response_model=ChatMessageResponse,
)
async def enriched_chat_message(body: ChatMessageRequest, request: Request):
    """
    Key integration endpoint. Before forwarding to the Chatbot service:

    1. Fetches `/tracker/analyse` (best-effort, 5 s timeout).
    2. Injects the result as `tracker_context` into the request body.
    3. Forwards the enriched payload to the Chatbot service.

    The LLM therefore always knows the user's current **health score**,
    **cycle phase**, and **active risk flags** — automatically, on every
    single message, with no extra work from the Flutter app.
    """
    payload = body.model_dump()

    # Step 1: fetch tracker insight (best-effort — chat still works if tracker is down)
    tracker_context: Dict[str, Any] = {}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            res = await client.get(f"{TRACKER_URL}/analyse")
            if res.status_code == 200:
                tracker_context = res.json()
    except Exception:
        pass

    # Step 2: inject
    if tracker_context:
        payload["tracker_context"] = tracker_context

    # Step 3: forward
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        upstream = await client.post(
            f"{CHATBOT_URL}/chat/message",
            json=payload,
            headers={k: v for k, v in request.headers.items()
                     if k.lower() not in ("host", "content-length")},
        )
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(upstream.headers),
    )


@app.delete(
    "/chat/session/{session_id}",
    tags=["chat"],
    summary="Clear conversation memory for a session",
    response_model=Dict[str, str],
)
async def chat_clear_session(session_id: str, request: Request):
    return await _proxy(request, f"{CHATBOT_URL}/chat/session/{session_id}")


# ── Gateway health check ──────────────────────────────────────────────

@app.get(
    "/health",
    tags=["gateway"],
    summary="Aggregated liveness check — polls both services",
    response_model=GatewayHealthResponse,
)
async def health():
    results: Dict[str, str] = {}
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
        for name, url in [("chatbot", CHATBOT_URL), ("tracker", TRACKER_URL)]:
            try:
                r = await client.get(f"{url}/health")
                results[name] = r.json().get("status", "unknown")
            except Exception:
                results[name] = "unreachable"
    overall = "healthy" if all(v == "healthy" for v in results.values()) else "degraded"
    return {"gateway": "healthy", "services": results, "overall": overall}