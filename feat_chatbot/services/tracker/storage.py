"""
Aarogyini Period Tracker - Storage Layer

CHANGES FROM ORIGINAL:
  Serialisers updated to match new UserProfile and DailyLog fields.
  DATA_DIR still configurable via environment variable.
"""

import json
import os
from datetime import date
from pathlib import Path
from period_tracker import UserProfile, DailyLog

DATA_DIR     = Path(os.environ.get("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_FILE = DATA_DIR / "profile.json"
LOGS_FILE    = DATA_DIR / "logs.json"


# ── Serialisers ───────────────────────────────────────────────────────

def profile_to_dict(p: UserProfile) -> dict:
    return {
        "age":              p.age,
        "weight":           p.weight,
        "height":           p.height,
        "lifestyle":        p.lifestyle,
        "stress_level":     p.stress_level,
        "sleep_hours":      p.sleep_hours,
        "period_duration":  p.period_duration,
        "cycle_regularity": p.cycle_regularity,
        "past_diagnosis":   p.past_diagnosis,
    }


def profile_from_dict(d: dict) -> UserProfile:
    return UserProfile(
        age=d["age"],
        weight=d["weight"],
        height=d["height"],
        lifestyle=d["lifestyle"],
        stress_level=d["stress_level"],
        sleep_hours=d["sleep_hours"],
        period_duration=d["period_duration"],
        cycle_regularity=d["cycle_regularity"],
        past_diagnosis=d.get("past_diagnosis", []),
    )


def log_to_dict(l: DailyLog) -> dict:
    return {
        "log_date":       l.log_date.isoformat(),
        "period_status":  l.period_status,
        "flow_intensity": l.flow_intensity,
        "daily_stress":   l.daily_stress,
        "daily_sleep":    l.daily_sleep,
        "symptoms":       l.symptoms,
        "discharge":      l.discharge,
    }


def log_from_dict(d: dict) -> DailyLog:
    return DailyLog(
        log_date=date.fromisoformat(d["log_date"]),
        period_status=d.get("period_status", "not_on_period"),
        flow_intensity=d.get("flow_intensity", "low"),
        daily_stress=d.get("daily_stress", "low"),
        daily_sleep=d.get("daily_sleep", "7-8h"),
        symptoms=d.get("symptoms", []),
        discharge=d.get("discharge", "No Discharge"),
    )


# ── Storage operations ────────────────────────────────────────────────

def save_profile(profile: UserProfile):
    PROFILE_FILE.write_text(json.dumps(profile_to_dict(profile), indent=2))


def load_profile() -> UserProfile | None:
    if not PROFILE_FILE.exists():
        return None
    return profile_from_dict(json.loads(PROFILE_FILE.read_text()))


def load_all_logs() -> list[DailyLog]:
    if not LOGS_FILE.exists():
        return []
    return [log_from_dict(d) for d in json.loads(LOGS_FILE.read_text())]


def save_log(log: DailyLog):
    logs_dict = {l.log_date: l for l in load_all_logs()}
    logs_dict[log.log_date] = log
    LOGS_FILE.write_text(json.dumps(
        [log_to_dict(l) for l in sorted(logs_dict.values(), key=lambda x: x.log_date)],
        indent=2,
    ))


def get_log_for_date(target: date) -> DailyLog | None:
    return next((l for l in load_all_logs() if l.log_date == target), None)