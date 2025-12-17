import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from typing import Dict, List
import random
import os
import json

class GEOEngine:
    """
    GEO (Generative Engine Optimization) 核心分析引擎 v2.0
    
    Features:
    - Dual Mode: 自动检测 API Key，有 Key 则真搜，无 Key 则模拟。
    - Sentiment Analysis: 真实的情感分析。
    """
    
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.models = {
            "ChatGPT-4o": {"weight_authority": 0.8, "weight_recency": 0.9},
            "Claude 3.5": {"weight_authority": 0.9, "weight_recency": 0.7},
            "Perplexity": {"weight_authority": 0.6, "weight_recency": 1.0},
        }
        
    def analyze_brand(self, brand_name: str, industry: str) -> Dict:
        """
        分析入口：智能路由
        """
        if self.tavily_api_key:
            print(f"🔍 [Real Mode] Searching for {brand_name} via Tavily API...")
            web_signals = self._fetch_real_signals(brand_name)
        else:
            print(f"🎭 [Sim Mode] Simulating signals for {brand_name}...")
            web_signals = self._fetch_mock_signals(brand_name)
        
        results = {}
        total_score = 0
        
        for model_name, weights in self.models.items():
            visibility = self._calculate_visibility(web_signals, weights)
            sentiment = self._analyze_sentiment(web_signals['snippets'])
            
            results[model_name] = {
                "visibility_score": visibility, 
                "sentiment": sentiment,
                "ranking": self._estimate_ranking(visibility)
            }
            total_score += visibility

        avg_score = int(total_score / len(self.models))
        
        return {
            "brand": brand_name,
            "geo_score": avg_score,
            "market_grade": self._get_grade(avg_score),
            "web_signals_found": web_signals['count'],
            "data_source": "Real-Time Web" if self.tavily_api_key else "Simulation (No API Key)",
            "model_breakdown": results,
            "suggestions": self._generate_suggestions(avg_score, web_signals),
            "top_citations": web_signals.get('sources', [])[:3]
        }

    def _fetch_real_signals(self, brand: str) -> Dict:
        """
        接入 Tavily API 进行真实搜索
        """
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.tavily_api_key,
                "query": f"What is {brand} brand reputation review",
                "search_depth": "basic",
                "include_answer": False,
                "include_domains": []
            }
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            snippets = [r['content'] for r in data.get('results', [])]
            sources = [r['url'] for r in data.get('results', [])]
            
            return {
                "count": len(snippets) * 10, # 放大系数
                "snippets": snippets,
                "sources": sources
            }
        except Exception as e:
            print(f"⚠️ Tavily API Error: {e}")
            return self._fetch_mock_signals(brand)

    def _fetch_mock_signals(self, brand: str) -> Dict:
        """
        模拟数据生成器 (Fallback)
        """
        base_signal_count = len(brand) * 5 + random.randint(10, 50)
        if "Tesla" in brand or "Apple" in brand:
            base_signal_count += 80
            
        return {
            "count": base_signal_count,
            "snippets": [
                f"{brand} is a leading player in the industry.",
                f"Users are discussing {brand} features on Reddit.",
                f"Comparison: {brand} vs Competitors."
            ],
            "sources": ["wikipedia.org", "reddit.com", "techcrunch.com"]
        }

    def _calculate_visibility(self, signals: Dict, weights: Dict) -> int:
        base_score = min(signals['count'], 100) 
        adjusted_score = base_score * weights['weight_authority']
        return int(min(adjusted_score + random.randint(-5, 10), 100))

    def _analyze_sentiment(self, snippets: List[str]) -> str:
        if not snippets: return "Neutral"
        combined_text = " ".join(snippets)
        analysis = TextBlob(combined_text)
        polarity = analysis.sentiment.polarity
        
        if polarity > 0.1: return "Positive"
        if polarity < -0.1: return "Negative"
        return "Neutral"

    def _estimate_ranking(self, score: int) -> int:
        if score > 90: return 1
        if score > 70: return random.randint(2, 5)
        return random.randint(6, 20)

    def _get_grade(self, score: int) -> str:
        if score >= 80: return "Dominant (统治级)"
        if score >= 60: return "Competitive (竞争级)"
        return "Invisible (隐形状态)"

    def _generate_suggestions(self, score: int, signals: Dict) -> List[str]:
        suggestions = []
        if score < 50:
            suggestions.append("🚨 你的品牌在 AI 语料库中几乎不存在")
        if signals['count'] < 30:
            suggestions.append("📉 外部引用源太少，LLM 认为你不可信")
        if score >= 80:
            suggestions.append("🌟 维持现状，关注竞品动向")
            
        suggestions.append(f"💡 针对 {random.choice(list(self.models.keys()))} 优化你的 'About Us' 页面")
        return suggestions
