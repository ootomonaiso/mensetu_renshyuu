# AI分析実装ガイド

**更新日**: 2025年11月29日

---

## 概要

このシステムでは、以下の分析にGemini APIを活用します:
1. **キーワード抽出**: 面接内容から重要キーワードを抽出
2. **敬語分析**: 文字起こしテキストから敬語の適切性を分析
3. **感情分析**: テキストと音声特徴から感情を推定

---

## 1. キーワード抽出

### Gemini APIプロンプト

```python
KEYWORD_EXTRACTION_PROMPT = """
あなたは面接分析の専門家です。以下の面接の文字起こしから、
重要なキーワードを抽出し、それぞれの関連性とコンテキストを分析してください。

# 文字起こし
{transcript}

# 生徒プロフィール
- 志望業界: {target_industry}
- 志望職種: {target_position}
- 部活動: {club_activity}

# 出力形式
以下のJSON形式で出力してください:
{{
  "keywords": [
    {{
      "keyword": "キーワード",
      "relevance": 0.95,  // 0-1の関連度
      "context": "志望動機/自己PR/学生時代の経験/その他",
      "explanation": "このキーワードが重要な理由"
    }}
  ],
  "categories": ["志望動機", "自己PR", "学生時代の経験"],
  "summary": "面接内容の簡潔な要約（100文字程度）",
  "strengths": ["強みとして評価できる点"],
  "areas_to_improve": ["改善が望まれる点"]
}}
"""
```

### 実装例

```python
import google.generativeai as genai
import json

def extract_keywords(transcript: str, student_profile: dict) -> dict:
    """Gemini APIでキーワード抽出"""
    
    # キャッシュチェック
    cache_key = generate_cache_key(transcript, "keywords")
    cached = get_from_cache(cache_key)
    if cached:
        return cached
    
    # Gemini API呼び出し
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = KEYWORD_EXTRACTION_PROMPT.format(
        transcript=transcript,
        target_industry=student_profile.get('target_industry', ''),
        target_position=student_profile.get('target_position', ''),
        club_activity=student_profile.get('club_activity', '')
    )
    
    response = model.generate_content(prompt)
    result = json.loads(response.text)
    
    # キャッシュに保存
    save_to_cache(cache_key, result, ttl_days=30)
    
    return result
```

---

## 2. 敬語分析

### Gemini APIプロンプト

```python
KEIGO_ANALYSIS_PROMPT = """
あなたは日本語の敬語の専門家です。以下の面接の文字起こしを分析し、
敬語の使い方を詳細に評価してください。

# 文字起こし
{transcript}

# 分析ポイント
1. タメ口や俗語の検出
2. 尊敬語・謙譲語・丁寧語の適切な使用
3. 二重敬語や不自然な表現
4. ビジネスシーンにふさわしくない表現

# 出力形式
以下のJSON形式で出力してください:
{{
  "score": 75,  // 0-100点
  "overall_assessment": "全体的な評価コメント",
  "errors": [
    {{
      "text": "問題のある表現",
      "position": 45,  // 文字位置
      "issue": "問題の種類（タメ口/俗語/二重敬語など）",
      "suggestion": "正しい表現",
      "severity": "critical/warning/info",
      "explanation": "なぜ問題なのか、どう直すべきかの詳細説明"
    }}
  ],
  "strengths": [
    {{
      "text": "良い表現",
      "explanation": "なぜ良いのか"
    }}
  ],
  "recommendations": [
    "具体的な改善アドバイス"
  ],
  "correct_expressions_count": 15,
  "total_expressions_count": 20
}}
"""
```

### 実装例

```python
def analyze_keigo(transcript: str) -> dict:
    """Gemini APIで敬語分析"""
    
    # キャッシュチェック
    cache_key = generate_cache_key(transcript, "keigo")
    cached = get_from_cache(cache_key)
    if cached:
        return cached
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = KEIGO_ANALYSIS_PROMPT.format(transcript=transcript)
    
    response = model.generate_content(prompt)
    result = json.loads(response.text)
    
    # キャッシュに保存
    save_to_cache(cache_key, result, ttl_days=30)
    
    return result
```

---

## 3. 感情分析（ハイブリッド）

### テキストベース感情分析（Gemini API）

