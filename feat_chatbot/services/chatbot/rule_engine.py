"""
Aarogyini Chatbot - Rule Engine
Maps symptoms and health data to conditions, urgency levels, and recommendations.
"""

from models import UserHealthProfile, RuleEngineInsight, UrgencyLevel, CyclePhase
from typing import List


# ─────────────────────────────────────────────
# Symptom → Condition Mapping Rules
# ─────────────────────────────────────────────

SYMPTOM_RULES = [
    {
        "symptoms": ["irregular_cycle", "weight_gain", "acne", "excess_hair"],
        "min_match": 2,
        "condition": "PCOS Risk Detected",
        "recommendation": "These symptoms may indicate PCOS. A gynecologist visit and hormonal panel is recommended.",
        "urgency": UrgencyLevel.MEDIUM,
    },
    {
        "symptoms": ["severe_cramps", "heavy_bleeding", "pelvic_pain"],
        "min_match": 2,
        "condition": "Possible Endometriosis Indicators",
        "recommendation": "Severe cramps with heavy bleeding may indicate endometriosis. Please consult a doctor.",
        "urgency": UrgencyLevel.HIGH,
    },
    {
        "symptoms": ["unusual_discharge", "itching", "burning_urination"],
        "min_match": 2,
        "condition": "Possible Vaginal Infection",
        "recommendation": "These symptoms suggest a possible infection. A doctor visit for proper diagnosis is advised.",
        "urgency": UrgencyLevel.HIGH,
    },
    {
        "symptoms": ["missed_period", "nausea", "breast_tenderness"],
        "min_match": 2,
        "condition": "Possible Pregnancy Indicator",
        "recommendation": "These symptoms may indicate pregnancy. Consider taking a home pregnancy test and consulting a doctor.",
        "urgency": UrgencyLevel.MEDIUM,
    },
    {
        "symptoms": ["heavy_bleeding", "dizziness", "fatigue"],
        "min_match": 2,
        "condition": "Possible Anemia Risk",
        "recommendation": "Heavy bleeding with fatigue and dizziness may indicate anemia. Iron levels should be checked.",
        "urgency": UrgencyLevel.MEDIUM,
    },
    {
        "symptoms": ["severe_abdominal_pain", "fever", "vomiting"],
        "min_match": 2,
        "condition": "Acute Abdominal Emergency Risk",
        "recommendation": "These symptoms require IMMEDIATE medical attention. Please visit an emergency room.",
        "urgency": UrgencyLevel.EMERGENCY,
    },
]

CYCLE_PHASE_TIPS = {
    CyclePhase.MENSTRUAL: [
        "Stay hydrated and rest as much as possible.",
        "Use a heating pad on your lower abdomen to ease cramps.",
        "Eat iron-rich foods like spinach, lentils, and dates.",
        "Avoid excessive caffeine and salty foods.",
        "Light yoga and walking can help relieve pain naturally.",
    ],
    CyclePhase.FOLLICULAR: [
        "Great phase to start a new workout routine – energy is increasing!",
        "Eat protein-rich and nutrient-dense foods.",
        "Focus on creative tasks and learning; your brain is sharp now.",
        "Drink plenty of water to support follicle development.",
    ],
    CyclePhase.OVULATION: [
        "Peak fertility window – track if you're planning or avoiding pregnancy.",
        "Include antioxidant-rich foods like berries and leafy greens.",
        "Energy levels are highest – excellent time for intense workouts.",
        "You may notice increased libido and social energy – this is normal.",
    ],
    CyclePhase.LUTEAL: [
        "PMS symptoms like bloating, mood swings, and cravings are common.",
        "Magnesium-rich foods (nuts, dark chocolate) help with mood.",
        "Reduce caffeine and alcohol to ease PMS symptoms.",
        "Prioritize sleep and stress-reduction practices like meditation.",
        "Light exercise like yoga can ease bloating and irritability.",
    ],
}

RISK_FLAG_RULES = {
    "PCOS_RISK": {
        "condition": "PCOS Risk Flag Active",
        "recommendation": "Your profile shows PCOS risk indicators. Monitor symptoms and get regular hormonal check-ups.",
        "urgency": UrgencyLevel.MEDIUM,
    },
    "IRREGULAR_CYCLE": {
        "condition": "Irregular Menstrual Cycle",
        "recommendation": "Irregular cycles can have many causes. Track your cycle consistently and consult a gynecologist if irregularity persists beyond 3 months.",
        "urgency": UrgencyLevel.LOW,
    },
    "INFECTION_RISK": {
        "condition": "Infection Risk Flag",
        "recommendation": "Maintain hygiene practices. If symptoms worsen or persist, consult a doctor promptly.",
        "urgency": UrgencyLevel.HIGH,
    },
    "LOW_HEALTH_SCORE": {
        "condition": "Low Overall Health Score",
        "recommendation": "Your health score is below optimal. Focus on nutrition, sleep, and regular exercise. Consider a full health check-up.",
        "urgency": UrgencyLevel.LOW,
    },
}


# ─────────────────────────────────────────────
# Rule Engine Class
# ─────────────────────────────────────────────

class RuleEngine:
    def analyze(self, profile: UserHealthProfile) -> List[RuleEngineInsight]:
        insights: List[RuleEngineInsight] = []

        # 1. Symptom-based rules
        user_symptoms = {s.name.lower().replace(" ", "_") for s in profile.symptoms}
        for rule in SYMPTOM_RULES:
            matches = sum(1 for s in rule["symptoms"] if s in user_symptoms)
            if matches >= rule["min_match"]:
                confidence = min(matches / len(rule["symptoms"]) + 0.2, 1.0)
                insights.append(RuleEngineInsight(
                    condition=rule["condition"],
                    confidence=round(confidence, 2),
                    recommendation=rule["recommendation"],
                    urgency=rule["urgency"],
                ))

        # 2. Risk flag rules
        for flag in profile.risk_flags:
            if flag in RISK_FLAG_RULES:
                r = RISK_FLAG_RULES[flag]
                insights.append(RuleEngineInsight(
                    condition=r["condition"],
                    confidence=0.85,
                    recommendation=r["recommendation"],
                    urgency=r["urgency"],
                ))

        # 3. Low health score rule
        if profile.health_score is not None and profile.health_score < 40:
            r = RISK_FLAG_RULES["LOW_HEALTH_SCORE"]
            insights.append(RuleEngineInsight(
                condition=r["condition"],
                confidence=1.0,
                recommendation=r["recommendation"],
                urgency=r["urgency"],
            ))

        return insights

    def get_cycle_tips(self, phase: CyclePhase) -> List[str]:
        return CYCLE_PHASE_TIPS.get(phase, [])