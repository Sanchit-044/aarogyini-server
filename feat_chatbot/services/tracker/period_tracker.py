"""
Aarogyini Period Logger & Cycle Tracker
Rule-based health insight engine for women's menstrual health.

CHANGES FROM ORIGINAL:
  Profile:
    - stress_level: int (0-3)     -> str ("low"/"medium"/"high")
    - sleep_hours: int             -> str ("4-5h"/"5-6h"/"6-7h"/"7-8h"/"8h+")
    - lifestyle values             -> "sedentary"/"lightly_active"/"highly_active"
    - period_duration: int         -> str ("3-4d"/"4-5d"/"5-6d"/"6d+")
    - avg_cycle_length             -> removed (derived from logged period dates)
    - last_period_start            -> removed (derived from logs)

  DailyLog:
    - period_day: bool             -> period_status: str ("on_period"/"not_on_period")
    - flow_intensity: int (0-3)    -> str ("low"/"medium"/"high"/"very_high")
    - all individual symptom ints  -> symptoms: list[str] (multi-select)
    - discharge_type + color       -> discharge: str (single select)
    - daily_stress added           -> str ("low"/"medium"/"high")
    - daily_sleep added            -> str (same options as profile sleep)
    - clotting, spotting removed
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
import json


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

STRESS_LEVELS    = ("low", "medium", "high")
SLEEP_OPTIONS    = ("4-5h", "5-6h", "6-7h", "7-8h", "8h+")
LIFESTYLES       = ("sedentary", "lightly_active", "highly_active")
PERIOD_DURATIONS = ("3-4d", "4-5d", "5-6d", "6d+")
FLOW_LEVELS      = ("low", "medium", "high", "very_high")
PERIOD_STATUSES  = ("on_period", "not_on_period")

VALID_SYMPTOMS = {
    "Bloating", "Headache", "Acne", "Craving", "Breast Tenderness",
    "Nipple Discharge", "Frequent Urination", "Fatigue", "Vaginal Itching",
    "Vaginal Dryness", "Vaginal Pain", "Cramps", "Insomnia", "Dizziness",
    "Odour", "Back Pain",
}

VALID_DISCHARGES = {
    "No Discharge", "Thick Discharge", "Yellow or Green", "Unusual Texture",
    "Sticky", "Egg White", "Watery", "Grayish",
}


# ── Numeric converters for scoring ───────────────────────────────────

def stress_to_int(s: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(s, 1)

def sleep_to_hours(s: str) -> float:
    return {"4-5h": 4.5, "5-6h": 5.5, "6-7h": 6.5, "7-8h": 7.5, "8h+": 8.5}.get(s, 7.0)

def flow_to_int(s: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "very_high": 3}.get(s, 0)

def duration_to_days(s: str) -> int:
    return {"3-4d": 3, "4-5d": 4, "5-6d": 5, "6d+": 7}.get(s, 5)


# ─────────────────────────────────────────
# 1. DATA MODELS
# ─────────────────────────────────────────

@dataclass
class UserProfile:
    age:              int
    weight:           float
    height:           float
    lifestyle:        str
    stress_level:     str
    sleep_hours:      str
    period_duration:  str
    cycle_regularity: str
    past_diagnosis:   list[str] = field(default_factory=list)


@dataclass
class DailyLog:
    log_date:       date
    period_status:  str        = "not_on_period"
    flow_intensity: str        = "low"
    daily_stress:   str        = "low"
    daily_sleep:    str        = "7-8h"
    symptoms:       list[str]  = field(default_factory=list)
    discharge:      str        = "No Discharge"


@dataclass
class HealthInsight:
    cycle_health:          str
    health_score:          int
    risks:                 list[str]
    recommendations:       list[str]
    predicted_next_period: Optional[date]
    cycle_phase:           str
    flags:                 list[str]


# ─────────────────────────────────────────
# 2. VALIDATION
# ─────────────────────────────────────────

class ValidationError(Exception):
    pass


def validate_profile(profile: UserProfile) -> list[str]:
    errors = []
    if not (10 <= profile.age <= 60):
        errors.append("Age must be between 10 and 60.")
    if profile.lifestyle not in LIFESTYLES:
        errors.append(f"lifestyle must be one of {LIFESTYLES}.")
    if profile.stress_level not in STRESS_LEVELS:
        errors.append(f"stress_level must be one of {STRESS_LEVELS}.")
    if profile.sleep_hours not in SLEEP_OPTIONS:
        errors.append(f"sleep_hours must be one of {SLEEP_OPTIONS}.")
    if profile.period_duration not in PERIOD_DURATIONS:
        errors.append(f"period_duration must be one of {PERIOD_DURATIONS}.")
    if profile.cycle_regularity not in ("regular", "irregular"):
        errors.append("cycle_regularity must be 'regular' or 'irregular'.")
    return errors


def validate_log(log: DailyLog) -> list[str]:
    errors = []
    if log.period_status not in PERIOD_STATUSES:
        errors.append(f"period_status must be one of {PERIOD_STATUSES}.")
    if log.flow_intensity not in FLOW_LEVELS:
        errors.append(f"flow_intensity must be one of {FLOW_LEVELS}.")
    if log.daily_stress not in STRESS_LEVELS:
        errors.append(f"daily_stress must be one of {STRESS_LEVELS}.")
    if log.daily_sleep not in SLEEP_OPTIONS:
        errors.append(f"daily_sleep must be one of {SLEEP_OPTIONS}.")
    invalid = set(log.symptoms) - VALID_SYMPTOMS
    if invalid:
        errors.append(f"Invalid symptoms: {invalid}")
    if log.discharge not in VALID_DISCHARGES:
        errors.append(f"discharge must be one of {VALID_DISCHARGES}.")
    return errors


# ─────────────────────────────────────────
# 3. FEATURE ENGINEERING
# ─────────────────────────────────────────

def compute_actual_cycle_length(logs: list[DailyLog]) -> Optional[int]:
    period_starts = []
    in_period = False
    for log in sorted(logs, key=lambda l: l.log_date):
        if log.period_status == "on_period" and not in_period:
            period_starts.append(log.log_date)
            in_period = True
        elif log.period_status == "not_on_period":
            in_period = False
    if len(period_starts) >= 2:
        return (period_starts[-1] - period_starts[-2]).days
    return None


def get_last_period_start(logs: list[DailyLog]) -> Optional[date]:
    last_start = None
    in_period = False
    for log in sorted(logs, key=lambda l: l.log_date):
        if log.period_status == "on_period" and not in_period:
            last_start = log.log_date
            in_period = True
        elif log.period_status == "not_on_period":
            in_period = False
    return last_start


def get_current_cycle_phase(profile: UserProfile, logs: list[DailyLog],
                             today: date, effective_cycle: int) -> str:
    last_start = get_last_period_start(logs)
    if not last_start:
        return "unknown"
    period_dur = duration_to_days(profile.period_duration)
    days_since = (today - last_start).days % effective_cycle
    if days_since < period_dur:
        return "menstrual"
    elif days_since < 13:
        return "follicular"
    elif days_since in range(13, 16):
        return "ovulation"
    else:
        return "luteal"


def symptom_frequency(logs: list[DailyLog], symptom: str, within_days: int = 7) -> float:
    recent = sorted(logs, key=lambda l: l.log_date)[-within_days:]
    if not recent:
        return 0.0
    return sum(1 for l in recent if symptom in l.symptoms) / len(recent)


# ─────────────────────────────────────────
# 4. RULE ENGINE
# ─────────────────────────────────────────

class RuleEngine:
    def __init__(self, profile: UserProfile, logs: list[DailyLog], today: date):
        self.profile         = profile
        self.logs            = sorted(logs, key=lambda l: l.log_date)
        self.today           = today
        self.recent          = self.logs[-7:] if self.logs else []
        self.latest          = self.logs[-1] if self.logs else None
        self.actual_cycle    = compute_actual_cycle_length(self.logs)
        self.effective_cycle = self.actual_cycle or 28
        self._sf = {s: symptom_frequency(self.logs, s) for s in VALID_SYMPTOMS}

    def _freq(self, symptom: str) -> float:
        return self._sf.get(symptom, 0.0)

    # ── Cycle rules ───────────────────────────────────────────────

    def rule_cycle_irregular_short(self):
        t = self.actual_cycle is not None and self.actual_cycle < 21
        return t, "Short Cycle (<21 days)", 15, \
            "Your cycle appears shorter than normal. Track for 3+ cycles and consult a gynaecologist."

    def rule_cycle_irregular_long(self):
        t = self.actual_cycle is not None and self.actual_cycle > 35
        return t, "Long Cycle (>35 days)", 15, \
            "Your cycle appears longer than normal. Track for 3+ cycles and consult a gynaecologist."

    def rule_cycle_irregular_profile(self):
        t = self.profile.cycle_regularity == "irregular"
        return t, "Self-Reported Irregular Cycle", 10, \
            "Irregular cycles can be caused by stress, PCOS, or thyroid issues. Consider a gynaecology review."

    # ── Period characteristics ────────────────────────────────────

    def rule_heavy_bleeding(self):
        heavy = [l for l in self.recent
                 if l.period_status == "on_period"
                 and l.flow_intensity in ("high", "very_high")]
        t = len(heavy) >= 2
        return t, "Heavy Bleeding (2+ days)", 10, \
            "Heavy periods may indicate fibroids, endometriosis, or hormonal imbalance. Seek evaluation."

    def rule_prolonged_period(self):
        days = [l for l in self.recent if l.period_status == "on_period"]
        t = len(days) > 7
        return t, "Prolonged Period (>7 days)", 12, \
            "Periods lasting more than 7 days may indicate a hormonal or structural issue."

    # ── Pain rules ────────────────────────────────────────────────

    def rule_severe_cramps(self):
        t = self._freq("Cramps") >= 0.5
        return t, "Frequent Cramps", 10, \
            "Recurring severe cramps may suggest endometriosis or dysmenorrhea. Seek gynaecological evaluation."

    def rule_chronic_back_pain(self):
        t = self._freq("Back Pain") >= 0.5
        return t, "Chronic Back Pain", 8, \
            "Persistent back pain may be related to your menstrual cycle."

    def rule_chronic_vaginal_pain(self):
        t = self._freq("Vaginal Pain") >= 0.4
        return t, "Chronic Vaginal Pain", 12, \
            "Persistent vaginal pain may indicate endometriosis, cysts, or pelvic inflammatory disease."

    def rule_recurrent_headaches(self):
        t = self._freq("Headache") >= 0.5
        return t, "Recurrent Headaches", 5, \
            "Frequent headaches around your cycle may be hormonal migraines."

    # ── PCOS ──────────────────────────────────────────────────────

    def rule_pcos_risk(self):
        c = 0
        if self.profile.cycle_regularity == "irregular" or \
           (self.actual_cycle and self.actual_cycle > 35):
            c += 1
        if self._freq("Acne") >= 0.4:
            c += 1
        if self._freq("Fatigue") >= 0.5:
            c += 1
        if any("Nipple Discharge" in l.symptoms for l in self.recent):
            c += 1
        t = c >= 2
        return t, "Possible PCOS", 15, \
            "Signs of PCOS detected. Consult a gynaecologist for a hormone panel and ultrasound."

    def rule_pcos_known_worsening(self):
        known = any("PCOS" in d for d in self.profile.past_diagnosis)
        worse = self._freq("Acne") >= 0.4 or self.profile.cycle_regularity == "irregular"
        t = known and worse
        return t, "PCOS Symptom Worsening", 10, \
            "Your PCOS symptoms appear to be worsening. Review your management plan with your doctor."

    # ── Thyroid ───────────────────────────────────────────────────

    def rule_thyroid_risk(self):
        c = 0
        if self.profile.cycle_regularity == "irregular": c += 1
        if self._freq("Fatigue") >= 0.5:                c += 1
        if self._freq("Insomnia") >= 0.4:               c += 1
        if self._freq("Dizziness") >= 0.3:              c += 1
        t = c >= 3
        return t, "Possible Thyroid Dysfunction", 12, \
            "Fatigue, sleep issues, and irregular cycles may indicate a thyroid issue. Request a thyroid panel."

    # ── Infection ─────────────────────────────────────────────────

    def rule_yeast_infection(self):
        if not self.latest:
            return False, "", 0, ""
        t = ("Vaginal Itching" in self.latest.symptoms and
             self.latest.discharge in ("Thick Discharge", "Unusual Texture"))
        return t, "Possible Yeast Infection", 10, \
            "Thick discharge with itching suggests a yeast infection. Consult a doctor for antifungal treatment."

    def rule_bacterial_vaginosis(self):
        if not self.latest:
            return False, "", 0, ""
        t = (self.latest.discharge in ("Grayish", "Watery") and
             "Odour" in self.latest.symptoms)
        return t, "Possible Bacterial Vaginosis", 10, \
            "Grayish or watery discharge with odour may indicate bacterial vaginosis. Consult a doctor."

    def rule_uti(self):
        if not self.latest:
            return False, "", 0, ""
        t = ("Frequent Urination" in self.latest.symptoms and
             "Vaginal Pain" in self.latest.symptoms)
        return t, "Possible UTI", 12, \
            "Frequent urination with pain may indicate a UTI. Stay hydrated and seek medical treatment promptly."

    def rule_std_risk(self):
        if not self.latest:
            return False, "", 0, ""
        t = (self.latest.discharge == "Yellow or Green" and
             "Odour" in self.latest.symptoms and
             "Vaginal Pain" in self.latest.symptoms)
        return t, "Possible STI / PID", 20, \
            "Yellow or green discharge with odour and pain may indicate an STI or PID. Seek urgent medical evaluation."

    # ── PMS ───────────────────────────────────────────────────────

    def rule_severe_pms(self):
        pms = {"Bloating", "Fatigue", "Craving", "Breast Tenderness", "Insomnia"}
        count = sum(1 for s in pms if self._freq(s) >= 0.4)
        t = count >= 3
        return t, "Severe PMS / Possible PMDD", 8, \
            "Multiple recurring PMS symptoms may indicate PMDD. Lifestyle changes and medical support can help."

    # ── Lifestyle ─────────────────────────────────────────────────

    def rule_high_stress_impact(self):
        high_stress_days = sum(1 for l in self.recent if l.daily_stress == "high")
        t = (high_stress_days >= 4 and
             (self.profile.cycle_regularity == "irregular" or
              (self.actual_cycle and self.actual_cycle > 35)))
        return t, "Stress-Related Cycle Disruption", 5, \
            "High stress is a known cause of irregular cycles. Consider stress management techniques."

    def rule_poor_sleep_impact(self):
        poor = sum(1 for l in self.recent if l.daily_sleep in ("4-5h", "5-6h"))
        t = poor >= 4 and self._freq("Fatigue") >= 0.5
        return t, "Sleep Deprivation Affecting Cycle", 5, \
            "Poor sleep disrupts hormones. Aim for 7-9 hours per night."

    # ── Endometriosis ─────────────────────────────────────────────

    def rule_endometriosis_risk(self):
        c = 0
        if self._freq("Vaginal Pain") >= 0.4:  c += 1
        heavy = [l for l in self.recent
                 if l.period_status == "on_period"
                 and l.flow_intensity in ("high", "very_high")]
        if len(heavy) >= 3:                    c += 1
        if self._freq("Cramps") >= 0.5:        c += 1
        if self._freq("Back Pain") >= 0.4:     c += 1
        t = c >= 3
        return t, "Possible Endometriosis", 15, \
            "Chronic pelvic pain, heavy periods, and severe cramps may indicate endometriosis. Early diagnosis is important."

    # ── Evaluate all ──────────────────────────────────────────────

    def evaluate_all(self) -> tuple[list[str], list[str], int, list[str]]:
        rules = [
            self.rule_cycle_irregular_short,
            self.rule_cycle_irregular_long,
            self.rule_cycle_irregular_profile,
            self.rule_heavy_bleeding,
            self.rule_prolonged_period,
            self.rule_severe_cramps,
            self.rule_chronic_back_pain,
            self.rule_chronic_vaginal_pain,
            self.rule_recurrent_headaches,
            self.rule_pcos_risk,
            self.rule_pcos_known_worsening,
            self.rule_thyroid_risk,
            self.rule_yeast_infection,
            self.rule_bacterial_vaginosis,
            self.rule_uti,
            self.rule_std_risk,
            self.rule_severe_pms,
            self.rule_high_stress_impact,
            self.rule_poor_sleep_impact,
            self.rule_endometriosis_risk,
        ]

        risks, recommendations, total_deduction, flags = [], [], 0, []
        for fn in rules:
            triggered, label, deduction, recommendation = fn()
            if triggered:
                risks.append(label)
                if recommendation:
                    recommendations.append(recommendation)
                total_deduction += deduction
                flags.append(fn.__name__)

        seen = set()
        unique_recs = [r for r in recommendations if not (r in seen or seen.add(r))]
        return risks, unique_recs, total_deduction, flags


# ─────────────────────────────────────────
# 5. SCORING ENGINE
# ─────────────────────────────────────────

def compute_health_score(total_deduction: int, profile: UserProfile,
                         logs: list[DailyLog]) -> int:
    score = 100 - total_deduction

    if profile.lifestyle == "highly_active":  score += 3
    elif profile.lifestyle == "sedentary":    score -= 5

    avg_sleep = sleep_to_hours(profile.sleep_hours)
    if avg_sleep >= 7:   score += 2
    elif avg_sleep <= 5: score -= 5

    stress = stress_to_int(profile.stress_level)
    if stress == 2:   score -= 5
    elif stress == 0: score += 2

    if logs:
        recent = logs[-7:]
        avg_daily_stress = sum(stress_to_int(l.daily_stress) for l in recent) / len(recent)
        if avg_daily_stress >= 1.5:
            score -= 3

    return max(0, min(100, score))


# ─────────────────────────────────────────
# 6. CYCLE HEALTH LABEL
# ─────────────────────────────────────────

def cycle_health_label(score: int, risks: list[str]) -> str:
    if any("STI" in r or "Endometriosis" in r or "PID" in r for r in risks):
        return "Critical - Urgent Evaluation Needed"
    if score >= 85:   return "Healthy"
    elif score >= 70: return "Mild Irregularities"
    elif score >= 50: return "Moderate Concerns"
    else:             return "Significant Concerns - Consult a Doctor"


# ─────────────────────────────────────────
# 7. PREDICTION ENGINE
# ─────────────────────────────────────────

def predict_next_period(logs: list[DailyLog], effective_cycle: int) -> Optional[date]:
    last_start = get_last_period_start(logs)
    if not last_start:
        return None
    return last_start + timedelta(days=effective_cycle)


# ─────────────────────────────────────────
# 8. MAIN ANALYSER
# ─────────────────────────────────────────

def analyse(profile: UserProfile, logs: list[DailyLog],
            today: Optional[date] = None) -> HealthInsight:
    today = today or date.today()

    profile_errors = validate_profile(profile)
    if profile_errors:
        raise ValidationError("Profile errors: " + "; ".join(profile_errors))
    for log in logs:
        log_errors = validate_log(log)
        if log_errors:
            raise ValidationError(f"Log {log.log_date} errors: " + "; ".join(log_errors))

    engine         = RuleEngine(profile, logs, today)
    phase          = get_current_cycle_phase(profile, logs, today, engine.effective_cycle)
    predicted_next = predict_next_period(logs, engine.effective_cycle)

    risks, recommendations, total_deduction, flags = engine.evaluate_all()
    score = compute_health_score(total_deduction, profile, logs)
    label = cycle_health_label(score, risks)

    if not recommendations:
        recommendations.append(
            "Your cycle looks healthy. Keep logging daily for better insights."
        )

    return HealthInsight(
        cycle_health=label,
        health_score=score,
        risks=risks,
        recommendations=recommendations,
        predicted_next_period=predicted_next,
        cycle_phase=phase,
        flags=flags,
    )


def insight_to_dict(insight: HealthInsight) -> dict:
    return {
        "cycle_health":          insight.cycle_health,
        "health_score":          insight.health_score,
        "risks":                 insight.risks,
        "recommendations":       insight.recommendations,
        "predicted_next_period": insight.predicted_next_period.isoformat()
                                 if insight.predicted_next_period else None,
        "cycle_phase":           insight.cycle_phase,
        "flags":                 insight.flags,
    }