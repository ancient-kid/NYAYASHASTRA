import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)

try:
    with engine.connect() as connection:
        print("Listing tables...")
        result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        for row in result:
            print(f"- {row[0]}")
            
        print("\nCounting ipc_bns_mappings raw SQL...")
        result = connection.execute(text("SELECT count(*) FROM ipc_bns_mappings"))
        print(f"Count: {result.fetchone()[0]}")

except Exception as e:
    print(f"Error: {e}")
