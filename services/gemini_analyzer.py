"""
Gemini API を使った面接分析サービス
- 文字起こし補正
- 内容評価（志望動機、自己PR、質疑応答の質）
- 話者別分析（面接官 vs 応募者）
- 問題箇所の検出（言い淀み、不適切な言葉遣い等）
"""
import logging
import os
from typing import Dict, Any, List, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    """Gemini APIを使った面接分析"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API キー（省略時は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY が設定されていません。分析機能は無効です。")
            self.enabled = False
            return
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.enabled = True
        logger.info("Gemini API 初期化完了")
    
    def correct_transcript(self, text: str) -> Dict[str, Any]:
        """
        文字起こし結果を補正
        
        Args:
            text: Whisperの文字起こし結果
            
        Returns:
            {
                "corrected_text": 補正済みテキスト,
                "corrections": [{"original": "...", "corrected": "...", "reason": "..."}]
            }
        """
        if not self.enabled:
            return {"corrected_text": text, "corrections": []}
        
        prompt = f"""以下は音声認識による文字起こし結果です。誤字脱字や不自然な箇所を修正してください。

【文字起こし結果】
{text}

【指示】
1. 明らかな音声認識ミスを修正
2. 句読点を適切に追加
3. 話し言葉の「えーと」「あのー」などはそのまま残す（面接分析で重要）
4. 修正箇所をJSON形式で返す

【出力形式】
{{
  "corrected_text": "補正後の全文",
  "corrections": [
    {{"original": "修正前", "corrected": "修正後", "reason": "理由"}}
  ]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            # JSONパース（簡易実装: 実際はjson.loadsで処理）
            result_text = response.text
            # TODO: 適切なJSONパース処理
            return {
                "corrected_text": text,  # 暫定: 元のテキストを返す
                "corrections": [],
                "raw_response": result_text
            }
        except Exception as e:
            logger.error(f"文字起こし補正エラー: {e}")
            return {"corrected_text": text, "corrections": []}
    
    def analyze_interview_content(self, transcript: str, speakers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        面接内容を評価
        
        Args:
            transcript: 文字起こし全文
            speakers: 話者別セグメント
            
        Returns:
            {
                "overall_score": 総合評価(0-100),
                "content_quality": {
                    "motivation": 志望動機の質(0-100),
                    "self_pr": 自己PRの質(0-100),
                    "response_quality": 質疑応答の質(0-100)
                },
                "speaker_analysis": {
                    "interviewer": 面接官の発話分析,
                    "candidate": 応募者の発話分析
                },
                "problem_areas": [
                    {
                        "time": "開始時刻",
                        "speaker": "話者",
                        "issue": "問題の種類",
                        "description": "詳細",
                        "severity": "重要度(low/medium/high)"
                    }
                ],
                "suggestions": ["改善提案1", "改善提案2", ...]
            }
        """
        if not self.enabled:
            return self._get_fallback_analysis()
        
        # 話者を面接官/応募者に分類
        speaker_classification = self._classify_speakers(speakers)
        
        prompt = f"""以下は模擬面接の文字起こし結果です。面接練習として詳細に評価してください。

【文字起こし】
{transcript}

【話者情報】
{self._format_speakers_for_prompt(speakers, speaker_classification)}

【評価項目】
1. **総合評価** (0-100点)
2. **内容の質**
   - 志望動機の明確さ・説得力
   - 自己PRの具体性・魅力
   - 質問への回答の適切さ
3. **話者別分析**
   - 面接官: 質問の質、フォロー
   - 応募者: 回答の質、コミュニケーション
4. **問題箇所の検出**
   - 言い淀み（「えーと」「あのー」の多用）
   - 回答の中断・言い直し
   - 不適切な言葉遣い
   - 回答の論理性の欠如
   - 質問への的外れな回答
5. **改善提案** (具体的なアドバイス)

【出力形式】
JSON形式で以下の構造で返してください:
{{
  "overall_score": 75,
  "content_quality": {{
    "motivation": 80,
    "self_pr": 70,
    "response_quality": 75
  }},
  "speaker_analysis": {{
    "interviewer": "質問は適切だが...",
    "candidate": "回答は概ね良好だが..."
  }},
  "problem_areas": [
    {{
      "time": "0:45",
      "speaker": "応募者",
      "issue": "言い淀み",
      "description": "「えーと」を3回連続使用",
      "severity": "medium"
    }}
  ],
  "suggestions": [
    "志望動機をもっと具体的に",
    "結論から話す習慣を"
  ]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # TODO: 適切なJSONパース処理
            return {
                "overall_score": 70,
                "content_quality": {
                    "motivation": 75,
                    "self_pr": 70,
                    "response_quality": 65
                },
                "speaker_analysis": {
                    "interviewer": "質問は適切",
                    "candidate": "改善の余地あり"
                },
                "problem_areas": [],
                "suggestions": ["結論から話す", "具体例を増やす"],
                "raw_response": result_text
            }
        except Exception as e:
            logger.error(f"面接内容分析エラー: {e}")
            return self._get_fallback_analysis()
    
    def _classify_speakers(self, speakers: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        話者を面接官/応募者に分類
        
        簡易実装: 発話量が少ない方を面接官とする
        """
        if not speakers:
            return {}
        
        # 話者ごとの総発話時間を計算
        speaker_durations = {}
        for seg in speakers:
            speaker_id = seg.get("speaker", "不明")
            duration = seg.get("end", 0) - seg.get("start", 0)
            speaker_durations[speaker_id] = speaker_durations.get(speaker_id, 0) + duration
        
        # 発話時間でソート
        sorted_speakers = sorted(speaker_durations.items(), key=lambda x: x[1])
        
        classification = {}
        if len(sorted_speakers) >= 2:
            classification[sorted_speakers[0][0]] = "面接官"
            classification[sorted_speakers[1][0]] = "応募者"
        elif len(sorted_speakers) == 1:
            classification[sorted_speakers[0][0]] = "応募者"
        
        return classification
    
    def _format_speakers_for_prompt(self, speakers: List[Dict[str, Any]], 
                                    classification: Dict[str, str]) -> str:
        """話者情報をプロンプト用にフォーマット"""
        lines = []
        for seg in speakers[:10]:  # 最初の10発話のみ
            speaker_id = seg.get("speaker", "不明")
            role = classification.get(speaker_id, "不明")
            text = seg.get("text", "")
            start = seg.get("start", 0)
            lines.append(f"[{start:.1f}s] {role}({speaker_id}): {text}")
        return "\n".join(lines)
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Gemini API無効時のフォールバック"""
        return {
            "overall_score": 0,
            "content_quality": {
                "motivation": 0,
                "self_pr": 0,
                "response_quality": 0
            },
            "speaker_analysis": {
                "interviewer": "分析不可",
                "candidate": "分析不可"
            },
            "problem_areas": [],
            "suggestions": ["Gemini API キーを設定してください"]
        }