```python
TEXT_SENTIMENT_PROMPT = """
あなたは感情分析の専門家です。以下の面接の文字起こしから、
話者の感情状態を詳細に分析してください。

# 文字起こし
{transcript}

# 分析ポイント
1. 全体的な感情（ポジティブ/ニュートラル/ネガティブ）
2. 具体的な感情（自信/緊張/熱意/礼儀正しさなど）
3. 時系列での感情変化
4. 感情を示すキーフレーズ

# 出力形式
{{
  "overall_sentiment": "positive/neutral/negative/mixed",
  "confidence": 0.85,  // 0-1の確信度
  "sentiment_scores": {{
    "positive": 0.70,
    "neutral": 0.25,
    "negative": 0.05
  }},
  "emotions": {{
    "enthusiastic": 0.75,  // 熱意
    "nervous": 0.45,       // 緊張
    "confident": 0.55,     // 自信
    "polite": 0.90,        // 礼儀正しさ
    "humble": 0.65         // 謙虚さ
  }},
  "key_indicators": [
    {{
      "phrase": "感情を示すフレーズ",
      "emotion": "該当する感情",
      "intensity": 0.8,
      "explanation": "なぜこのフレーズがこの感情を示すか"
    }}
  ],
  "timeline": [
    {{
      "time_range": "0-30s",
      "dominant_emotion": "polite",
      "intensity": 0.9,
      "description": "開始時の挨拶。丁寧で礼儀正しい"
    }}
  ]
}}
"""
```

### 音声ベース感情推定（librosa）

```python
import librosa
import numpy as np

def analyze_voice_emotion(audio_path: str) -> dict:
    """音声特徴から感情を推定"""
    
    y, sr = librosa.load(audio_path)
    
    # ピッチ分析
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    pitch_mean = np.mean(pitches[pitches > 0])
    pitch_std = np.std(pitches[pitches > 0])
    
    # エネルギー分析
    rms = librosa.feature.rms(y=y)[0]
    energy_mean = np.mean(rms)
    energy_std = np.std(rms)
    
    # 話速
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    
    # 感情推定ルール（簡易版）
    emotion_scores = {
        "confident": 0.5,  # ベースライン
        "nervous": 0.5
    }
    
    # ピッチ変動が大きい → 緊張
    if pitch_std > 50:
        emotion_scores["nervous"] += 0.2
        emotion_scores["confident"] -= 0.2
    
    # 声量が安定 → 自信
    if energy_std < 0.02:
        emotion_scores["confident"] += 0.2
        emotion_scores["nervous"] -= 0.2
    
    # 話速が速い → 緊張
    if tempo > 140:
        emotion_scores["nervous"] += 0.15
        emotion_scores["confident"] -= 0.15
    
    # 正規化
    for key in emotion_scores:
        emotion_scores[key] = max(0.0, min(1.0, emotion_scores[key]))
    
    return {
        "emotion_from_voice": emotion_scores,
        "features": {
            "pitch_mean": float(pitch_mean),
            "pitch_variation": float(pitch_std),
            "volume_mean": float(energy_mean),
            "tempo": float(tempo)
        },
        "indicators": [
            f"ピッチ変動: {'大'if pitch_std > 50 else '小'}（緊張の{'高'if pitch_std > 50 else '低'}さ）",
            f"声量の安定性: {'高'if energy_std < 0.02 else '低'}",
            f"話速: {tempo:.0f}BPM"
        ]
    }
```

### 統合感情分析

```python
def analyze_sentiment_combined(transcript: str, audio_path: str) -> dict:
    """テキスト + 音声の統合感情分析"""
    
    # キャッシュチェック
    cache_key = generate_cache_key(transcript, "sentiment")
    cached = get_from_cache(cache_key)
    
    if not cached:
        # テキスト感情分析（Gemini）
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = TEXT_SENTIMENT_PROMPT.format(transcript=transcript)
        response = model.generate_content(prompt)
        text_analysis = json.loads(response.text)
        
        # キャッシュ保存
        save_to_cache(cache_key, text_analysis, ttl_days=30)
    else:
        text_analysis = cached
    
    # 音声感情分析（librosa）
    voice_analysis = analyze_voice_emotion(audio_path)
    
    # 統合評価
    combined = {
        "overall_sentiment": text_analysis["overall_sentiment"],
        "confidence": text_analysis["confidence"],
        "text_analysis": text_analysis,
        "voice_analysis": voice_analysis,
        "combined_assessment": {
            "summary": generate_combined_summary(text_analysis, voice_analysis),
            "strengths": [],
            "improvements": []
        }
    }
    
    # テキストと音声の整合性チェック
    text_confident = text_analysis["emotions"].get("confident", 0.5)
    voice_confident = voice_analysis["emotion_from_voice"].get("confident", 0.5)
    
    if abs(text_confident - voice_confident) > 0.3:
        combined["combined_assessment"]["improvements"].append(
            "言葉では自信がある様子ですが、声のトーンに緊張が表れています。深呼吸してリラックスしましょう。"
        )
    
    return combined

def generate_combined_summary(text_analysis: dict, voice_analysis: dict) -> str:
    """テキストと音声分析を統合したサマリー生成"""
    
    text_emotion = text_analysis["overall_sentiment"]
    voice_nervous = voice_analysis["emotion_from_voice"]["nervous"]
    
    if text_emotion == "positive" and voice_nervous < 0.4:
        return "前向きで自信のある印象を受けます。適度な緊張感も良いバランスです。"
    elif text_emotion == "positive" and voice_nervous > 0.6:
        return "内容は前向きですが、声から緊張が伝わります。深呼吸してリラックスしましょう。"
    else:
        return "全体的な印象を改善する余地があります。"
```

