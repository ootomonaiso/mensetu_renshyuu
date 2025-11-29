"""Gemini API クライアント（キーワード・敬語・感情分析）"""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.clients.supabase import get_supabase_client


class GeminiService:
    """Gemini API 統合サービス"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY が設定されていません")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_gemini(self, prompt: str) -> str:
        """Gemini API 呼び出し（リトライ付き）"""
        response = self.model.generate_content(prompt)
        return response.text
    
    def _get_cache(self, analysis_type: str, text: str) -> dict | None:
        """キャッシュから分析結果取得"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"{analysis_type}:{text_hash}"
        
        result = (
            self.supabase.table("ai_analysis_cache")
            .select("result")
            .eq("cache_key", cache_key)
            .single()
            .execute()
        )
        
        if result.data:
            return json.loads(result.data["result"])
        return None
    
    def _set_cache(self, analysis_type: str, text: str, result: dict) -> None:
        """キャッシュに分析結果保存"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"{analysis_type}:{text_hash}"
        
        self.supabase.table("ai_analysis_cache").upsert({
            "cache_key": cache_key,
            "analysis_type": analysis_type,
            "result": json.dumps(result, ensure_ascii=False),
        }).execute()
    
    def extract_keywords(self, transcript: str) -> list[str]:
        """キーワード抽出"""
        cached = self._get_cache("keywords", transcript)
        if cached:
            return cached.get("keywords", [])
        
        prompt = f"""
以下の面接発言から、重要なキーワードを5〜10個抽出してください。
JSON配列形式で返してください。

例: ["志望動機", "チームワーク", "課題解決"]

発言:
{transcript[:4000]}
"""
        try:
            response = self._call_gemini(prompt)
            # JSON解析（失敗時はフォールバック）
            keywords = json.loads(response.strip().replace("```json", "").replace("```", ""))
            result = {"keywords": keywords}
            self._set_cache("keywords", transcript, result)
            return keywords
        except Exception as e:
            print(f"キーワード抽出失敗: {e}")
            return ["（抽出失敗）"]
    
    def analyze_keigo(self, transcript: str) -> dict[str, Any]:
        """敬語分析"""
        cached = self._get_cache("keigo", transcript)
        if cached:
            return cached
        
        prompt = f"""
以下の面接発言について、敬語使用状況を分析してください。
JSON形式で以下の項目を返してください:
{{
  "score": 1〜5の評価,
  "issues": ["問題点1", "問題点2"],
  "suggestions": ["改善提案1", "改善提案2"]
}}

発言:
{transcript[:4000]}
"""
        try:
            response = self._call_gemini(prompt)
            result = json.loads(response.strip().replace("```json", "").replace("```", ""))
            self._set_cache("keigo", transcript, result)
            return result
        except Exception as e:
            print(f"敬語分析失敗: {e}")
            return {"score": 3, "issues": [], "suggestions": []}
    
    def analyze_sentiment(self, transcript: str) -> dict[str, Any]:
        """感情分析（自信・緊張・前向き度）"""
        cached = self._get_cache("sentiment", transcript)
        if cached:
            return cached
        
        prompt = f"""
以下の面接発言について、話者の感情状態を分析してください。
JSON形式で以下の項目を返してください（スコアは0.0〜1.0）:
{{
  "confidence": 自信度,
  "calmness": 落ち着き度,
  "positivity": 前向き度,
  "summary": "全体的な印象（30文字以内）"
}}

発言:
{transcript[:4000]}
"""
        try:
            response = self._call_gemini(prompt)
            result = json.loads(response.strip().replace("```json", "").replace("```", ""))
            self._set_cache("sentiment", transcript, result)
            return result
        except Exception as e:
            print(f"感情分析失敗: {e}")
            return {"confidence": 0.5, "calmness": 0.5, "positivity": 0.5, "summary": ""}
    
    def save_evaluation(self, session_id: str, transcript: str) -> None:
        """
        Gemini 評価結果を evaluations テーブルに保存
        """
        keywords = self.extract_keywords(transcript)
        keigo = self.analyze_keigo(transcript)
        sentiment = self.analyze_sentiment(transcript)
        
        self.supabase.table("evaluations").insert({
            "session_id": session_id,
            "evaluated_by": None,  # AI評価（教師評価は別途）
            "extracted_keywords": json.dumps(keywords, ensure_ascii=False),
            "keigo_analysis": json.dumps(keigo, ensure_ascii=False),
            "sentiment_analysis": json.dumps(sentiment, ensure_ascii=False),
        }).execute()
