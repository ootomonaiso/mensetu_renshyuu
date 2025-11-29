"""
AI 分析サービス (Gemini API)
"""
import google.generativeai as genai
import os
import json
import logging
from typing import Dict, Any, List
import time

logger = logging.getLogger(__name__)

# Gemini API 初期化
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if GEMINI_API_KEY and GEMINI_API_KEY != "your_api_key_here":
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API 設定完了")
else:
    logger.warning("GEMINI_API_KEY が設定されていません。AI 分析はルールベースで動作します。")


def analyze_with_gemini(transcript: str, audio_features: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Gemini API で面接内容を分析（文字起こしテキストのみ使用）
    
    Args:
        transcript: 文字起こしテキスト
        audio_features: 音響分析結果（オプション、プロンプトの参考情報として使用）
    
    Returns:
        {
            "keywords": ["志望動機", "強み", ...],
            "keigo_feedback": "敬語の使い方について...",
            "confidence_score": 75,  # 0-100
            "nervousness_score": 40,  # 0-100
            "overall_impression": "全体的な印象..."
        }
    """
    # Gemini API が設定されていない場合はルールベース分析
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_api_key_here":
        logger.info("ルールベース分析を実行")
        return _analyze_rule_based(transcript, audio_features)
    
    try:
        # Gemini モデル
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # プロンプト作成（文字起こしテキストのみ使用）
        audio_context = ""
        if audio_features:
            audio_context = f"""

## 音響データ（参考情報）
- 話速: {audio_features.get('speech_rate', 0)} 文字/分
- 平均音量: {audio_features.get('average_volume', 0)} dB
- ポーズ回数: {audio_features.get('pause_count', 0)} 回
"""
        
        prompt = f"""
あなたは就職面接のプロフェッショナルな評価者です。以下の面接の文字起こしを分析してください。

## 文字起こし
{transcript[:4000]}  # 4000文字まで{audio_context}

## 分析項目
1. **キーワード**: 面接で言及された重要なキーワードを5〜10個抽出してください
2. **敬語チェック**: 敬語の使い方について、問題があれば具体的に指摘してください
3. **自信度**: 話し方から推測される自信のレベルを0〜100で評価してください
4. **緊張度**: 緊張しているレベルを0〜100で評価してください
5. **全体印象**: 面接官の視点から、この応答者の印象を簡潔にまとめてください

**JSON形式で回答してください:**
{{
  "keywords": ["キーワード1", "キーワード2", ...],
  "keigo_feedback": "敬語に関するフィードバック",
  "confidence_score": 0-100の数値,
  "nervousness_score": 0-100の数値,
  "overall_impression": "全体的な印象"
}}
"""
        
        # API 呼び出し (リトライ付き)
        for attempt in range(3):
            try:
                response = model.generate_content(prompt)
                
                # JSON パース
                result_text = response.text.strip()
                
                # Markdown のコードブロックを除去
                if result_text.startswith("```json"):
                    result_text = result_text[7:]
                if result_text.startswith("```"):
                    result_text = result_text[3:]
                if result_text.endswith("```"):
                    result_text = result_text[:-3]
                
                result_text = result_text.strip()
                
                analysis = json.loads(result_text)
                
                logger.info(f"Gemini 分析完了: キーワード={len(analysis.get('keywords', []))}個")
                return analysis
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON パースエラー (試行 {attempt + 1}/3): {str(e)}")
                if attempt == 2:
                    # 最終試行失敗時はルールベースにフォールバック
                    logger.error("Gemini API の応答が不正なため、ルールベース分析に切り替えます")
                    return _analyze_rule_based(transcript, audio_features)
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Gemini API エラー (試行 {attempt + 1}/3): {str(e)}")
                if attempt == 2:
                    return _analyze_rule_based(transcript, audio_features)
                time.sleep(2)
        
    except Exception as e:
        logger.error(f"AI 分析エラー: {str(e)}", exc_info=True)
        return _analyze_rule_based(transcript, audio_features)


def _analyze_rule_based(transcript: str, audio_features: Dict[str, Any]) -> Dict[str, Any]:
    """
    ルールベースの簡易分析 (Gemini API が使えない場合)
    
    Args:
        transcript: 文字起こしテキスト
        audio_features: 音響分析結果
    
    Returns:
        分析結果
    """
    logger.info("ルールベース分析を実行中...")
    
    # キーワード抽出 (頻出語)
    keywords = _extract_keywords_simple(transcript)
    
    # 敬語チェック (簡易)
    keigo_feedback = _check_keigo_simple(transcript)
    
    # 自信度・緊張度 (音響データから推定)
    confidence_score = _estimate_confidence(audio_features)
    nervousness_score = _estimate_nervousness(audio_features)
    
    # 全体印象
    overall_impression = _generate_impression(transcript, audio_features)
    
    return {
        "keywords": keywords,
        "keigo_feedback": keigo_feedback,
        "confidence_score": confidence_score,
        "nervousness_score": nervousness_score,
        "overall_impression": overall_impression
    }


def _extract_keywords_simple(text: str) -> List[str]:
    """簡易キーワード抽出"""
    # よくある面接キーワード
    common_keywords = [
        "志望動機", "強み", "弱み", "経験", "スキル",
        "目標", "チーム", "リーダーシップ", "課題", "解決",
        "学習", "成長", "貢献", "やりがい", "挑戦"
    ]
    
    found_keywords = [kw for kw in common_keywords if kw in text]
    
    return found_keywords[:10] if found_keywords else ["キーワードが検出されませんでした"]


def _check_keigo_simple(text: str) -> str:
    """簡易敬語チェック"""
    issues = []
    
    # NG パターン
    if "だ。" in text or "である。" in text:
        issues.append("「だ・である」調が使われています。「です・ます」調に統一しましょう。")
    
    if "ら抜き" in text or "れる" in text:
        issues.append("ら抜き言葉に注意してください。")
    
    if len(issues) == 0:
        return "敬語の使い方は概ね適切です。"
    
    return "\\n".join(issues)


def _estimate_confidence(audio_features: Dict[str, Any]) -> int:
    """自信度を推定 (音量とポーズから)"""
    volume = audio_features.get("average_volume", -30)
    pauses = audio_features.get("pause_count", 0)
    
    # 音量が大きく、ポーズが少ないほど自信がある
    confidence = 50  # ベースライン
    
    if volume > -20:
        confidence += 20
    elif volume > -30:
        confidence += 10
    
    if pauses < 5:
        confidence += 15
    elif pauses < 10:
        confidence += 5
    
    return min(100, max(0, confidence))


def _estimate_nervousness(audio_features: Dict[str, Any]) -> int:
    """緊張度を推定 (ピッチのばらつきとポーズから)"""
    pitch_variance = audio_features.get("pitch_variance", 0)
    pauses = audio_features.get("pause_count", 0)
    
    # ピッチのばらつきが大きく、ポーズが多いほど緊張している
    nervousness = 30  # ベースライン
    
    if pitch_variance > 50:
        nervousness += 25
    elif pitch_variance > 30:
        nervousness += 15
    
    if pauses > 10:
        nervousness += 20
    elif pauses > 5:
        nervousness += 10
    
    return min(100, max(0, nervousness))


def _generate_impression(transcript: str, audio_features: Dict[str, Any]) -> str:
    """全体印象を生成"""
    char_count = len(transcript)
    pauses = audio_features.get("pause_count", 0)
    
    impressions = []
    
    if char_count > 500:
        impressions.append("十分な内容を話しています。")
    else:
        impressions.append("もう少し詳しく説明できると良いでしょう。")
    
    if pauses < 5:
        impressions.append("スムーズに話せています。")
    elif pauses > 15:
        impressions.append("少しポーズが多めです。リラックスして話しましょう。")
    
    return " ".join(impressions)
