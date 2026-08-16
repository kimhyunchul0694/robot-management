from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. SQLite 데이터베이스 파일 경로 설정 (project 폴더 내 students.db 생성)
SQLALCHEMY_DATABASE_URL = "sqlite:///./students.db"

# 2. DB 엔진 생성 (SQLite 연결 설정)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. DB 세션 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. DB 모델 작성을 위한 기본 클래스
Base = declarative_base()

# DB 세션 획득을 위한 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
