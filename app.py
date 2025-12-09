"""
FastAPI メインアプリケーション
"""
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import Request
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

from src.database.models import init_db, get_db, Interview
from src.audio.transcriber import Transcriber
from src.audio.diarization import Diarizer
from src.audio.analyzer import AudioAnalyzer
from src.ai.corrector import TextCorrector
from src.report.generator import ReportGenerator

load_dotenv()

# アプリケーション初期化
app = FastAPI(title="面接練習レポート支援ツール")

# 静的ファイルとテンプレート
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# データベース初期化
init_db()

# 各種モジュール初期化（グローバル）
transcriber = None
diarizer = None
analyzer = AudioAnalyzer()
corrector = None
report_gen = ReportGenerator()

# アップロードフォルダ
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./data/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def init_modules():
    """モジュールの遅延初期化"""
    global transcriber, diarizer, corrector
    
    if transcriber is None:
        print("Initializing Whisper...")
        transcriber = Transcriber()
    
    if diarizer is None:
        print("Initializing pyannote.audio...")
        try:
            diarizer = Diarizer()
        except Exception as e:
            print(f"Warning: Diarizer initialization failed: {e}")
            diarizer = None
    
    if corrector is None:
        print("Initializing Ollama...")
        try:
            corrector = TextCorrector()
        except Exception as e:
            print(f"Warning: Corrector initialization failed: {e}")
            corrector = None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページ"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/upload")
async def upload_audio(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    音声ファイルアップロード
    """
    # ファイル名生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"interview_{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # ファイル保存
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # データベースに登録
    interview = Interview(
        filename=filename,
        status="uploaded"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    # バックグラウンドで処理開始
    background_tasks.add_task(process_interview, interview.id, filepath)
    
    return {
        "success": True,
        "interview_id": interview.id,
        "message": "ファイルをアップロードしました。分析を開始します..."
    }


async def process_interview(interview_id: int, filepath: str):
    """
    面接音声の処理（バックグラウンドタスク）
    """
    db = next(get_db())
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    
    try:
        # モジュール初期化
        init_modules()
        
        # ステータス更新
        interview.status = "processing"
        db.commit()
        
        # 1. 文字起こし
        print(f"[{interview_id}] Step 1: Transcription...")
        result = transcriber.transcribe(filepath)
        segments = transcriber.get_segments_with_timestamps(result)
        interview.duration = result.get("duration", 0)
        
        # 2. 話者分離
        print(f"[{interview_id}] Step 2: Diarization...")
        if diarizer:
            diar_segments = diarizer.diarize(filepath)
            segments = diarizer.assign_speakers_to_segments(segments, diar_segments)
            segments = diarizer.map_speakers_to_roles(segments)
        else:
            # 話者分離が利用できない場合はスキップ
            for seg in segments:
                seg["speaker"] = "不明"
        
        # 3. 日本語補正
        print(f"[{interview_id}] Step 3: Text correction...")
        if corrector:
            segments = corrector.analyze_segments(segments)
        
        # 文字起こし保存
        interview.transcription = transcriber.format_transcript(segments)
        
        # 4. 音声分析
        print(f"[{interview_id}] Step 4: Audio analysis...")
        audio_analysis = analyzer.analyze(filepath, segments)
        
        # 話者別評価
        for speaker in ["教師", "生徒"]:
            if speaker in audio_analysis["by_speaker"]:
                evaluation = analyzer.evaluate_interview_voice(audio_analysis, speaker)
                audio_analysis[f"{speaker}_evaluation"] = evaluation
                
                # データベースに保存
                if speaker == "教師":
                    interview.teacher_pitch_mean = audio_analysis["by_speaker"][speaker]["pitch_mean"]
                    interview.teacher_volume_mean = audio_analysis["by_speaker"][speaker]["volume_mean"]
                    interview.teacher_speaking_rate = audio_analysis["by_speaker"][speaker]["speaking_rate"]
                else:
                    interview.student_pitch_mean = audio_analysis["by_speaker"][speaker]["pitch_mean"]
                    interview.student_volume_mean = audio_analysis["by_speaker"][speaker]["volume_mean"]
                    interview.student_speaking_rate = audio_analysis["by_speaker"][speaker]["speaking_rate"]
        
        # 5. 敬語チェック（生徒のみ）
        print(f"[{interview_id}] Step 5: Keigo check...")
        keigo_eval = None
        if corrector:
            student_text = "\n".join([
                seg.get("corrected_text", seg.get("text", ""))
                for seg in segments
                if seg.get("speaker") == "生徒"
            ])
            if student_text.strip():
                keigo_eval = corrector.check_keigo(student_text)
        
        # 6. レポート生成
        print(f"[{interview_id}] Step 6: Report generation...")
        report_path = report_gen.generate_html_report(
            interview_id,
            interview.filename,
            segments,
            audio_analysis,
            keigo_eval
        )
        
        interview.report_path = report_path
        interview.status = "completed"
        db.commit()
        
        print(f"[{interview_id}] Processing completed!")
        
    except Exception as e:
        print(f"[{interview_id}] Error: {e}")
        interview.status = "failed"
        interview.error_message = str(e)
        db.commit()
    finally:
        db.close()


@app.get("/api/status/{interview_id}")
async def get_status(interview_id: int, db: Session = Depends(get_db)):
    """処理ステータス確認"""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return {
        "id": interview.id,
        "status": interview.status,
        "filename": interview.filename,
        "error_message": interview.error_message,
        "report_ready": interview.status == "completed"
    }


@app.get("/api/report/{interview_id}")
async def get_report(interview_id: int, db: Session = Depends(get_db)):
    """レポート取得"""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview.status != "completed":
        raise HTTPException(status_code=400, detail="Report not ready")
    
    if not interview.report_path or not os.path.exists(interview.report_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        interview.report_path,
        media_type="text/html",
        filename=f"report_{interview_id}.html"
    )


@app.get("/api/interviews")
async def list_interviews(db: Session = Depends(get_db)):
    """面接一覧取得"""
    interviews = db.query(Interview).order_by(Interview.created_at.desc()).limit(20).all()
    
    return [{
        "id": i.id,
        "filename": i.filename,
        "status": i.status,
        "created_at": i.created_at.isoformat(),
        "duration": i.duration
    } for i in interviews]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
