"""
Markdownレポート生成
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Template

logger = logging.getLogger(__name__)

REPORT_TEMPLATE = """# 面接練習レポート

**日時**: {{ timestamp }}  
**セッションID**: {{ session_id }}

---

## 📝 文字起こし

{% if speakers %}
### 話者別発言

{% for seg in segments %}
**{{ seg.speaker or "不明" }}** ({{ "%.1f"|format(seg.start) }}s - {{ "%.1f"|format(seg.end) }}s)  
> {{ seg.text }}

{% endfor %}

### 全文

{{ transcript }}

{% else %}
{{ transcript }}
{% endif %}

---

## 📊 音声分析結果

### 基本情報
- **録音時間**: {{ duration }}秒
- **言語**: {{ language }}
{% if speakers %}
- **検出話者数**: {{ speaker_count }}名
{% endif %}

### 音響特徴
| 項目 | 値 | 評価 |
|------|------|------|
| 話速 | {{ speech_rate }} 文字/分 | {{ speech_rate_assessment }} |
| ポーズ回数 | {{ pause_count }}回 | {{ pause_assessment }} |
| 平均ピッチ | {{ pitch_mean }} Hz | - |
| 声の安定性 (ジッター) | {{ jitter }}% | {{ jitter_assessment }} |

### 声域分析（VoiceMind風）

```
低音域: {{ voice_range_low }}%   {{ voice_range_low_bar }}
中音域: {{ voice_range_mid }}%   {{ voice_range_mid_bar }}
高音域: {{ voice_range_high }}%  {{ voice_range_high_bar }}

支配的な声域: {{ voice_range_dominant }}
```

{% if speakers and speaker_count > 1 %}
### 話者別タイムライン

```
{% for seg in speakers %}
{{ seg.speaker }}: {{ "%.1f"|format(seg.start) }}s ━━━━━━━━━━ {{ "%.1f"|format(seg.end) }}s ({{ "%.1f"|format(seg.end - seg.start) }}秒)
{% endfor %}
```
{% endif %}

### 声質分析（VoiceMind風12軸）

**性格タイプ**: {{ personality_type }} (平均スコア: {{ avg_score }})

#### 多次元分析チャート

```
         社会性                行動性
    {{ "%3d"|format(social) }} {{ social_bar }}     {{ "%3d"|format(action) }} {{ action_bar }}

感覚性                              感情性
{{ "%3d"|format(sensation) }} {{ sensation_bar }}              {{ "%3d"|format(emotion) }} {{ emotion_bar }}

分析性                              本能性
{{ "%3d"|format(analysis) }} {{ analysis_bar }}              {{ "%3d"|format(instinct) }} {{ instinct_bar }}

思考性                              存在感
{{ "%3d"|format(thinking) }} {{ thinking_bar }}              {{ "%3d"|format(presence) }} {{ presence_bar }}

順応性                              自己表現
{{ "%3d"|format(adaptation) }} {{ adaptation_bar }}              {{ "%3d"|format(self_expression) }} {{ self_expression_bar }}

    {{ "%3d"|format(balance) }} {{ balance_bar }}     {{ "%3d"|format(harmony) }} {{ harmony_bar }}
         調和性                同調性
```

**最も強い特性**: {{ dominant_trait }} ({{ dominant_score }}点)

---

## 🎯 Gemini AI面接分析

{% if interview_analysis and interview_analysis.overall_score > 0 %}

### 総合評価

**スコア**: {{ interview_analysis.overall_score }}/100点

### 内容の質

