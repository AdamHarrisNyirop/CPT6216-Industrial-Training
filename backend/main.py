import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, Submission, SubmissionStatus, init_db
from schemas import SubmissionResponse, FixedCodeResponse
from worker import run_static_analysis, fix_python_code

app = FastAPI(title="Code Quality & Security Linter API")
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/linter_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/submissions", response_model=SubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_code(
    student_id: str = Form(...),
    assignment_id: str = Form(...),
    language: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
    ):
    submission_id = str(uuid.uuid4())
    sub_folder = os.path.join(UPLOAD_DIR, submission_id)
    os.makedirs(sub_folder, exist_ok=True)
    
    file_path = os.path.join(sub_folder, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    submission = Submission(
        id=submission_id,
        student_id=student_id,
        assignment_id=assignment_id,
        filename=file.filename,
        language=language,
        status=SubmissionStatus.PENDING
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Queue background static analysis task
    run_static_analysis.delay(submission_id, file_path, language)

    return submission

@app.post("/api/fix-python", response_model=FixedCodeResponse)
async def fix_python_endpoint(
    file: UploadFile = File(default=None),
    code: str = Form(default=""),
):
    if file is not None:
        filename = file.filename or "uploaded.py"
        raw_code = await file.read()
        try:
            source_code = raw_code.decode("utf-8")
        except UnicodeDecodeError:
            source_code = raw_code.decode("utf-8", errors="replace")
    else:
        filename = "python_code.py"
        source_code = code

    if not source_code.strip():
        raise HTTPException(status_code=400, detail="No Python code was provided to fix.")

    try:
        fixed_code = fix_python_code(source_code)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "filename": filename,
        "original_code": source_code,
        "fixed_code": fixed_code,
        "changed": fixed_code != source_code,
    }

@app.get("/api/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission_report(submission_id: str, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission