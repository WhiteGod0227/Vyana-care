from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv("POSTGRES_URL"))

with engine.connect() as conn:
    asha = conn.execute(text("select count(*) from asha_workers")).scalar()
    patients = conn.execute(text("select count(*) from patients")).scalar()
    symptoms = conn.execute(text("select count(*) from symptoms")).scalar()
    savitri = conn.execute(text("select count(*) from patients where name='Savitri Devi' ")).scalar()
    savitri_high = conn.execute(
        text(
            """
            select count(*)
            from symptoms s
            join patients p on s.patient_id = p.id
            where p.name = 'Savitri Devi'
              and s.risk_level = 'HIGH'
              and s.symptoms_list @> '[\"swelling\", \"blurred_vision\", \"headache\"]'::jsonb
            """
        )
    ).scalar()

print(
    {
        "asha_workers": asha,
        "patients": patients,
        "symptoms": symptoms,
        "savitri_exists": savitri,
        "savitri_high_record": savitri_high,
    }
)
