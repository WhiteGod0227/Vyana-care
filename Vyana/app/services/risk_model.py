from __future__ import annotations


def calculate_risk(
    symptoms: list[str],
    bp_systolic: int,
    bp_diastolic: int,
    age: int,
    pregnancy_week: int,
    days_since_last_checkup: int,
    previous_complications: bool,
) -> dict:
    symptom_set = set(symptoms)

    if {"blurred_vision", "swelling", "headache"}.issubset(symptom_set):
        result = {
            "score": 95,
            "level": "HIGH",
            "primary_reason": "Pre-eclampsia symptoms detected",
            "recommendation": "Turant doctor ke paas jayein. ASHA didi ko abhi call karein.",
        }
        print(f"[RISK] Score calculated: {result['score']} - {result['level']}")
        return result

    if "bleeding" in symptom_set:
        result = {
            "score": 90,
            "level": "HIGH",
            "primary_reason": "Active bleeding reported",
            "recommendation": "Turant doctor ke paas jayein. ASHA didi ko abhi call karein.",
        }
        print(f"[RISK] Score calculated: {result['score']} - {result['level']}")
        return result

    if {"difficulty_breathing", "chest_pain"}.issubset(symptom_set):
        result = {
            "score": 88,
            "level": "HIGH",
            "primary_reason": "Respiratory distress detected",
            "recommendation": "Turant doctor ke paas jayein. ASHA didi ko abhi call karein.",
        }
        print(f"[RISK] Score calculated: {result['score']} - {result['level']}")
        return result

    if "reduced_fetal_movement" in symptom_set:
        result = {
            "score": 85,
            "level": "HIGH",
            "primary_reason": "Reduced fetal movement reported",
            "recommendation": "Turant doctor ke paas jayein. ASHA didi ko abhi call karein.",
        }
        print(f"[RISK] Score calculated: {result['score']} - {result['level']}")
        return result

    score = 0
    weighted = {
        "headache": 10,
        "swelling": 12,
        "blurred_vision": 15,
        "fever": 10,
        "reduced_fetal_movement": 20,
        "chest_pain": 15,
        "abdominal_pain": 12,
        "dizziness": 8,
        "nausea": 6,
        "fatigue": 5,
    }

    max_weight = 0
    primary_reason = "No major risk indicators"
    for symptom, weight in weighted.items():
        if symptom in symptom_set:
            score += weight
            if weight > max_weight:
                max_weight = weight
                primary_reason = f"Primary symptom: {symptom}"

    if bp_systolic > 140:
        score += 20
        if 20 > max_weight:
            max_weight = 20
            primary_reason = "High systolic blood pressure"

    if bp_diastolic > 90:
        score += 15
        if 15 > max_weight:
            max_weight = 15
            primary_reason = "High diastolic blood pressure"

    if age < 18 or age > 35:
        score += 10
        if 10 > max_weight:
            primary_reason = "High-risk age group"

    if pregnancy_week > 36:
        score += 8

    if days_since_last_checkup > 14:
        score += 10

    if previous_complications:
        score += 10
        if 10 > max_weight:
            primary_reason = "Previous complications history"

    score = min(score, 100)

    if score <= 40:
        level = "LOW"
        recommendation = "Sab theek lag raha hai. Routine checkup time pe karein."
    elif score <= 70:
        level = "MEDIUM"
        recommendation = "Agle 24 ghante mein ASHA didi se milein. Aaram karein."
    else:
        level = "HIGH"
        recommendation = "Turant doctor ke paas jayein. ASHA didi ko abhi call karein."

    result = {
        "score": score,
        "level": level,
        "primary_reason": primary_reason,
        "recommendation": recommendation,
    }
    print(f"[RISK] Score calculated: {result['score']} - {result['level']}")
    return result
