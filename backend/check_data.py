import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from app.models import IPCBNSMapping, Statute

load_dotenv()

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    print("Checking IPCBNSMapping count...")
    count = session.query(IPCBNSMapping).count()
    print(f"Total mappings: {count}")
    
    if count > 0:
        first = session.query(IPCBNSMapping).first()
        print(f"First mapping ID: {first.id}")
        print(f"IPC ID: {first.ipc_section_id}")
        print(f"BNS ID: {first.bns_section_id}")
        
    print("Checking Statute count...")
    statute_count = session.query(Statute).count()
    print(f"Total statutes: {statute_count}")

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
