"""
面接練習システム - Flask + WebSocket版
録音 → 分析 → レポート生成をシンプルに実装
"""
from flask import Flask, render_template, request, send_file, jsonify
from flask_sock import Sock
import logging
import json
import base64
from pathlib import Path
from datetime import datetime
import numpy as np
from dotenv import load_dotenv

from services.recorder import SessionRecorder
from services.audio_processor import AudioProcessor
from services.report_generator import ReportGenerator
from services.gemini_analyzer import GeminiAnalyzer

# 環境変数読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask初期化
app = Flask(__name__)
sock = Sock(app)

# ディレクトリ設定
OUTPUT_DIR = Path("output")
SESSIONS_DIR = OUTPUT_DIR / "sessions"
REPORTS_DIR = OUTPUT_DIR / "reports"

for dir_path in [OUTPUT_DIR, SESSIONS_DIR, REPORTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 音声処理モデル (遅延ロード)
audio_processor = None
gemini_analyzer = None


def get_audio_processor():
    """AudioProcessorのシングルトン取得"""
    global audio_processor
    if audio_processor is None:
        audio_processor = AudioProcessor(model_size="base")
    return audio_processor


def get_gemini_analyzer():
    """GeminiAnalyzerのシングルトン取得"""
    global gemini_analyzer
    if gemini_analyzer is None:
        gemini_analyzer = GeminiAnalyzer()
    return gemini_analyzer


# アクティブセッション管理
active_sessions = {}


@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    """Favicon対応"""
    return '', 204


@app.route('/reports')
def list_reports():
    """レポート一覧"""
    reports = []
    for report_file in REPORTS_DIR.glob("*.md"):
        reports.append({
            "name": report_file.stem,
            "path": f"/reports/{report_file.name}",
            "created": datetime.fromtimestamp(report_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        })
    reports.sort(key=lambda x: x["created"], reverse=True)
    return jsonify(reports)


@app.route('/reports/<filename>')
def serve_report(filename):
    """レポートファイル配信"""
    file_path = REPORTS_DIR / filename
    if file_path.exists():
        return send_file(file_path, mimetype='text/markdown')
    return "ファイルが見つかりません", 404


@sock.route('/ws/record')
def websocket_record(ws):
    """
    WebSocketエンドポイント - 録音と分析
    """
    session_id = None
    recorder = None
    
    try:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        logger.info(f"新規セッション開始: {session_id}")
        
        # レコーダー初期化
        recorder = SessionRecorder(session_id, SESSIONS_DIR)
        recorder.start()
        active_sessions[session_id] = recorder
        
        logger.info(f"WebSocket接続確立: {session_id}")
        
        while True:
            try:
                message = ws.receive()
                if message is None:
                    logger.info(f"クライアントが切断: {session_id}")
                    break
                
                data = json.loads(message)
                message_type = data.get('type')
                
                logger.debug(f"受信: {message_type} ({session_id})")
                
                if message_type == 'audio_chunk':
                    # 音声チャンク受信 → WAVファイルに書き込み
                    audio_bytes = base64.b64decode(data.get('data', ''))
                    recorder.write_chunk(audio_bytes)
                    
                    # 簡易フィードバック (オプション)
                    ws.send(json.dumps({
                        'type': 'status',
                        'message': '録音中...'
                    }))
                    
                elif message_type == 'stop':
                    # 録音停止 → 分析開始
                    logger.info(f"セッション終了・分析開始: {session_id}")
                    audio_path = recorder.stop()
                    
                    # 分析実行
                    ws.send(json.dumps({
                        'type': 'status',
                        'message': '音声を分析中...'
                    }))
                    
                    processor = get_audio_processor()
                    
                    # 文字起こし
                    transcript_result = processor.transcribe(audio_path)
                    
                    # 音響分析
                    audio_features = processor.analyze_audio(audio_path)
                    
                    # 声質の多次元分析（VoiceMind風）
                    voice_quality = processor.analyze_voice_quality(audio_features)
                    
                    # Gemini面接分析
                    ws.send(json.dumps({
                        'type': 'status',
                        'message': 'Gemini AIで面接内容を分析中...'
                    }))
                    
                    gemini = get_gemini_analyzer()
                    interview_analysis = gemini.analyze_interview_content(
                        transcript_result['text'],
                        transcript_result.get('speakers', [])
                    )
                    
                    # レポート生成
                    ws.send(json.dumps({
                        'type': 'status',
                        'message': 'レポートを生成中...'
                    }))
                    
                    report_gen = ReportGenerator()
                    report_path = report_gen.generate(
                        session_id,
                        transcript_result,
                        audio_features,
                        voice_quality,
                        REPORTS_DIR,
                        interview_analysis=interview_analysis
                    )
                    
                    # 完了通知
                    ws.send(json.dumps({
                        'type': 'complete',
                        'session_id': session_id,
                        'report_url': f'/reports/{report_path.name}',
                        'transcript': transcript_result['text'],
                        'speakers': transcript_result.get('speakers', []),
                        'voice_range': audio_features.get('voice_range', {}),
                        'voice_quality': voice_quality,
                        'interview_analysis': interview_analysis
                    }))
                    
                    logger.info(f"セッション完了: {session_id}")
                    break
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSONパースエラー: {e}")
                ws.send(json.dumps({
                    'type': 'error',
                    'message': 'データ形式エラー'
                }))
            except Exception as e:
                logger.error(f"メッセージ処理エラー: {e}", exc_info=True)
                ws.send(json.dumps({
                    'type': 'error',
                    'message': f'処理エラー: {str(e)}'
                }))
                
    except Exception as e:
        logger.error(f"WebSocketエラー ({session_id}): {e}", exc_info=True)
        try:
            ws.send(json.dumps({
                'type': 'error',
                'message': f'エラーが発生しました: {str(e)}'
            }))
        except:
            pass
    finally:
        if session_id and session_id in active_sessions:
            del active_sessions[session_id]
        if recorder:
            try:
                recorder.stop()
            except:
                pass
        logger.info(f"セッション終了: {session_id}")


if __name__ == '__main__':
    print("=" * 60)
    print("🎤 面接練習システム - 起動中")
    print("=" * 60)
    print(f"📂 出力ディレクトリ: {OUTPUT_DIR.absolute()}")
    print(f"🌐 アクセス: http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