| 項目 | スコア | 評価 |
|------|--------|------|
| 志望動機の明確さ | {{ interview_analysis.content_quality.motivation }}/100 | {{ "█" * (interview_analysis.content_quality.motivation // 10) }}{{ "░" * (10 - interview_analysis.content_quality.motivation // 10) }} |
| 自己PRの具体性 | {{ interview_analysis.content_quality.self_pr }}/100 | {{ "█" * (interview_analysis.content_quality.self_pr // 10) }}{{ "░" * (10 - interview_analysis.content_quality.self_pr // 10) }} |
| 質疑応答の質 | {{ interview_analysis.content_quality.response_quality }}/100 | {{ "█" * (interview_analysis.content_quality.response_quality // 10) }}{{ "░" * (10 - interview_analysis.content_quality.response_quality // 10) }} |

### 話者別分析

{% if interview_analysis.speaker_analysis %}
**面接官**: {{ interview_analysis.speaker_analysis.interviewer }}

**応募者**: {{ interview_analysis.speaker_analysis.candidate }}
{% endif %}

{% if interview_analysis.problem_areas %}
### 問題箇所の検出

{% for problem in interview_analysis.problem_areas %}
- **{{ problem.time }}** ({{ problem.speaker }}): **{{ problem.issue }}**
  - {{ problem.description }}
  - 重要度: {{ "🔴" if problem.severity == "high" else "🟡" if problem.severity == "medium" else "🟢" }}
{% endfor %}
{% endif %}

### AI改善提案

{% for suggestion in interview_analysis.suggestions %}
- {{ suggestion }}
{% endfor %}

{% else %}
_Gemini APIが設定されていないため、AI分析は実行されませんでした。_
{% endif %}

---

## 💡 音声分析による改善ポイント

{{ improvement_suggestions }}

---

## ✍️ 教師コメント

_※ここに教師のコメントを記入してください_

---

**生成日時**: {{ generated_at }}
"""


class ReportGenerator:
    """レポート生成クラス"""
    
    def __init__(self):
        self.template = Template(REPORT_TEMPLATE)
    
    def generate(
        self,
        session_id: str,
        transcript_result: Dict[str, Any],
        audio_features: Dict[str, Any],
        emotion_scores: Dict[str, int],
        output_dir: Path,
        interview_analysis: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Markdownレポートを生成
        
        Args:
            session_id: セッションID
            transcript_result: 文字起こし結果
            audio_features: 音響特徴
            emotion_scores: 感情スコア
            output_dir: 出力ディレクトリ
            interview_analysis: Gemini面接分析結果
            
        Returns:
            生成されたレポートファイルのパス
        """
        logger.info(f"レポート生成開始: {session_id}")
        
        # 話速計算
        text_length = len(transcript_result["text"])
        duration_min = audio_features["duration"] / 60
        speech_rate = int(text_length / duration_min) if duration_min > 0 else 0
        
        # プログレスバー生成
        def make_bar(score: int) -> str:
            filled = int(score / 10)
            return "█" * filled + "░" * (10 - filled)
        
        # 評価テキスト生成
        def assess_speech_rate(rate: int) -> str:
            if 250 <= rate <= 350: return "✅ 適切"
            elif rate < 250: return "⚠️ ゆっくり"
            else: return "⚠️ 速い"
        
        def assess_pause(count: int) -> str:
            if count < 5: return "⚠️ 少ない"
            elif count <= 15: return "✅ 適切"
            else: return "⚠️ 多い"
        
        def assess_jitter(j: float) -> str:
            if j < 3: return "✅ 安定"
            elif j < 5: return "⚠️ やや不安定"
            else: return "❌ 不安定"
        
        # 改善提案生成 (12軸分析ベース)
        suggestions = []
        if speech_rate > 350:
            suggestions.append("- ⏱️ **話速**: 少しゆっくり話すと聞き取りやすくなります")
        if audio_features["jitter"] > 5:
            suggestions.append("- 😌 **声の安定性**: 深呼吸してリラックスしましょう")
        
        # 12軸分析からの提案
        dims = emotion_scores.get('dimensions', {})
        if dims.get('social', 50) < 40:
            suggestions.append("- 🗣️ **社交性**: もう少し明るく話すと印象が良くなります")
        if dims.get('emotion', 50) < 30:
            suggestions.append("- 😊 **感情表現**: 表情豊かに話すことを意識しましょう")
        if dims.get('presence', 50) < 35:
            suggestions.append("- 💪 **存在感**: 声に自信を持って、堂々と話しましょう")
        
        if not suggestions:
            suggestions.append("- ✨ **総合**: 全体的に良好です！この調子で練習を続けましょう")
        
        # レンダリング
        speakers = transcript_result.get("speakers", [])
        speaker_count = len(set(s["speaker"] for s in speakers)) if speakers else 0
        
        content = self.template.render(
            session_id=session_id,
            timestamp=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
            transcript=transcript_result["text"],
            segments=transcript_result.get("segments", []),
            speakers=speakers,
            speaker_count=speaker_count,
            duration=f"{audio_features['duration']:.1f}",
            language=transcript_result.get("language", "ja"),
            speech_rate=speech_rate,
            speech_rate_assessment=assess_speech_rate(speech_rate),
            pause_count=audio_features["pause_count"],
            pause_assessment=assess_pause(audio_features["pause_count"]),
            pitch_mean=f"{audio_features['pitch_mean']:.1f}",
            pitch_std=f"{audio_features['pitch_std']:.1f}",
            jitter=f"{audio_features['jitter']:.2f}",
            jitter_assessment=assess_jitter(audio_features["jitter"]),
            voice_range_low=audio_features['voice_range']['low'],
            voice_range_low_bar=make_bar(int(audio_features['voice_range']['low'])),
            voice_range_mid=audio_features['voice_range']['mid'],
            voice_range_mid_bar=make_bar(int(audio_features['voice_range']['mid'])),
            voice_range_high=audio_features['voice_range']['high'],
            voice_range_high_bar=make_bar(int(audio_features['voice_range']['high'])),
            voice_range_dominant=audio_features['voice_range']['dominant'],
            # VoiceMind風12軸分析
            personality_type=emotion_scores['summary']['personality_type'],
            avg_score=emotion_scores['summary']['average'],
            dominant_trait=self._translate_trait(emotion_scores['summary']['dominant_trait']),
            dominant_score=emotion_scores['summary']['dominant_score'],
            social=emotion_scores['dimensions']['social'],
            social_bar=make_bar(emotion_scores['dimensions']['social']),
            action=emotion_scores['dimensions']['action'],
            action_bar=make_bar(emotion_scores['dimensions']['action']),
            emotion=emotion_scores['dimensions']['emotion'],
            emotion_bar=make_bar(emotion_scores['dimensions']['emotion']),
            instinct=emotion_scores['dimensions']['instinct'],
            instinct_bar=make_bar(emotion_scores['dimensions']['instinct']),
            presence=emotion_scores['dimensions']['presence'],
            presence_bar=make_bar(emotion_scores['dimensions']['presence']),
            self_expression=emotion_scores['dimensions']['self_expression'],
            self_expression_bar=make_bar(emotion_scores['dimensions']['self_expression']),
            harmony=emotion_scores['dimensions']['harmony'],
            harmony_bar=make_bar(emotion_scores['dimensions']['harmony']),
            balance=emotion_scores['dimensions']['balance'],
            balance_bar=make_bar(emotion_scores['dimensions']['balance']),
            adaptation=emotion_scores['dimensions']['adaptation'],
            adaptation_bar=make_bar(emotion_scores['dimensions']['adaptation']),
            thinking=emotion_scores['dimensions']['thinking'],
            thinking_bar=make_bar(emotion_scores['dimensions']['thinking']),
            analysis=emotion_scores['dimensions']['analysis'],
            analysis_bar=make_bar(emotion_scores['dimensions']['analysis']),
            sensation=emotion_scores['dimensions']['sensation'],
            sensation_bar=make_bar(emotion_scores['dimensions']['sensation']),
            improvement_suggestions="\n".join(suggestions),
            interview_analysis=interview_analysis or {},
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # ファイル保存
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"{session_id}.md"
        
        report_path.write_text(content, encoding="utf-8")
        logger.info(f"レポート生成完了: {report_path}")
        
        return report_path
    
    def _translate_trait(self, trait: str) -> str:
        """特性名を日本語に変換"""
        translations = {
            "social": "社会性",
            "action": "行動性",
            "emotion": "感情性",
            "instinct": "本能性",
            "presence": "存在感",
            "self_expression": "自己表現",
            "harmony": "同調性",
            "balance": "調和性",
            "adaptation": "順応性",
            "thinking": "思考性",
            "analysis": "分析性",
            "sensation": "感覚性"
        }
        return translations.get(trait, trait)
