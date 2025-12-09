"""
Ollama を使用した日本語補正
"""
import ollama
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()


class TextCorrector:
    def __init__(self, model: str = None, host: str = None):
        """
        Args:
            model: Ollamaモデル名
            host: Ollama ホストURL
        """
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        # Ollama クライアント設定
        self.client = ollama.Client(host=self.host)
        
        print(f"Using Ollama model: {self.model} at {self.host}")
    
    def correct_text(self, text: str) -> str:
        """
        文字起こしテキストの日本語を補正
        
        Args:
            text: 補正対象テキスト
        
        Returns:
            補正済みテキスト
        """
        prompt = f"""以下の文字起こしテキストの日本語を補正してください。
誤字脱字、文法ミス、不自然な表現を修正してください。
元の意味を変えずに、より自然な日本語に修正してください。

【文字起こしテキスト】
{text}

【補正済みテキスト】
"""
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response["message"]["content"].strip()
        except Exception as e:
            print(f"Text correction error: {e}")
            return text  # エラー時は元のテキストを返す
    
    def check_keigo(self, text: str) -> Dict:
        """
        敬語・ビジネス表現のチェック
        
        Args:
            text: チェック対象テキスト
        
        Returns:
            評価結果
        """
        prompt = f"""以下の面接での発言について、敬語とビジネス表現の使用を評価してください。

【発言】
{text}

以下の項目について評価してください：
1. 敬語の適切性（尊敬語、謙譲語、丁寧語の使い分け）
2. ビジネス表現の適切性
3. 不適切な表現があれば指摘
4. 改善提案

評価は以下の形式で出力してください：
【評価点】0-100点
【良い点】
【改善点】
【改善例】
"""
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            result_text = response["message"]["content"]
            return self._parse_keigo_evaluation(result_text)
        except Exception as e:
            print(f"Keigo check error: {e}")
            return {
                "score": 0,
                "good_points": [],
                "improvements": [],
                "examples": []
            }
    
    def _parse_keigo_evaluation(self, text: str) -> Dict:
        """
        敬語評価結果をパース
        
        Args:
            text: Ollamaの出力テキスト
        
        Returns:
            パース済み評価結果
        """
        result = {
            "score": 70,  # デフォルト
            "good_points": [],
            "improvements": [],
            "examples": [],
            "raw_text": text
        }
        
        lines = text.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 評価点の抽出
            if "評価点" in line or "点数" in line:
                try:
                    import re
                    score_match = re.search(r'(\d+)', line)
                    if score_match:
                        result["score"] = int(score_match.group(1))
                except:
                    pass
            
            # セクション判定
            if "良い点" in line:
                current_section = "good_points"
            elif "改善点" in line:
                current_section = "improvements"
            elif "改善例" in line or "例" in line:
                current_section = "examples"
            elif line.startswith("-") or line.startswith("•") or line.startswith("・"):
                # 箇条書き項目
                item = line.lstrip("-•・ ").strip()
                if current_section and item:
                    result[current_section].append(item)
        
        return result
    
    def analyze_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        セグメントごとに日本語を補正
        
        Args:
            segments: 話者分離済みセグメント
        
        Returns:
            補正済みセグメント
        """
        corrected_segments = []
        
        for seg in segments:
            original_text = seg.get("text", "")
            
            # 短いテキストはスキップ
            if len(original_text.strip()) < 10:
                corrected_segments.append({
                    **seg,
                    "corrected_text": original_text
                })
                continue
            
            # 補正実行
            corrected_text = self.correct_text(original_text)
            
            corrected_segments.append({
                **seg,
                "corrected_text": corrected_text
            })
        
        return corrected_segments


if __name__ == "__main__":
    # テスト用
    try:
        corrector = TextCorrector()
        print("TextCorrector initialized successfully")
        
        # 簡単なテスト
        test_text = "えーと、私はですね、この会社に入りたいと思ってまして"
        corrected = corrector.correct_text(test_text)
        print(f"Original: {test_text}")
        print(f"Corrected: {corrected}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Ollama is running: ollama serve")
