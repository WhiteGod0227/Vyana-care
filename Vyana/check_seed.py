from sqlalchemy import text
from app.database import engine

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
