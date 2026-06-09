import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from app.models import IPCBNSMapping
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    print("Measuring query performance...")
    start_time = time.time()
    
    query = session.query(IPCBNSMapping).options(
        joinedload(IPCBNSMapping.ipc_section),
        joinedload(IPCBNSMapping.bns_section)
    )
    results = query.all()
    
    end_time = time.time()
    print(f"Query took {end_time - start_time:.4f} seconds")
    print(f"Fetched {len(results)} rows")
    
    # Measure serialization time roughly
    import json
    start_json = time.time()
    data = []
    for m in results:
        data.append({
            "id": m.id,
            "ipc": m.ipc_section.section_number if m.ipc_section else None
        })
    json.dumps(data)
    end_json = time.time()
    print(f"Serialization/Processing took {end_json - start_json:.4f} seconds")

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
