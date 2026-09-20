from app.database import engine
from app.models import Base

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("✓ All tables dropped.")

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("✓ All tables created.")
