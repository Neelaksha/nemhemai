from sqlalchemy import create_engine
import pandas as pd

# 🔁 Replace with your credentials
DB_USER = "postgres"
DB_PASSWORD = "password"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "analytics"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

def run_query(query):
    try:
        df = pd.read_sql(query, engine)
        return df, None
    except Exception as e:
        return None, str(e)