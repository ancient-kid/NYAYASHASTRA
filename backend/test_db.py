import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")
print(f"Connecting to: {database_url}")

try:
    engine = create_engine(database_url)
    with engine.connect() as connection:
        print("Connected!")
        result = connection.execute(text("SELECT 1"))
        print(f"Result: {result.fetchone()}")
        print("Done.")
except Exception as e:
    print(f"Error: {e}")
