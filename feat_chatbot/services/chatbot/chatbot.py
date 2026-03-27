"""
Aarogyini Chatbot - LangChain Chatbot Engine
Core AI engine: prompt templates, memory, LLM, guardrails.
"""

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.chains import LLMChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from config import settings
from models import UserHealthProfile, RuleEngineInsight, CyclePhase, UrgencyLevel
from rule_engine import RuleEngine
from guardrails import SafetyGuardrail

from typing import List, Optional, Dict
import json
import re


# ─────────────────────────────────────────────
# System Prompt Template
# ─────────────────────────────────────────────

AAROGYINI_SYSTEM_PROMPT = """You are Aarogyini, a compassionate and knowledgeable AI health assistant 
specializing in women's menstrual and reproductive health. You were created to empower women with 
clear, evidence-based health information.

## Your Personality
- Warm, empathetic, and non-judgmental
- Speak in simple, easy-to-understand language
- Use culturally sensitive language appropriate for Indian women
- Be encouraging and supportive

## Your Capabilities
- Explain menstrual health, cycle phases, and related symptoms
- Interpret health scores and reports in simple language
- Provide cycle-phase-specific guidance and lifestyle tips
- Explain health alerts (PCOS, infections, irregular cycles)
- Recommend when to see a doctor (with urgency level)
- Give hygiene and wellness tips

## STRICT SAFETY RULES (Never Violate)
1. NEVER provide medical diagnoses
2. NEVER prescribe or recommend specific medications or dosages
3. ALWAYS recommend consulting a doctor for serious or persistent symptoms
4. If urgency is HIGH or EMERGENCY, immediately tell the user to seek medical attention
5. Never provide information that could cause self-harm
6. Always acknowledge the limits of AI-based health advice

## User Context
{user_context}

## Health Insights from Rule Engine
{health_insights}

## Current Cycle Phase
{cycle_phase}

## Response Guidelines
- Keep responses concise (150-300 words unless detail is needed)
- Use bullet points for tips and recommendations
- End responses with 1-2 relevant follow-up questions when appropriate
- Always maintain a warm, caring tone
"""

CYCLE_PHASE_GUIDANCE = {
    CyclePhase.MENSTRUAL: "The user is in their menstrual phase (Day 1-5). Focus on comfort, rest, iron-rich foods, and pain management tips.",
    CyclePhase.FOLLICULAR: "The user is in their follicular phase (Day 6-13). Energy is rising. Focus on activity, nutrition, and positive habits.",
    CyclePhase.OVULATION: "The user is in their ovulation phase (Day 14). Peak fertility and energy. Focus on nutrition and wellness.",
    CyclePhase.LUTEAL: "The user is in their luteal phase (Day 15-28). PMS may occur. Focus on managing mood, cravings, and bloating.",
    CyclePhase.UNKNOWN: "Cycle phase is unknown. Provide general menstrual health guidance.",
}


# ─────────────────────────────────────────────
# Session Memory Store (in-memory; swap for Redis in production)
# ─────────────────────────────────────────────

class SessionMemoryStore:
    def __init__(self):
        self._store: Dict[str, ConversationBufferWindowMemory] = {}

    def get_or_create(self, session_id: str) -> ConversationBufferWindowMemory:
        if session_id not in self._store:
            self._store[session_id] = ConversationBufferWindowMemory(
                k=settings.MAX_CONVERSATION_TURNS // 2,
                return_messages=True,
                memory_key="chat_history",
            )
        return self._store[session_id]

    def clear(self, session_id: str):
        if session_id in self._store:
            del self._store[session_id]


memory_store = SessionMemoryStore()


# ─────────────────────────────────────────────
# LLM Factory
# ─────────────────────────────────────────────

def get_llm():
    if settings.LLM_PROVIDER == "ollama":
        return ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
        )
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        max_tokens=settings.MAX_TOKENS,
        temperature=0.7,
    )


# ─────────────────────────────────────────────
# Chatbot Engine
# ─────────────────────────────────────────────

