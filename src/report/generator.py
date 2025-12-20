"""
分析レポート生成（感情チャート付き）
"""
from datetime import datetime
from typing import Dict, List
import json
import os
import matplotlib
matplotlib.use('Agg')  # GUIなし環境用
import matplotlib.pyplot as plt
import base64
from io import BytesIO


class ReportGenerator:
    def __init__(self, report_folder: str = "./data/reports"):
        """
        Args:
            report_folder: レポート保存フォルダ
        """
        self.report_folder = report_folder
        os.makedirs(report_folder, exist_ok=True)
    
    def generate_html_report(
        self,
        interview_id: int,
        filename: str,
        transcription: List[Dict],
        audio_analysis: Dict,
        keigo_evaluation: Dict = None
    ) -> str:
        """
        HTMLレポート生成
        
        Args:
            interview_id: 面接ID
            filename: 音声ファイル名
            transcription: 文字起こし結果
            audio_analysis: 音声分析結果
            keigo_evaluation: 敬語評価結果
        
        Returns:
            レポートファイルパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"report_{interview_id}_{timestamp}.html"
        report_path = os.path.join(self.report_folder, report_filename)
        
        # HTMLコンテンツ生成
        html_content = self._create_html_content(
            filename,
            transcription,
            audio_analysis,
            keigo_evaluation
        )
        
        # ファイルに書き込み
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"Report generated: {report_path}")
        return report_path
    
    def _create_html_content(
        self,
        filename: str,
        transcription: List[Dict],
        audio_analysis: Dict,
        keigo_evaluation: Dict = None
    ) -> str:
        """
        HTMLコンテンツを作成
        """
        # 文字起こし部分のHTML
        transcript_html = self._format_transcription(transcription)
        
        # 音声分析部分のHTML
        audio_html = self._format_audio_analysis(audio_analysis)
        
        # 敬語評価部分のHTML
        keigo_html = ""
        if keigo_evaluation:
            keigo_html = self._format_keigo_evaluation(keigo_evaluation)
        
        # 完成HTML
        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>面接練習レポート - {filename}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Meiryo, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .transcript-line {{
            margin: 15px 0;
            padding: 10px;
            border-left: 4px solid #ddd;
            background-color: #f9f9f9;
        }}
        .speaker-teacher {{
            border-left-color: #667eea;
        }}
        .speaker-student {{
            border-left-color: #f093fb;
        }}
        .speaker-label {{
            font-weight: bold;
            color: #667eea;
            margin-right: 10px;
        }}
        .timestamp {{
            color: #999;
            font-size: 0.9em;
            margin-right: 10px;
        }}
        .score {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            text-align: center;
            margin: 20px 0;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .metric-label {{
            font-weight: bold;
            color: #555;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 1.3em;
            color: #667eea;
        }}
        .feedback {{
            background: #e8f4f8;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        .feedback-item {{
            margin: 8px 0;
            padding-left: 20px;
        }}
        .good {{
            color: #28a745;
        }}
        .warning {{
            color: #ffc107;
        }}
        .chart-container {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .chart-container h4 {{
            margin-top: 0;
            color: #667eea;
        }}
        .footer {{
            text-align: center;
            color: #999;
            margin-top: 40px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 面接練習分析レポート</h1>
        <p>ファイル: {filename}</p>
        <p>作成日時: {datetime.now().strftime("%Y年%m月%d日 %H:%M")}</p>
    </div>
    
    {audio_html}
    
    {keigo_html}
    
    <div class="section">
        <h2>💬 文字起こし結果</h2>
        {transcript_html}
    </div>
    
    <div class="footer">
        <p>面接練習レポート支援ツール</p>
        <p>© 2025 - Powered by Whisper, Ollama, librosa</p>
    </div>
</body>
</html>"""
        
        return html
    
    def _format_transcription(self, segments: List[Dict]) -> str:
        """文字起こしをHTMLフォーマット"""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "不明")
            text = seg.get("corrected_text") or seg.get("text", "")
            start_time = self._format_time(seg.get("start", 0))
            
            speaker_class = "speaker-teacher" if speaker == "教師" else "speaker-student"
            
            lines.append(f'''
                <div class="transcript-line {speaker_class}">
                    <span class="timestamp">{start_time}</span>
                    <span class="speaker-label">{speaker}</span>
                    <span class="text">{text}</span>
                </div>
            ''')
        
        return "\n".join(lines)
    
    def _format_audio_analysis(self, analysis: Dict) -> str:
        """音声分析結果をHTMLフォーマット（感情チャート付き）"""
        by_speaker = analysis.get("by_speaker", {})
        
        html_parts = ['<div class="section"><h2>🎵 音声分析結果</h2>']
        
        for speaker, data in by_speaker.items():
            score_data = analysis.get(f"{speaker}_evaluation", {})
            score = score_data.get("score", 0)
            feedback = score_data.get("feedback", [])
            emotions = data.get("emotion_average", {})
            
            # 感情チャートを生成
            chart_img = self._create_emotion_chart(data, speaker)
            
            html_parts.append(f'''
                <h3>{speaker} の分析</h3>
                <div class="score">{score}点</div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">自信度</div>
                        <div class="metric-value">{emotions.get("confidence", 0):.1f}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">活力</div>
                        <div class="metric-value">{emotions.get("energy", 0):.1f}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">落ち着き</div>
                        <div class="metric-value">{emotions.get("calmness", 0):.1f}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">話速</div>
                        <div class="metric-value">{data.get("speaking_rate", 0):.0f} 文字/分</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">発話時間</div>
                        <div class="metric-value">{data.get("total_duration", 0):.1f} 秒</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h4>感情の推移</h4>
                    <img src="data:image/png;base64,{chart_img}" alt="感情推移グラフ" style="max-width: 100%; height: auto;">
                </div>
                
                <div class="feedback">
                    <h4>フィードバック</h4>
            ''')
            
            for item in feedback:
                feedback_class = "good" if "✓" in item else "warning"
                html_parts.append(f'<div class="feedback-item {feedback_class}">{item}</div>')
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        return "\n".join(html_parts)
    
    def _format_keigo_evaluation(self, evaluation: Dict) -> str:
        """敬語評価をHTMLフォーマット"""
        score = evaluation.get("score", 0)
        good_points = evaluation.get("good_points", [])
        improvements = evaluation.get("improvements", [])
        
        html = f'''
        <div class="section">
            <h2>✍️ 敬語・表現評価</h2>
            <div class="score">{score}点</div>
            
            <div class="feedback">
                <h4>良い点</h4>
        '''
        
        for point in good_points:
            html += f'<div class="feedback-item good">✓ {point}</div>'
        
        html += '<h4>改善点</h4>'
        
        for point in improvements:
            html += f'<div class="feedback-item warning">⚠ {point}</div>'
        
        html += '</div></div>'
        
        return html
    
    def _create_emotion_chart(self, speaker_data: Dict, speaker_name: str) -> str:
        """
        感情の時系列チャートを生成してBase64エンコード
        
        Args:
            speaker_data: 話者の分析データ
            speaker_name: 話者名
        
        Returns:
            Base64エンコードされた画像
        """
        emotion_timeline = speaker_data.get("emotion_timeline", [])
        
        if not emotion_timeline:
            return ""
        
        # 日本語フォント設定
        plt.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # データ準備
        times = [e["time"] / 60 for e in emotion_timeline]  # 秒から分に変換
        confidence = [e["confidence"] for e in emotion_timeline]
        energy = [e["energy"] for e in emotion_timeline]
        calmness = [e["calmness"] for e in emotion_timeline]
        stress = [e["stress"] for e in emotion_timeline]
        
        # グラフ作成
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(times, confidence, label='自信度', marker='o', linewidth=2, markersize=4, color='#667eea')
        ax.plot(times, energy, label='活力', marker='s', linewidth=2, markersize=4, color='#f093fb')
        ax.plot(times, calmness, label='落ち着き', marker='^', linewidth=2, markersize=4, color='#4facfe')
        ax.plot(times, stress, label='緊張度', marker='d', linewidth=2, markersize=4, color='#fa709a')
        
        ax.set_xlabel('時間 (分)', fontsize=12)
        ax.set_ylabel('スコア (%)', fontsize=12)
        ax.set_title(f'{speaker_name}の感情推移', fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
        
        # Base64エンコード
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return image_base64
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """秒を MM:SS 形式に変換"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    # テスト用
    generator = ReportGenerator()
    print("ReportGenerator initialized successfully")
