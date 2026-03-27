"""
Aarogyini Chatbot - Safety Guardrails
Input validation and output sanitization to prevent unsafe medical advice.
"""

import re
from typing import Dict


# ─────────────────────────────────────────────
# Blocked Patterns (input)
# ─────────────────────────────────────────────

BLOCKED_INPUT_PATTERNS = [
    r"\b(diagnose me|tell me i have|i definitely have|confirm my diagnosis)\b",
    r"\b(prescribe|what dosage|how many mg|take this medicine|give me medicine)\b",
    r"\b(abort|abortion|terminate pregnancy)\b",
    r"\b(self harm|hurt myself|end my life)\b",
]

# Phrases the LLM should NEVER say in output
BLOCKED_OUTPUT_PATTERNS = [
    r"\byou have (cancer|tumor|fibroid|cyst|endometriosis|PCOS)\b",
    r"\btake \d+\s?mg\b",
    r"\bprescribe\b",
    r"\bi diagnose\b",
    r"\bdefinitely have\b",
]

SAFE_DISCLAIMER = (
    "\n\n⚠️ *Please note: I am an AI assistant and cannot provide medical diagnoses or prescriptions. "
    "Always consult a qualified healthcare professional for medical advice.*"
)

CRISIS_RESPONSE = (
    "I'm really sorry you're going through this. Your wellbeing matters deeply. "
    "Please reach out to iCall (India): 9152987821 or Vandrevala Foundation: 1860-2662-345. "
    "You are not alone. 💙"
)

BLOCKED_RESPONSE = (
    "I'm here to help with general menstrual and women's health information, but I can't assist with "
    "that specific request. For medical diagnoses or prescriptions, please consult a qualified doctor. "
    "Is there something else about your health I can help explain or guide you on?"
)


class SafetyGuardrail:

    def check_input(self, user_message: str) -> Dict:
        """
        Check user input for unsafe or blocked content.
        Returns {"safe": bool, "reason": str, "fallback_response": str}
        """
        msg_lower = user_message.lower()

        # Crisis / self-harm detection
        crisis_keywords = ["hurt myself", "end my life", "kill myself", "want to die", "self harm"]
        if any(kw in msg_lower for kw in crisis_keywords):
            return {
                "safe": False,
                "reason": "crisis_content",
                "fallback_response": CRISIS_RESPONSE,
            }

        # Blocked medical request patterns
        for pattern in BLOCKED_INPUT_PATTERNS:
            if re.search(pattern, msg_lower):
                return {
                    "safe": False,
                    "reason": "blocked_medical_request",
                    "fallback_response": BLOCKED_RESPONSE,
                }

        return {"safe": True, "reason": None, "fallback_response": None}

    def sanitize_output(self, response: str) -> str:
        """
        Remove or soften any dangerous claims from LLM output.
        Always append disclaimer if health-sensitive.
        """
        sanitized = response

        # Replace diagnostic language
        sanitized = re.sub(
            r"\b(you have|you are diagnosed with|you definitely have)\b",
            "your symptoms may suggest",
            sanitized,
            flags=re.IGNORECASE,
        )

        # Remove dosage mentions
        sanitized = re.sub(r"\btake \d+\s?mg\b", "consult a doctor for appropriate dosage", sanitized, flags=re.IGNORECASE)

        # Append disclaimer if response contains medical keywords
        health_keywords = ["symptom", "condition", "treatment", "pain", "bleeding", "infection", "PCOS", "cycle"]
        if any(kw.lower() in sanitized.lower() for kw in health_keywords):
            if SAFE_DISCLAIMER not in sanitized:
                sanitized += SAFE_DISCLAIMER

        return sanitized