class AarogyiniChatbot:
    def __init__(self):
        self.llm = get_llm()
        self.rule_engine = RuleEngine()
        self.guardrail = SafetyGuardrail()

    def _build_user_context(self, profile: UserHealthProfile) -> str:
        if not profile:
            return "No user profile available."
        parts = []
        if profile.age:
            parts.append(f"Age: {profile.age}")
        if profile.health_score is not None:
            parts.append(f"Health Score: {profile.health_score:.1f}/100")
        if profile.risk_flags:
            parts.append(f"Risk Flags: {', '.join(profile.risk_flags)}")
        if profile.symptoms:
            sym_list = ", ".join(f"{s.name} (severity {s.severity}/10)" for s in profile.symptoms)
            parts.append(f"Current Symptoms: {sym_list}")
        if profile.last_period_date:
            parts.append(f"Last Period: {profile.last_period_date}")
        return "\n".join(parts) if parts else "Basic profile, no detailed health data."

    def _build_insights_context(self, insights: List[RuleEngineInsight]) -> str:
        if not insights:
            return "No specific insights generated."
        lines = []
        for ins in insights:
            lines.append(
                f"- [{ins.urgency.value.upper()}] {ins.condition}: {ins.recommendation}"
            )
        return "\n".join(lines)

    async def chat(
        self,
        user_message: str,
        session_id: str,
        profile: Optional[UserHealthProfile] = None,
        history: Optional[list] = None,
    ) -> dict:
        # 1. Input safety check
        safety_check = self.guardrail.check_input(user_message)
        if not safety_check["safe"]:
            return {
                "response": safety_check["fallback_response"],
                "doctor_recommendation": "Please consult a healthcare professional.",
                "urgency_level": UrgencyLevel.MEDIUM,
                "follow_up_questions": [],
                "tips": [],
            }

        # 2. Run rule engine
        insights: List[RuleEngineInsight] = []
        if profile:
            insights = self.rule_engine.analyze(profile)

        # 3. Determine urgency
        max_urgency = UrgencyLevel.LOW
        for ins in insights:
            if ins.urgency == UrgencyLevel.EMERGENCY:
                max_urgency = UrgencyLevel.EMERGENCY
                break
            elif ins.urgency == UrgencyLevel.HIGH:
                max_urgency = UrgencyLevel.HIGH
            elif ins.urgency == UrgencyLevel.MEDIUM and max_urgency == UrgencyLevel.LOW:
                max_urgency = UrgencyLevel.MEDIUM

        # 4. Build prompt
        cycle_phase = profile.cycle_phase if profile else CyclePhase.UNKNOWN
        system_content = AAROGYINI_SYSTEM_PROMPT.format(
            user_context=self._build_user_context(profile) if profile else "No profile provided.",
            health_insights=self._build_insights_context(insights),
            cycle_phase=CYCLE_PHASE_GUIDANCE.get(cycle_phase, CYCLE_PHASE_GUIDANCE[CyclePhase.UNKNOWN]),
        )

        # 5. Build messages with history
        messages = [SystemMessage(content=system_content)]
        if history:
            for msg in history[-10:]:  # last 10 messages for context window control
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))
        messages.append(HumanMessage(content=user_message))

        # 6. Call LLM
        response = await self.llm.ainvoke(messages)
        raw_response = response.content if hasattr(response, "content") else str(response)

        # 7. Output safety check
        raw_response = self.guardrail.sanitize_output(raw_response)

        # 8. Extract structured parts (tips, follow-up Qs, doctor advice)
        parsed = self._parse_response(raw_response, max_urgency)
        return parsed

    def _parse_response(self, response: str, urgency: UrgencyLevel) -> dict:
        """Extract tips, follow-up questions, and doctor recommendations from response."""
        tips = []
        follow_up_questions = []
        doctor_recommendation = None

        # Extract bullet tips
        tip_pattern = re.compile(r"^[\-\•\*]\s+(.+)$", re.MULTILINE)
        tip_matches = tip_pattern.findall(response)
        tips = [t.strip() for t in tip_matches if "?" not in t][:5]

        # Extract follow-up questions
        q_pattern = re.compile(r"(.+\?)\s*$", re.MULTILINE)
        q_matches = q_pattern.findall(response)
        follow_up_questions = [q.strip() for q in q_matches][:2]

        # Doctor recommendation based on urgency
        if urgency == UrgencyLevel.EMERGENCY:
            doctor_recommendation = "⚠️ Please visit an emergency room or call your doctor immediately."
        elif urgency == UrgencyLevel.HIGH:
            doctor_recommendation = "Please consult a doctor as soon as possible (within 24-48 hours)."
        elif urgency == UrgencyLevel.MEDIUM:
            doctor_recommendation = "It is advisable to schedule an appointment with your gynecologist."

        return {
            "response": response,
            "doctor_recommendation": doctor_recommendation,
            "urgency_level": urgency,
            "follow_up_questions": follow_up_questions,
            "tips": tips,
        }