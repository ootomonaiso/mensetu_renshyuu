"""
Markdown レポート生成サービス
"""
from jinja2 import Template
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def generate_markdown_report(
    report_data: Dict[str, Any],
    output_path: str
) -> None:
    """
    Markdown レポートを生成（リアルタイム分析用）
    
    Args:
        report_data: レポートデータ（transcription, audio_features, voice_emotion, ai_analysis 含む）
        output_path: 出力ファイルパス
    """
    try:
        # 後方互換性のため、旧形式の引数もサポート
        if isinstance(report_data, str):
            # 旧形式: output_path が第1引数
            logger.warning("旧形式の generate_markdown_report 呼び出しを検出しました")
            return _generate_markdown_report_legacy(*[report_data, output_path] + list(locals().values())[2:])
        
        # テンプレート読み込み
        template_path = Path(__file__).parent.parent / "templates" / "report.md.j2"
        
        if not template_path.exists():
            # テンプレートが無い場合はインラインテンプレートを使用
            logger.warning("テンプレートファイルが見つかりません。デフォルトテンプレートを使用します。")
            template_str = _get_default_template()
        else:
            with open(template_path, "r", encoding="utf-8") as f:
                template_str = f.read()
        
        template = Template(template_str)
        
        # データ準備
        timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        filename = report_data.get("filename", "リアルタイム分析")
        
        transcript = report_data.get("transcription", {})
        audio_features = report_data.get("audio_features", {})
        ai_analysis = report_data.get("ai_analysis", {})
        voice_emotion = report_data.get("voice_emotion", {})
        
        # 話速の計算
        if "duration" in audio_features and audio_features["duration"] > 0:
            transcript_text = transcript.get("text", "")
            actual_speech_rate = (len(transcript_text) / audio_features["duration"]) * 60
            audio_features["speech_rate"] = round(actual_speech_rate, 1)
        
        # レンダリング
        content = template.render(
            date=timestamp,
            filename=filename,
            transcript=transcript,
            audio=audio_features,
            ai=ai_analysis,
            emotion=voice_emotion,
            emotion_feedback=voice_emotion.get("feedback", "")
        )
        
        # ファイル出力
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"レポート生成完了: {output_path}")
        
    except Exception as e:
        logger.error(f"レポート生成エラー: {str(e)}", exc_info=True)
        raise


def _get_default_template() -> str:
    """デフォルトのレポートテンプレート"""
    return """# 面接練習レポート

**日時**: {{ date }}  
**音声ファイル**: `{{ filename }}`

---

## 📝 文字起こし結果

{{ transcript.text }}

{% if transcript.segment_count > 0 %}
**セグメント数**: {{ transcript.segment_count }}  
**音声の長さ**: {{ audio.duration }}秒
{% endif %}

---

## 📊 音響分析

| 項目 | 値 | 評価 |
|------|-----|------|
| **話速** | {{ audio.speech_rate }} 文字/分 | {% if audio.speech_rate > 350 %}少し速いです{% elif audio.speech_rate < 250 %}少しゆっくりです{% else %}適切です{% endif %} |
| **平均音量** | {{ audio.average_volume }} dB | {% if audio.average_volume > -20 %}良好です{% elif audio.average_volume > -30 %}適切です{% else %}少し小さめです{% endif %} |
| **ポーズ回数** | {{ audio.pause_count }} 回 | {% if audio.pause_count > 15 %}やや多めです{% elif audio.pause_count < 5 %}とても少ないです{% else %}適切です{% endif %} |
| **総ポーズ時間** | {{ audio.pause_total_duration }} 秒 | - |
| **平均ピッチ** | {{ audio.pitch_mean }} Hz | - |

### 分析コメント

{% if audio.speech_rate > 350 %}
- 話速が速めです。落ち着いて、一呼吸おいて話すと良いでしょう。
{% elif audio.speech_rate < 250 %}
- 話速がやや遅めです。もう少しテンポよく話すことを意識しましょう。
{% else %}
- 話速は適切です。このペースを維持しましょう。
{% endif %}

{% if audio.pause_count > 15 %}
- ポーズが多めです。事前準備を十分にして、スムーズに話せるようにしましょう。
{% elif audio.pause_count < 5 %}
- ポーズが少ないです。要点を強調する際に、意図的なポーズを入れると効果的です。
{% endif %}

---

## 🤖 AI 分析結果

### キーワード

{% if ai.keywords %}
{% for keyword in ai.keywords %}
- {{ keyword }}
{% endfor %}
{% else %}
キーワードが検出されませんでした。
{% endif %}

### 敬語チェック

{{ ai.keigo_feedback }}

### 感情分析

| 項目 | スコア | 評価 |
|------|--------|------|
| **自信度** | {{ ai.confidence_score }}/100 | {% if ai.confidence_score > 70 %}自信を持って話せています✨{% elif ai.confidence_score > 50 %}もう少し自信を持ちましょう{% else %}練習を重ねて自信をつけましょう{% endif %} |
| **緊張度** | {{ ai.nervousness_score }}/100 | {% if ai.nervousness_score > 70 %}かなり緊張しています{% elif ai.nervousness_score > 50 %}やや緊張気味です{% else %}リラックスして話せています{% endif %} |

### 全体的な印象

{{ ai.overall_impression }}

---

## 💬 教師コメント

<!-- ここに教師がコメントを追加してください -->

**指導ポイント**:
- 
- 
- 

**次回までの課題**:
1. 
2. 
3. 

---

## 📈 改善のヒント

### 話し方
- 明瞭に発音する
- 適度なスピードで話す (300文字/分程度)
- 要点の前後で間を取る

### 内容
- 具体的なエピソードを交える
- 結論→理由→具体例の順で話す (PREP法)
- 志望動機と自分の強みを関連付ける

### 態度
- 笑顔を意識する
- 相手の目を見て話す (視線を3秒ずつ)
- 姿勢を正しく保つ

---

**生成日時**: {{ date }}  
**システム**: 圧勝面接練習システム v1.0
"""


def _generate_markdown_report_legacy(
    output_path: str,
    timestamp: str,
    filename: str,
    transcript: Dict[str, Any],
    audio_features: Dict[str, Any],
    ai_analysis: Dict[str, Any],
    voice_emotion: Dict[str, Any] = None,
    emotion_feedback: str = None
) -> None:
    """
    旧形式の generate_markdown_report（後方互換性用）
    """
    report_data = {
        "filename": filename,
        "transcription": transcript,
        "audio_features": audio_features,
        "ai_analysis": ai_analysis,
        "voice_emotion": voice_emotion or {},
    }
    
    return generate_markdown_report(report_data, output_path)
