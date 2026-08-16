from sqlalchemy import Column, Integer, String
from database import Base

# DB의 students 테이블 구조 정의
class StudentModel(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    grade = Column(String)
    attendance = Column(String, default="출석")
