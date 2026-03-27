"""
Tests for Aarogyini Period Tracker Rule Engine.
Covers healthy cycle, PCOS risk, UTI, yeast infection, thyroid, and endometriosis.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, timedelta
from period_tracker import (
    UserProfile, DailyLog, analyse, ValidationError,
    compute_actual_cycle_length, get_current_cycle_phase
)


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def make_profile(**overrides) -> UserProfile:
    defaults = dict(
        age=28, weight=62.0, height=165.0,
        lifestyle="moderate", stress_level=1, sleep_hours=7,
        last_period_start=date(2024, 3, 1),
        avg_cycle_length=28, period_duration=5,
        cycle_regularity="regular", past_diagnosis=[]
    )
    defaults.update(overrides)
    return UserProfile(**defaults)


def make_log(log_date: date, **overrides) -> DailyLog:
    return DailyLog(log_date=log_date, **overrides)


def period_logs(start: date, duration: int) -> list[DailyLog]:
    return [
        make_log(start + timedelta(days=i), period_day=True, flow_intensity=2)
        for i in range(duration)
    ]


# ─────────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────────

def test_healthy_cycle():
    print("\n[TEST] Healthy 28-day cycle")
    profile = make_profile()
    logs = period_logs(date(2024, 3, 1), 5)
    today = date(2024, 3, 15)
    insight = analyse(profile, logs, today)
    assert insight.health_score >= 80, f"Expected high score, got {insight.health_score}"
    assert "Possible PCOS" not in insight.risks
    assert "Possible UTI" not in insight.risks
    print(f"  Score: {insight.health_score} | Phase: {insight.cycle_phase} | Risks: {insight.risks}")
    print("  PASSED ✓")


def test_irregular_long_cycle():
    print("\n[TEST] Irregular long cycle (42 days)")
    profile = make_profile(avg_cycle_length=42, cycle_regularity="irregular")
    logs = period_logs(date(2024, 1, 1), 5) + period_logs(date(2024, 2, 11), 5)
    today = date(2024, 3, 1)
    insight = analyse(profile, logs, today)
    assert any("Long Cycle" in r or "Irregular" in r for r in insight.risks), f"Risks: {insight.risks}"
    print(f"  Score: {insight.health_score} | Risks: {insight.risks}")
    print("  PASSED ✓")


def test_pcos_risk():
    print("\n[TEST] PCOS Risk detection")
    profile = make_profile(avg_cycle_length=40, cycle_regularity="irregular")
    base_date = date(2024, 3, 10)
    logs = [
        make_log(base_date + timedelta(days=i),
                 acne=3, hair_growth=2, weight_change=1)
        for i in range(7)
    ]
    insight = analyse(profile, logs, base_date + timedelta(days=7))
    assert "Possible PCOS" in insight.risks, f"Expected PCOS risk, got: {insight.risks}"
    print(f"  Score: {insight.health_score} | Risks: {insight.risks}")
    print("  PASSED ✓")


def test_uti_detection():
    print("\n[TEST] UTI detection")
    profile = make_profile()
    today = date(2024, 3, 20)
    logs = [
        make_log(today, burning_urination=3, frequent_urination=True)
    ]
    insight = analyse(profile, logs, today)
    assert "Possible UTI" in insight.risks, f"Expected UTI, got: {insight.risks}"
    assert any("UTI" in r for r in insight.recommendations)
    print(f"  Score: {insight.health_score} | Risks: {insight.risks}")
    print("  PASSED ✓")


def test_yeast_infection():
    print("\n[TEST] Yeast Infection detection")
    profile = make_profile()
    today = date(2024, 3, 20)
    logs = [
        make_log(today, itching=3, discharge_type="thick", discharge_color="white")
    ]
    insight = analyse(profile, logs, today)
    assert "Possible Yeast Infection" in insight.risks, f"Risks: {insight.risks}"
    print(f"  Score: {insight.health_score} | Risks: {insight.risks}")
    print("  PASSED ✓")


def test_bacterial_vaginosis():
    print("\n[TEST] BV detection")
    profile = make_profile()
    today = date(2024, 3, 20)
    logs = [
        make_log(today, discharge_type="watery", discharge_color="yellow", odor="strong")
    ]
    insight = analyse(profile, logs, today)
    assert "Possible Bacterial Vaginosis" in insight.risks, f"Risks: {insight.risks}"
    print(f"  Score: {insight.health_score} | Risks: {insight.risks}")
    print("  PASSED ✓")


def test_std_risk():
    print("\n[TEST] STI / PID risk")
    profile = make_profile()
    today = date(2024, 3, 20)
    logs = [
        make_log(today, discharge_color="green", odor="strong", pelvic_pain_non_period=3)
    ]
    insight = analyse(profile, logs, today)
    assert "Possible STI / PID" in insight.risks, f"Risks: {insight.risks}"
    print(f"  Score: {insight.health_score} | Risks: {insight.risks}")
    print("  PASSED ✓")


def test_thyroid_risk():
    print("\n[TEST] Thyroid dysfunction risk")
    profile = make_profile(avg_cycle_length=42, cycle_regularity="irregular")
    base = date(2024, 3, 1)
    logs = [
        make_log(base + timedelta(days=i), hair_loss=3, fatigue=3, weight_change=1)
        for i in range(7)
    ]
    insight = analyse(profile, logs, base + timedelta(days=7))
    assert "Possible Thyroid Dysfunction" in insight.risks, f"Risks: {insight.risks}"
    print(f"  Score: {insight.health_score} | Risks: {insight.risks}")
    print("  PASSED ✓")


def test_endometriosis_risk():
    print("\n[TEST] Endometriosis risk")
    profile = make_profile()
    base = date(2024, 3, 1)
    logs = (
        [make_log(base + timedelta(days=i), period_day=True, flow_intensity=3, clotting=True, cramps=3)
         for i in range(5)]
        +
        [make_log(base + timedelta(days=i+5), pelvic_pain_non_period=3, cramps=2)
         for i in range(5)]
    )
    insight = analyse(profile, logs, base + timedelta(days=10))
    assert "Possible Endometriosis" in insight.risks, f"Risks: {insight.risks}"
    print(f"  Score: {insight.health_score} | Risks: {insight.risks}")
    print("  PASSED ✓")


def test_next_period_prediction():
    print("\n[TEST] Next period prediction")
    profile = make_profile(last_period_start=date(2024, 3, 1), avg_cycle_length=28)
    logs = period_logs(date(2024, 3, 1), 5)
    insight = analyse(profile, logs, date(2024, 3, 15))
    expected = date(2024, 3, 29)
    assert insight.predicted_next_period == expected, \
        f"Expected {expected}, got {insight.predicted_next_period}"
    print(f"  Predicted next period: {insight.predicted_next_period}")
    print("  PASSED ✓")


def test_cycle_phase_detection():
    print("\n[TEST] Cycle phase detection")
    profile = make_profile(last_period_start=date(2024, 3, 1))
    assert get_current_cycle_phase(profile, date(2024, 3, 3)) == "menstrual"
    assert get_current_cycle_phase(profile, date(2024, 3, 10)) == "follicular"
    assert get_current_cycle_phase(profile, date(2024, 3, 15)) == "ovulation"
    assert get_current_cycle_phase(profile, date(2024, 3, 22)) == "luteal"
    print("  All phases correct.")
    print("  PASSED ✓")


def test_validation_rejects_bad_score():
    print("\n[TEST] Validation rejects out-of-range scores")
    profile = make_profile()
    log = DailyLog(log_date=date(2024, 3, 1), cramps=5)  # 5 is invalid
    try:
        analyse(profile, [log])
        assert False, "Should have raised ValidationError"
    except ValidationError:
        print("  ValidationError raised as expected.")
        print("  PASSED ✓")


def test_known_pcos_worsening():
    print("\n[TEST] Known PCOS worsening")
    profile = make_profile(past_diagnosis=["PCOS"])
    base = date(2024, 3, 10)
    logs = [
        make_log(base + timedelta(days=i), acne=3, hair_growth=3)
        for i in range(7)
    ]
    insight = analyse(profile, logs, base + timedelta(days=7))
    assert "PCOS Symptom Worsening" in insight.risks, f"Risks: {insight.risks}"
    print(f"  Risks: {insight.risks}")
    print("  PASSED ✓")


# ─────────────────────────────────────────
# RUN ALL
# ─────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_healthy_cycle,
        test_irregular_long_cycle,
        test_pcos_risk,
        test_uti_detection,
        test_yeast_infection,
        test_bacterial_vaginosis,
        test_std_risk,
        test_thyroid_risk,
        test_endometriosis_risk,
        test_next_period_prediction,
        test_cycle_phase_detection,
        test_validation_rejects_bad_score,
        test_known_pcos_worsening,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  FAILED ✗ — {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests.")
    print('='*40)