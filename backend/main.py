"""
面接練習システム - FastAPI サーバー

音声ファイルをアップロード → 分析 → Markdown レポート生成
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os
import asyncio
import json
from dotenv import load_dotenv

# 環境変数読み込み (backend/.env を優先)
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from backend.services.transcription import transcribe_audio
from backend.services.audio_analysis import analyze_audio_features
from backend.services.ai_analysis import analyze_with_gemini
from backend.services.report import generate_markdown_report
from backend.services.voice_emotion import analyze_voice_emotion, get_emotion_feedback
from backend.services.realtime_transcription import RealtimeTranscriber
from backend.services.video_analysis import analyze_video
from backend.services.realtime_analyzer import RealtimeAnalyzer
from backend.services.session_recorder import SessionRecorder
from backend.services.post_session_pipeline import run_post_session_pipeline

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI アプリ初期化
app = FastAPI(
    title="圧勝面接練習システム",
    description="音声分析 → AI 評価 → Markdown レポート生成",
    version="1.0.0"
)

# CORS 設定 (フロントエンドからのアクセスを許可)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite/React 開発サーバー
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 出力ディレクトリ設定
OUTPUT_DIR = Path("output")
AUDIO_DIR = OUTPUT_DIR / "audio"
REPORTS_DIR = OUTPUT_DIR / "reports"
VIDEO_DIR = OUTPUT_DIR / "videos"
SESSIONS_DIR = OUTPUT_DIR / "sessions"
STATIC_DIR = Path("backend/static")

# ディレクトリ作成
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# 静的ファイル配信
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")
app.mount("/videos", StaticFiles(directory=str(VIDEO_DIR)), name="videos")

# WebSocket 接続管理
active_connections: Dict[str, WebSocket] = {}


async def send_progress(session_id: str, stage: str, message: str, progress: int):
    """
    進捗状況を WebSocket で送信
    
    Args:
        session_id: セッション ID
        stage: 処理ステージ (transcription/audio_analysis/ai_analysis/report)
        message: メッセージ
        progress: 進捗率 (0-100)
    """
    if session_id in active_connections:
        try:
            await active_connections[session_id].send_json({
                "stage": stage,
                "message": message,
                "progress": progress,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"WebSocket 送信エラー: {e}")
            del active_connections[session_id]


@app.get("/", response_class=HTMLResponse)
async def index():
    """
    簡易アップロードフォーム
    """
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>圧勝面接練習システム</title>
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                margin-bottom: 30px;
            }
            .upload-area {
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
            }
            input[type="file"] {
                display: none;
            }
            .file-label {
                display: inline-block;
                padding: 12px 30px;
                background: #007bff;
                color: white;
                border-radius: 5px;
                cursor: pointer;
                transition: background 0.3s;
            }
            .file-label:hover {
                background: #0056b3;
            }
            button {
                width: 100%;
                padding: 15px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                margin-top: 20px;
            }
            button:hover {
                background: #218838;
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            #status {
                margin-top: 20px;
                padding: 15px;
                border-radius: 5px;
                display: none;
            }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            .info { background: #d1ecf1; color: #0c5460; }
            #fileName {
                margin-top: 10px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 圧勝面接練習システム</h1>
            <p>音声ファイルをアップロードして、AI が分析します。</p>
            
            <div style="margin: 20px 0; padding: 15px; background: #e3f2fd; border-radius: 8px; text-align: center;">
                <a href="/static/realtime.html" style="color: #1976d2; text-decoration: none; font-weight: bold; font-size: 1.1em;">
                    🎙️ リアルタイム面接練習を開始 →
                </a>
            </div>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-area">
                    <label for="audioFile" class="file-label">
                        📁 音声ファイルを選択
                    </label>
                    <input type="file" id="audioFile" name="file" accept=".mp3,.wav,.m4a" required>
                    <div id="fileName"></div>
                </div>
                
                <button type="submit" id="submitBtn">
                    🚀 分析開始
                </button>
            </form>
            
            <div id="progressContainer" style="display:none; margin-top: 20px;">
                <div style="margin-bottom: 10px;">
                    <strong id="currentStage">準備中...</strong>
                </div>
                <div style="background: #e0e0e0; border-radius: 10px; overflow: hidden; height: 30px;">
                    <div id="progressBar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #007bff, #0056b3); transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                        <span id="progressText">0%</span>
                    </div>
                </div>
                <div id="progressMessage" style="margin-top: 10px; color: #666; font-size: 14px;"></div>
            </div>
            
            <div id="status"></div>
        </div>

        <script>
            const form = document.getElementById('uploadForm');
            const fileInput = document.getElementById('audioFile');
            const fileName = document.getElementById('fileName');
            const status = document.getElementById('status');
            const submitBtn = document.getElementById('submitBtn');

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    fileName.textContent = `選択: ${e.target.files[0].name}`;
                }
            });

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const file = fileInput.files[0];
                if (!file) return;

                // セッション ID 生成
                const sessionId = Date.now().toString();

                // UI 更新
                submitBtn.disabled = true;
                submitBtn.textContent = '⏳ 分析中...';
                status.style.display = 'none';
                const progressContainer = document.getElementById('progressContainer');
                progressContainer.style.display = 'block';

                // WebSocket 接続
                const ws = new WebSocket(`ws://${window.location.host}/ws/${sessionId}`);
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    document.getElementById('currentStage').textContent = data.stage;
                    document.getElementById('progressBar').style.width = `${data.progress}%`;
                    document.getElementById('progressText').textContent = `${data.progress}%`;
                    document.getElementById('progressMessage').textContent = data.message;
                };

                ws.onerror = (error) => {
                    console.log('WebSocket エラー（進捗表示のみ影響）:', error);
                };

                // FormData 作成
                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch(`/api/analyze?session_id=${sessionId}`, {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (response.ok) {
                        progressContainer.style.display = 'none';
                        status.style.display = 'block';
                        status.className = 'success';
                        status.innerHTML = `
                            ✅ 分析完了!<br>
                            <strong>キーワード:</strong> ${result.summary.keywords.join(', ')}<br>
                            <strong>話速:</strong> ${result.summary.speech_rate} 文字/分<br>
                            <a href="${result.report_url}" target="_blank" style="display: inline-block; margin-top: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">📄 レポートを開く</a>
                        `;
                        ws.close();
                    } else {
                        throw new Error(result.detail || '分析に失敗しました');
                    }
                } catch (error) {
                    progressContainer.style.display = 'none';
                    status.style.display = 'block';
                    status.className = 'error';
                    status.textContent = `❌ エラー: ${error.message}`;
                    ws.close();
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🚀 分析開始';
                }
            });
        </script>
    </body>
    </html>
    """


