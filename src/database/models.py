"""
データベースモデル定義
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class Interview(Base):
    """面接練習セッション"""
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    duration = Column(Float)  # 録音時間（秒）
    status = Column(String, default="uploaded")  # uploaded, processing, completed, failed
    
    # 文字起こし結果
    transcription = Column(Text)
    
    # 補正結果
    corrected_text = Column(Text)
    
    # 音声分析結果
    teacher_pitch_mean = Column(Float)
    teacher_volume_mean = Column(Float)
    teacher_speaking_rate = Column(Float)
    
    student_pitch_mean = Column(Float)
    student_volume_mean = Column(Float)
    student_speaking_rate = Column(Float)
    
    # レポートファイルパス
    report_path = Column(String)
    
    # エラーメッセージ
    error_message = Column(Text)


# データベース接続設定
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/interviews.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """データベース初期化"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """データベースセッション取得"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
