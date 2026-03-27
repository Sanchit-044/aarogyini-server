"""
Aarogyini Chatbot - Data Models
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class CyclePhase(str, Enum):
    MENSTRUAL = "menstrual"
    FOLLICULAR = "follicular"
    OVULATION = "ovulation"
    LUTEAL = "luteal"
    UNKNOWN = "unknown"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ─────────────────────────────────────────────
# Chat Models
# ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: str
    response: str
    doctor_recommendation: Optional[str] = None
    urgency_level: Optional[UrgencyLevel] = None
    follow_up_questions: Optional[List[str]] = None
    tips: Optional[List[str]] = None


# ─────────────────────────────────────────────
# Health Data Models
# ─────────────────────────────────────────────

class Symptom(BaseModel):
    name: str
    severity: int = Field(ge=1, le=10, description="Severity 1 (mild) to 10 (severe)")
    duration_days: Optional[int] = None


class UserHealthProfile(BaseModel):
    user_id: str
    age: Optional[int] = None
    cycle_phase: CyclePhase = CyclePhase.UNKNOWN
    cycle_length_days: Optional[int] = None
    last_period_date: Optional[str] = None
    symptoms: List[Symptom] = Field(default_factory=list)
    health_score: Optional[float] = None
    risk_flags: List[str] = Field(default_factory=list)   # e.g. ["PCOS_RISK", "IRREGULAR_CYCLE"]
    notes: Optional[str] = None


class HealthLogEntry(BaseModel):
    user_id: str
    date: str
    flow_level: Optional[str] = None          # "light" | "medium" | "heavy"
    pain_level: Optional[int] = Field(default=None, ge=0, le=10)
    mood: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class RuleEngineInsight(BaseModel):
    condition: str
    confidence: float = Field(ge=0.0, le=1.0)
    recommendation: str
    urgency: UrgencyLevel = UrgencyLevel.LOW