@app.post("/api/analyze")
async def analyze_interview(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    音声ファイルを分析し、Markdown レポートを生成
    
    Args:
        file: 音声ファイル (mp3/wav/m4a)
    
    Returns:
        レポート URL と分析結果のサマリ
    """
    try:
        # ファイル検証
        allowed_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないファイル形式です。対応形式: {', '.join(allowed_extensions)}"
            )
        
        # タイムスタンプ生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # ファイル保存
        audio_filename = f"{timestamp}_{file.filename}"
        audio_path = AUDIO_DIR / audio_filename
        
        logger.info(f"音声ファイル保存開始: {audio_filename}")
        
        with open(audio_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"音声ファイル保存完了: {audio_path} ({len(content)} bytes)")
        
        # === 分析処理 ===
        
        # 1. 文字起こし
        logger.info("文字起こし開始...")
        transcript_result = transcribe_audio(str(audio_path))
        
        # 2. 音響分析
        logger.info("音響分析開始...")
        audio_features = analyze_audio_features(str(audio_path))
        
        # 3. 音声感情分析 (声の震え・緊張度)
        logger.info("音声感情分析開始...")
        voice_emotion = analyze_voice_emotion(str(audio_path))
        emotion_feedback = get_emotion_feedback(voice_emotion)
        
        # 4. AI 分析
        logger.info("AI 分析開始...")
        ai_analysis = analyze_with_gemini(
            transcript=transcript_result["text"],
            audio_features=audio_features
        )
        
        # 5. レポート生成
        logger.info("レポート生成開始...")
        report_filename = f"{timestamp}_report.md"
        report_path = REPORTS_DIR / report_filename
        
        generate_markdown_report(
            output_path=str(report_path),
            timestamp=timestamp,
            filename=file.filename,
            transcript=transcript_result,
            audio_features=audio_features,
            ai_analysis=ai_analysis,
            voice_emotion=voice_emotion,
            emotion_feedback=emotion_feedback
        )
        
        logger.info(f"レポート生成完了: {report_path}")
        
        # レスポンス
        return {
            "status": "success",
            "report_url": f"/reports/{report_filename}",
            "report_path": str(report_path),
            "summary": {
                "transcript_length": len(transcript_result["text"]),
                "speech_rate": audio_features.get("speech_rate", 0),
                "keywords": ai_analysis.get("keywords", [])[:5],
                "confidence_score": voice_emotion.get("confidence_score", 0),
                "nervousness_score": voice_emotion.get("nervousness_score", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"分析エラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析に失敗しました: {str(e)}")


@app.post("/api/video/analyze")
async def analyze_video_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    動画ファイルを受け取り、将来のビデオ分析処理へ連携するためのプレースホルダ API

    Phase 4 で実装予定の MediaPipe 解析に備え、現時点ではファイル保存とスタブ分析のみ行う。
    """
    try:
        allowed_extensions = {".mp4", ".mov", ".webm", ".mkv"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていない動画形式です。対応形式: {', '.join(sorted(allowed_extensions))}"
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"{timestamp}_{file.filename}"
        video_path = VIDEO_DIR / video_filename

        logger.info(f"動画ファイル保存開始: {video_filename}")
        with open(video_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"動画ファイル保存完了: {video_path} ({len(content)} bytes)")

        # Phase 4 予定のビデオ分析スタブを呼び出し
        analysis_result = analyze_video(str(video_path))

        preview_url = f"/videos/{video_filename}"

        return {
            "status": "pending",
            "message": "ビデオ分析は Phase 4 で本格対応予定です。アップロードした動画は安全に保存されています。",
            "preview_url": preview_url,
            "analysis": analysis_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"動画分析エラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"動画の処理に失敗しました: {str(e)}")


@app.get("/api/reports")
async def list_reports():
    """
    生成されたレポート一覧を取得
    """
    reports = []
    for report_file in REPORTS_DIR.glob("*.md"):
        reports.append({
            "filename": report_file.name,
            "url": f"/reports/{report_file.name}",
            "created_at": datetime.fromtimestamp(report_file.stat().st_mtime).isoformat()
        })
    
    reports.sort(key=lambda x: x["created_at"], reverse=True)
    return {"reports": reports, "total": len(reports)}


@app.get("/health")
async def health_check():
    """
    ヘルスチェック
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    return {
        "status": "healthy",
        "gemini_configured": bool(gemini_key and gemini_key != "your_api_key_here"),
        "output_dir_exists": OUTPUT_DIR.exists(),
        "audio_dir_exists": AUDIO_DIR.exists(),
        "reports_dir_exists": REPORTS_DIR.exists()
    }


@app.websocket("/ws/realtime")
async def websocket_realtime_analysis(websocket: WebSocket):
    """
    リアルタイム音声分析WebSocketエンドポイント
    
    クライアント → サーバー:
        { "type": "audio_chunk", "data": base64_encoded_audio }
        { "type": "end_session" }
    
    サーバー → クライアント:
        { "type": "transcription", "text": "...", "accumulated_text": "..." }
        { "type": "analysis", "keywords": [...], "confidence_score": 75, ... }
        { "type": "final", "full_text": "...", "analysis": {...} }
    """
    await websocket.accept()
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    active_connections[session_id] = websocket
    
    transcriber = RealtimeTranscriber()
    
    logger.info(f"WebSocket接続開始: {session_id}")
    
    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "リアルタイム分析開始"
        })
        
        while True:
            try:
                # クライアントからメッセージ受信
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "audio_chunk":
                    # Base64エンコードされた音声データをデコード
                    import base64
                    audio_data = base64.b64decode(data.get("data", ""))
                    
                    # バッファに追加
                    transcriber.add_audio_chunk(audio_data)
                    
                    # バッファが一定時間分貯まったら文字起こし + 音響・感情分析
                    if transcriber.get_buffer_duration() >= transcriber.buffer_duration:
                        result = await transcriber.process_buffer()
                        
                        if result.get("text"):
                            # 文字起こし結果送信
                            await websocket.send_json({
                                "type": "transcription",
                                "text": result["text"],
                                "accumulated_text": result["accumulated_text"],
                                "duration": result["duration"]
                            })
                            
                            # リアルタイム音響分析送信
                            audio_features = result.get("audio_features", {})
                            if audio_features:
                                await websocket.send_json({
                                    "type": "audio_analysis",
                                    "speech_rate": audio_features.get("speech_rate", 0),
                                    "average_volume": audio_features.get("average_volume", 0),
                                    "max_volume": audio_features.get("max_volume", 0),
                                    "pause_count": audio_features.get("pause_count", 0),
                                    "average_pitch": audio_features.get("average_pitch", 0)
                                })
                            
                            # リアルタイム感情分析送信
                            voice_emotion = result.get("voice_emotion", {})
                            if voice_emotion:
                                await websocket.send_json({
                                    "type": "voice_emotion",
                                    "jitter": voice_emotion.get("jitter", 0),
                                    "pitch_variance": voice_emotion.get("pitch_variance", 0),
                                    "energy_variance": voice_emotion.get("energy_variance", 0),
                                    "confidence_score": voice_emotion.get("confidence_score", 0),
                                    "nervousness_score": voice_emotion.get("nervousness_score", 0),
                                    "feedback": voice_emotion.get("feedback", "")
                                })
                            
                            # 一定量のテキストが貯まったらAI分析実行
                            if len(result["accumulated_text"]) > 100:
                                analysis = await transcriber.analyze_accumulated_text()
                                await websocket.send_json({
                                    "type": "analysis",
                                    **analysis
                                })
                
                elif message_type == "end_session":
                    # セッション終了：残りの処理
                    logger.info(f"セッション終了リクエスト: {session_id}")
                    
                    final_result = await transcriber.finalize()
                    final_analysis = await transcriber.analyze_accumulated_text()
                    
                    await websocket.send_json({
                        "type": "final",
                        "full_text": final_result["accumulated_text"],
                        "analysis": final_analysis
                    })
                    
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket切断: {session_id}")
                break
            except Exception as e:
                logger.error(f"WebSocketエラー: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    finally:
        # 接続クリーンアップ
        if session_id in active_connections:
            del active_connections[session_id]
        logger.info(f"WebSocket接続終了: {session_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


@app.websocket("/ws/live-analysis/{session_id}")
async def websocket_live_analysis(websocket: WebSocket, session_id: str):
    """
    リアルタイム音声+映像分析WebSocketエンドポイント
    
    クライアント → サーバー:
        { "type": "audio", "data": base64_audio_chunk }
        { "type": "video", "data": base64_video_frame }
        { "type": "stop" }
    
    サーバー → クライアント:
        { "type": "audio_analysis", "transcription": "...", "emotion": {...}, "audio_level": 75 }
        { "type": "video_analysis", "posture": {...}, "eye_contact": {...} }
        { "type": "summary", ... }
    """
    await websocket.accept()
    active_connections[session_id] = websocket
    
    session_recorder = SessionRecorder(session_id, SESSIONS_DIR)
    analyzer = RealtimeAnalyzer(session_id, recorder=session_recorder)
    logger.info(f"リアルタイム分析開始: {session_id}")
    
    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "リアルタイム分析準備完了"
        })
        
        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "audio":
                    # 音声チャンク分析
                    import base64
                    audio_bytes = base64.b64decode(data.get("data", ""))
                    result = await analyzer.analyze_audio_chunk(audio_bytes)
                    await websocket.send_json(result)
                    
                elif message_type == "video":
                    # 映像フレーム分析
                    import base64
                    frame_bytes = base64.b64decode(data.get("data", ""))
                    result = await analyzer.analyze_video_frame(frame_bytes)
                    await websocket.send_json(result)
                    
                elif message_type == "stop":
                    # セッション終了：サマリーとレポート生成
                    logger.info(f"セッション終了: {session_id}")
                    
                    recording_info = await analyzer.finalize_session()
                    summary = await analyzer.get_summary()
                    await websocket.send_json(summary)

                    await websocket.send_json({
                        "type": "processing",
                        "message": "録画データを解析しています..."
                    })

                    try:
                        report_info = await run_post_session_pipeline(session_id, recording_info, REPORTS_DIR)
                        await websocket.send_json({
                            "type": "report_ready",
                            "report_url": report_info["report_url"],
                            "report_path": report_info["report_path"],
                            "video_analysis": report_info.get("video"),
                            "message": "レポートが生成されました"
                        })
                        logger.info(f"レポート生成完了: {report_info['report_path']}")
                    except Exception as e:
                        logger.error(f"レポート生成エラー: {e}", exc_info=True)
                        await websocket.send_json({
                            "type": "error",
                            "message": f"レポート生成に失敗しました: {str(e)}"
                        })
                    
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket切断: {session_id}")
                break
            except Exception as e:
                logger.error(f"分析エラー: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    finally:
        if session_id in active_connections:
            del active_connections[session_id]
        await analyzer.finalize_session()
        logger.info(f"リアルタイム分析終了: {session_id}")

