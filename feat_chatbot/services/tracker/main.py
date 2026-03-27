"""
Aarogyini - Period Tracker Service
Runs on port 8002.

CHANGES FROM ORIGINAL:
  All Pydantic request schemas updated to match the new UI field design.
  ProfileRequest: stress/sleep/lifestyle/period_duration are now string enums.
  DailyLogRequest: symptoms is a list, discharge is a single string,
                   daily_stress and daily_sleep added,
                   all old integer symptom fields removed.
"""

import os
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List

from period_tracker import (
    UserProfile, DailyLog, analyse, insight_to_dict, ValidationError,
    STRESS_LEVELS, SLEEP_OPTIONS, LIFESTYLES, PERIOD_DURATIONS,
    FLOW_LEVELS, PERIOD_STATUSES, VALID_SYMPTOMS, VALID_DISCHARGES,
)
from storage import (
    save_profile, load_profile, save_log,
    load_all_logs, get_log_for_date, log_to_dict,
)

app = FastAPI(
    title="Aarogyini Period Tracker Service",
    description="Rule-based menstrual health engine",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Schemas ────────────────────────────────────────

class ProfileRequest(BaseModel):
    age:              int   = Field(..., ge=10, le=60, example=28)
    weight:           float = Field(..., example=62.0)
    height:           float = Field(..., example=165.0)
    lifestyle:        str   = Field(..., example="lightly_active",
                                   description="sedentary | lightly_active | highly_active")
    stress_level:     str   = Field(..., example="low",
                                   description="low | medium | high")
    sleep_hours:      str   = Field(..., example="7-8h",
                                   description="4-5h | 5-6h | 6-7h | 7-8h | 8h+")
    period_duration:  str   = Field(..., example="4-5d",
                                   description="3-4d | 4-5d | 5-6d | 6d+")
    cycle_regularity: str   = Field(..., example="regular",
                                   description="regular | irregular")
    past_diagnosis:   List[str] = Field(default_factory=list, example=[])


class DailyLogRequest(BaseModel):
    log_date:       date   = Field(..., example="2026-03-27")
    period_status:  str    = Field("not_on_period", example="not_on_period",
                                   description="on_period | not_on_period")
    flow_intensity: str    = Field("low", example="medium",
                                   description="low | medium | high | very_high")
    daily_stress:   str    = Field("low", example="medium",
                                   description="low | medium | high")
    daily_sleep:    str    = Field("7-8h", example="6-7h",
                                   description="4-5h | 5-6h | 6-7h | 7-8h | 8h+")
    symptoms:       List[str] = Field(
        default_factory=list,
        example=["Cramps", "Fatigue", "Bloating"],
        description=(
            "Any of: Bloating, Headache, Acne, Craving, Breast Tenderness, "
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


# ── Helpers ───────────────────────────────────────────────────────────

def _build_profile(r: ProfileRequest) -> UserProfile:
    return UserProfile(
        age=r.age, weight=r.weight, height=r.height,
        lifestyle=r.lifestyle, stress_level=r.stress_level,
        sleep_hours=r.sleep_hours, period_duration=r.period_duration,
        cycle_regularity=r.cycle_regularity, past_diagnosis=r.past_diagnosis,
    )


def _build_log(r: DailyLogRequest) -> DailyLog:
    return DailyLog(
        log_date=r.log_date,
        period_status=r.period_status,
        flow_intensity=r.flow_intensity,
        daily_stress=r.daily_stress,
        daily_sleep=r.daily_sleep,
        symptoms=r.symptoms,
        discharge=r.discharge,
    )


# ── Endpoints ─────────────────────────────────────────────────────────

@app.post("/profile", summary="Save or update user health profile")
def create_profile(body: ProfileRequest):
    save_profile(_build_profile(body))
    return {"message": "Profile saved successfully."}


@app.get("/profile", summary="Fetch current user profile")
def fetch_profile():
    profile = load_profile()
    if not profile:
        raise HTTPException(404, "Profile not found. Please complete onboarding.")
    return {
        "age":              profile.age,
        "weight":           profile.weight,
        "height":           profile.height,
        "lifestyle":        profile.lifestyle,
        "stress_level":     profile.stress_level,
        "sleep_hours":      profile.sleep_hours,
        "period_duration":  profile.period_duration,
        "cycle_regularity": profile.cycle_regularity,
        "past_diagnosis":   profile.past_diagnosis,
    }


@app.post("/log", summary="Submit a daily health log")
def submit_log(body: DailyLogRequest):
    if not load_profile():
        raise HTTPException(400, "Complete onboarding before logging.")
    save_log(_build_log(body))
    return {"message": f"Log for {body.log_date} saved."}


@app.get("/log/{log_date}", summary="Fetch log for a specific date")
def fetch_log(log_date: date):
    log = get_log_for_date(log_date)
    if not log:
        raise HTTPException(404, f"No log found for {log_date}.")
    return log_to_dict(log)


@app.get("/analyse", summary="Run rule engine and get health insights")
def run_analysis(today: Optional[date] = None):
    profile = load_profile()
    if not profile:
        raise HTTPException(400, "Complete onboarding first.")
    logs = load_all_logs()
    if not logs:
        raise HTTPException(400, "No logs found. Start logging daily.")
    try:
        return insight_to_dict(analyse(profile, logs, today))
    except ValidationError as e:
        raise HTTPException(422, str(e))


@app.get("/history", summary="Get all past daily log entries")
def get_history():
    return [log_to_dict(l) for l in load_all_logs()]


@app.get("/health", summary="Service liveness check")
def health_check():
    return {"service": "tracker", "status": "healthy"}