import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from typing import Dict, List
import random
import time

class GEOEngine:
    """
    GEO (Generative Engine Optimization) 核心分析引擎
    
    Current Stage:
    - [x] MVP 模拟算法
    - [ ] 真实 SERP/LLM 数据接入 (正在进行)
    """
    
    def __init__(self):
        # 模拟不同模型的搜索偏好
        self.models = {
            "ChatGPT-4o": {"weight_authority": 0.8, "weight_recency": 0.9},
            "Claude 3.5": {"weight_authority": 0.9, "weight_recency": 0.7},
            "Perplexity": {"weight_authority": 0.6, "weight_recency": 1.0}, # Perplexity 更注重实时性
        }
        
    def analyze_brand(self, brand_name: str, industry: str) -> Dict:
        """
        分析入口
        """
        # 1. 模拟真实搜索信号抓取 (Real-time Signal Fetching)
        # 在没有付费 API 的情况下，我们用 Requests 模拟一次基础的 Google/Bing 搜索特征提取
        # 注意：生产环境必须接入 SerpAPI 或 Tavily
        web_signals = self._fetch_web_signals(brand_name)
        
        results = {}
        total_score = 0
        
        for model_name, weights in self.models.items():
            # 2. 根据模型权重计算 "LLM 可见性"
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
            "model_breakdown": results,
            "suggestions": self._generate_suggestions(avg_score, web_signals)
        }

    def _fetch_web_signals(self, brand: str) -> Dict:
        """
        [模拟] 真实环境下这里会调用 Google Custom Search API 或 Tavily
        目前为了 MVP 演示，我们做一层 '伪-真实' 的数据模拟，
        但在代码结构上预留了真实 API 的位置。
        """
        # TODO: Replace with Tavily API call
        # response = tavily.search(query=brand)
        
        # 模拟：如果品牌名很长或很生僻，信号就少；如果是大品牌，信号就多
        # 这比纯随机更真实一点
        base_signal_count = len(brand) * 5 + random.randint(10, 50)
        if "Tesla" in brand or "Apple" in brand or "Coffee" in brand:
            base_signal_count += 80
            
        return {
            "count": base_signal_count,
            "snippets": [
                f"{brand} is leading the market in...",
                f"Users complain about {brand}'s pricing...",
                f"Review of {brand}: The best solution for..."
            ]
        }

    def _calculate_visibility(self, signals: Dict, weights: Dict) -> int:
        # 算法核心：信号数量 * 权威性权重 + 随机波动 (模拟 LLM 的随机性)
        base_score = min(signals['count'], 100) 
        adjusted_score = base_score * weights['weight_authority']
        return int(min(adjusted_score + random.randint(-5, 10), 100))

    def _analyze_sentiment(self, snippets: List[str]) -> str:
        # 使用 TextBlob 进行简单的 NLP 情感分析
        combined_text = " ".join(snippets)
        analysis = TextBlob(combined_text)
        polarity = analysis.sentiment.polarity # -1 to 1
        
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
            suggestions.append("👉 建议立即建立 Wikipedia 词条")
        if signals['count'] < 30:
            suggestions.append("📉 外部引用源太少，LLM 认为你不可信")
        if score >= 80:
            suggestions.append("🌟 维持现状，关注竞品动向")
            
        suggestions.append(f"💡 针对 {random.choice(list(self.models.keys()))} 优化你的 'About Us' 页面")
        return suggestions
