from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql://postgres1:8DtsAln9YgFcDpTHVCsJMoPfy4MufOF7@dpg-d7j29iflk1mc73a87odg-a.oregon-postgres.render.com:5432/expense_tracker_list"

engine = create_engine(
    DATABASE_URL
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
