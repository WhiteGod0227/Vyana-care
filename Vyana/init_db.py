from app.database import SessionLocal, engine
from app.models import Base, AshaWorker

# Create tables
Base.metadata.create_all(bind=engine)

# Create session
db = SessionLocal()

try:
    # Check if ASHA worker with ID 1 exists
    asha = db.query(AshaWorker).filter(AshaWorker.id == 1).first()
    
    if not asha:
        print("Creating default ASHA worker...")
        asha = AshaWorker(
            id=1,
            name="Default ASHA Worker",
            phone="9000000001",
            area_pincode="345001",
            is_active=True
        )
        db.add(asha)
        db.commit()
        print("✓ Default ASHA worker created with ID 1")
    else:
        print("✓ ASHA worker with ID 1 already exists")
finally:
    db.close()
