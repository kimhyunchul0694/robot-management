import os
import requests
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import engine, get_db

# 1. DB 테이블 생성
models.Base.metadata.create_all(bind=engine)

# 2. Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "test")

app = FastAPI(title="로봇 교실 관리 및 AI 일지 시스템")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StudentCreate(BaseModel):
    name: str
    grade: str


class StudentUpdate(BaseModel):
    name: str = None
    grade: str = None
    attendance: str = None


class DailyLogRequest(BaseModel):
    student_name: str
    today_topic: str
    performance: str


class NoticeRequest(BaseModel):
    student_name: str
    today_topic: str
    performance: str


# ==========================================
# [학생 관리 API]
# ==========================================

@app.get("/api/students")
def get_students(db: Session = Depends(get_db)):
    return db.query(models.StudentModel).all()


@app.post("/api/students")
def create_student(student_data: StudentCreate, db: Session = Depends(get_db)):
    db_student = models.StudentModel(
        name=student_data.name,
        grade=student_data.grade,
        attendance="출석"
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@app.put("/api/students/{student_id}")
def update_student(student_id: int, updated_data: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(models.StudentModel).filter(models.StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다.")

    if updated_data.name is not None:
        student.name = updated_data.name
    if updated_data.grade is not None:
        student.grade = updated_data.grade
    if updated_data.attendance is not None:
        student.attendance = updated_data.attendance

    db.commit()
    db.refresh(student)
    return student


@app.delete("/api/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentModel).filter(models.StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다.")

    db.delete(student)
    db.commit()
    return {"message": "성공적으로 삭제되었습니다."}


# ==========================================
# [AI 수업일지 자동 생성 API]
# ==========================================

@app.post("/api/generate-log")
def generate_daily_log(data: DailyLogRequest):
    prompt = f"""
    당신은 방과후 로봇 코딩 전문 교사입니다.
    아래 학생 정보를 바탕으로 학부모님이나 학교 관리자에게 제출할 수 있는 정중하고 전문적인 수업일지를 작성해 주세요.

    [학생 정보]
    - 학생 이름: {data.student_name}
    - 오늘 수업 주제: {data.today_topic}
    - 학생 수행 내용 및 특이사항: {data.performance}

    [작성 규칙]
    - 3줄 이내로 명확하고 긍정적인 어조로 작성해 주세요.
    - 수업 중 학생의 성취와 태도를 강조해 주세요.
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        res_data = res.json()

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Gemini API 응답 오류가 발생했습니다.")

        generated_text = res_data['candidates'][0]['content']['parts'][0]['text']
        return {"log": generated_text}

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# [AI 학부모 안내문 자동 생성 API]
# ==========================================

@app.post("/api/generate-notice")
def generate_parent_notice(data: NoticeRequest):
    prompt = f"""
    당신은 방과후 로봇 코딩 교실 지도교사입니다.
    학부모님께 전달할 알림장(카카오톡/문자메시지용)을 정중하고 친절하게 작성해 주세요.

    [학생 정보]
    - 학생 이름: {data.student_name}
    - 오늘 수업 주제: {data.today_topic}
    - 수업 수행 내용 및 특징: {data.performance}

    [작성 형태]
    - 정중한 인사말 및 마무리 인사 포함
    - 오늘 수업 주제 설명 및 학생의 칭찬/성장 포인트 강조
    - 가정에서의 따뜻한 격려 부탁 문구 포함
    - 전체 분량은 모바일로 읽기 좋은 4~5줄 내외
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        res_data = res.json()

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Gemini API 응답 오류가 발생했습니다.")

        generated_text = res_data['candidates'][0]['content']['parts'][0]['text']
        return {"notice": generated_text}

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# [정적 파일 연결]
# ==========================================

@app.get("/")
def read_index():
    return FileResponse("index.html")


app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/css", StaticFiles(directory="css"), name="css")
