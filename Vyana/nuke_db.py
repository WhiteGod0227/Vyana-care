from sqlalchemy import text
from app.database import engine

def drop_all_tables():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Get all table names in the public schema
            result = conn.execute(text("""
                SELECT tablename FROM pg_catalog.pg_tables 
                WHERE schemaname = 'public';
            """))
            tables = [row[0] for row in result]
            
            if not tables:
                print("No tables found to drop.")
                return

            print(f"Dropping tables: {', '.join(tables)}")
            # Perform DROP TABLE CASCADE for each table
            for table in tables:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            
            trans.commit()
            print("✓ All tables dropped successfully with CASCADE.")
        except Exception as e:
            trans.rollback()
            print(f"Error dropping tables: {e}")

if __name__ == "__main__":
    drop_all_tables()