---

## 4. キャッシュ戦略

### キャッシュキー生成

```python
import hashlib

def generate_cache_key(text: str, analysis_type: str) -> str:
    """キャッシュキー生成"""
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return f"{analysis_type}:{text_hash}"
```

### キャッシュ操作

```python
from datetime import datetime, timedelta

def get_from_cache(cache_key: str) -> dict | None:
    """キャッシュから取得"""
    result = supabase.table('ai_analysis_cache').select('*').eq('cache_key', cache_key).execute()
    
    if result.data:
        cache = result.data[0]
        
        # 期限チェック
        if cache['expires_at'] and datetime.fromisoformat(cache['expires_at']) < datetime.now():
            return None
        
        # ヒットカウント更新
        supabase.table('ai_analysis_cache').update({
            'hit_count': cache['hit_count'] + 1,
            'last_used_at': datetime.now().isoformat()
        }).eq('id', cache['id']).execute()
        
        return cache['result']
    
    return None

def save_to_cache(cache_key: str, result: dict, analysis_type: str, ttl_days: int = 30) -> None:
    """キャッシュに保存"""
    expires_at = datetime.now() + timedelta(days=ttl_days)
    
    supabase.table('ai_analysis_cache').upsert({
        'cache_key': cache_key,
        'analysis_type': analysis_type,
        'input_text': result.get('input_text', ''),
        'input_hash': cache_key.split(':')[1],
        'result': result,
        'model_version': 'gemini-1.5-flash',
        'expires_at': expires_at.isoformat()
    }).execute()
```

---

## 5. エラーハンドリング

```python
import time
from typing import Callable

def retry_with_backoff(func: Callable, max_retries: int = 3) -> any:
    """リトライ処理"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            wait_time = 2 ** attempt  # 指数バックオフ
            print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
            time.sleep(wait_time)

def analyze_with_fallback(text: str, analysis_type: str) -> dict:
    """フォールバック付き分析"""
    try:
        # Gemini API呼び出し
        return retry_with_backoff(lambda: call_gemini_api(text, analysis_type))
    
    except Exception as e:
        print(f"Gemini API failed: {e}")
        
        # フォールバック: シンプルなルールベース分析
        if analysis_type == "keigo":
            return simple_keigo_check(text)
        elif analysis_type == "sentiment":
            return simple_sentiment_analysis(text)
        else:
            raise
```

---

## 6. コスト管理

### API使用量の監視

```python
def log_api_usage(analysis_type: str, token_count: int, cost: float) -> None:
    """API使用量をログ"""
    # 使用量テーブルに記録（将来実装）
    pass

def check_daily_limit() -> bool:
    """日次制限チェック"""
    # Gemini無料枠: 1500 requests/day
    # 実装は省略
    return True
```

### 最適化のポイント

1. **キャッシュ活用**: 同じテキストは再分析しない（30日TTL）
2. **バッチ処理**: 可能な限りまとめて処理
3. **プロンプト最適化**: トークン数を削減
4. **フォールバック**: API制限時はルールベースに切り替え

---

## 7. テスト

### ユニットテスト例

```python
def test_keigo_analysis():
    """敬語分析のテスト"""
    text = "はい、そうっすね。マジでやばいと思いました。"
    result = analyze_keigo(text)
    
    assert result["score"] < 60
    assert len(result["errors"]) >= 2
    assert any(e["text"] == "っす" for e in result["errors"])
    assert any(e["text"] == "マジで" for e in result["errors"])

def test_sentiment_analysis():
    """感情分析のテスト"""
    text = "はい、本日はよろしくお願いいたします。非常に楽しみにしておりました。"
    result = analyze_sentiment_text(text)
    
    assert result["overall_sentiment"] == "positive"
    assert result["emotions"]["enthusiastic"] > 0.6
```
