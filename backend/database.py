import enum
import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, Enum, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql://linter_user:linter_password@localhost:5432/linter_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String, primary_key=True, index=True) # UUID
    student_id = Column(String, nullable=False)
    assignment_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    language = Column(String, nullable=False)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING)
    quality_score = Column(Float, nullable=True)
    report_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)