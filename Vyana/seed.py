import random
from datetime import datetime, timedelta, timezone

from app.database import Base, SessionLocal, engine
from app.models import AshaWorker, Patient, Symptom
from app.services.risk_model import calculate_risk


ASHA_DATA = [
    {"name": "Kamla Devi", "phone": "9876543210", "area_pincode": "344001"},
    {"name": "Sunita Sharma", "phone": "9876543211", "area_pincode": "345001"},
    {"name": "Radha Bai", "phone": "9876543212", "area_pincode": "342001"},
]

PATIENT_DATA = [
    ("Savitri Devi", 29, "Ramgarh", "Barmer", 32, "9000010001", "Kamla Devi"),
    ("Meera Kumari", 24, "Balotra", "Barmer", 21, "9000010002", "Kamla Devi"),
    ("Gita Bai", 33, "Siwana", "Barmer", 34, "9000010003", "Kamla Devi"),
    ("Rukmini", 27, "Ramgarh", "Barmer", 18, "9000010004", "Kamla Devi"),
    ("Laxmi", 19, "Balotra", "Barmer", 29, "9000010005", "Kamla Devi"),
    ("Parvati", 36, "Siwana", "Barmer", 37, "9000010006", "Kamla Devi"),
    ("Shanti", 30, "Sam", "Jaisalmer", 26, "9000010007", "Sunita Sharma"),
    ("Bhanwari", 22, "Pokaran", "Jaisalmer", 14, "9000010008", "Sunita Sharma"),
    ("Durga", 28, "Fatehgarh", "Jaisalmer", 31, "9000010009", "Sunita Sharma"),
    ("Nirmala", 34, "Sam", "Jaisalmer", 35, "9000010010", "Sunita Sharma"),
    ("Pushpa", 25, "Pokaran", "Jaisalmer", 22, "9000010011", "Sunita Sharma"),
    ("Kamli", 17, "Fatehgarh", "Jaisalmer", 16, "9000010012", "Sunita Sharma"),
    ("Rekha", 31, "Osian", "Jodhpur", 28, "9000010013", "Radha Bai"),
    ("Suman", 23, "Bilara", "Jodhpur", 12, "9000010014", "Radha Bai"),
    ("Kesar", 38, "Phalodi", "Jodhpur", 39, "9000010015", "Radha Bai"),
    ("Anita", 26, "Osian", "Jodhpur", 24, "9000010016", "Radha Bai"),
    ("Manju", 21, "Bilara", "Jodhpur", 30, "9000010017", "Radha Bai"),
    ("Seema", 28, "Phalodi", "Jodhpur", 19, "9000010018", "Radha Bai"),
    ("Tara", 32, "Osian", "Jodhpur", 33, "9000010019", "Radha Bai"),
    ("Bhavna", 27, "Bilara", "Jodhpur", 27, "9000010020", "Radha Bai"),
]

SYMPTOM_POOL = [
    "headache",
    "swelling",
    "blurred_vision",
    "bleeding",
    "fever",
    "reduced_fetal_movement",
    "chest_pain",
    "difficulty_breathing",
    "abdominal_pain",
    "fatigue",
    "nausea",
    "dizziness",
]


Base.metadata.create_all(bind=engine)


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def run_seed():
    db = SessionLocal()
    try:
        db.query(Symptom).delete()
        db.query(Patient).delete()
        db.query(AshaWorker).delete()
        db.commit()

        asha_map = {}
        for a in ASHA_DATA:
            worker = AshaWorker(
                name=a["name"],
                phone=a["phone"],
                area_pincode=a["area_pincode"],
                is_active=True,
            )
            db.add(worker)
            db.flush()
            asha_map[worker.name] = worker.id

        patients = []
        for row in PATIENT_DATA:
            p = Patient(
                name=row[0],
                age=row[1],
                village=row[2],
                district=row[3],
                pregnancy_week=row[4],
                phone_number=row[5],
                asha_id=asha_map[row[6]],
            )
            db.add(p)
            db.flush()
            patients.append(p)

        savitri = next(p for p in patients if p.name == "Savitri Devi")
        mandatory_symptoms = ["swelling", "blurred_vision", "headache"]
        mandatory_risk = calculate_risk(
            symptoms=mandatory_symptoms,
            bp_systolic=150,
            bp_diastolic=98,
            age=savitri.age,
            pregnancy_week=savitri.pregnancy_week,
            days_since_last_checkup=17,
            previous_complications=False,
        )

        db.add(
            Symptom(
                patient_id=savitri.id,
                symptoms_list=mandatory_symptoms,
                input_type="text",
                transcription="Severe headache, swelling and blurred vision",
                risk_score=mandatory_risk["score"],
                risk_level=mandatory_risk["level"],
                primary_reason=mandatory_risk["primary_reason"],
                timestamp=utc_now_naive() - timedelta(hours=2),
            )
        )

        for i in range(49):
            patient = random.choice(patients)
            count = random.randint(0, 3)
            picked = random.sample(SYMPTOM_POOL, k=count) if count > 0 else []

            bp_sys = random.choice([118, 122, 130, 138, 145, 150])
            bp_dia = random.choice([76, 80, 86, 92, 96])
            days_since_last_checkup = random.randint(0, 21)
            previous_complications = random.choice([True, False, False])

            risk = calculate_risk(
                symptoms=picked,
                bp_systolic=bp_sys,
                bp_diastolic=bp_dia,
                age=patient.age,
                pregnancy_week=patient.pregnancy_week,
                days_since_last_checkup=days_since_last_checkup,
                previous_complications=previous_complications,
            )

            db.add(
                Symptom(
                    patient_id=patient.id,
                    symptoms_list=picked,
                    input_type=random.choice(["text", "voice"]),
                    transcription="" if random.random() > 0.5 else "Auto-seeded complaint",
                    risk_score=risk["score"],
                    risk_level=risk["level"],
                    primary_reason=risk["primary_reason"],
                    timestamp=utc_now_naive() - timedelta(hours=random.randint(1, 220)),
                )
            )

        db.commit()
        print("Seeding complete: 3 ASHA workers, 20 patients, 50 symptom records")
    except Exception as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
