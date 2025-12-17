import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from typing import Dict, List
import random
import os
import json

class GEOEngine:
    """
    GEO (Generative Engine Optimization) 核心分析引擎 v2.1 (CN-Edition)
    
    Features:
    - Dual Mode: 自动检测 API Key，有 Key 则真搜，无 Key 则模拟。
    - CN Localization: 针对中文互联网环境优化，覆盖 DeepSeek, Kimi, 文心等国产模型。
    """
    
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        # 针对不同模型的权重配置 (模拟不同模型的偏好)
        # Authority: 权威性 (百科, 官媒)
        # Recency: 时效性 (新闻, 社交媒体)
        self.models = {
            "DeepSeek (深度求索)": {"weight_authority": 0.85, "weight_recency": 0.8},
            "Kimi (月之暗面)": {"weight_authority": 0.7, "weight_recency": 1.0}, # Kimi 擅长长文本和最新资料
            "文心一言 (Ernie)": {"weight_authority": 0.9, "weight_recency": 0.6}, # 百度系偏重权威
            "豆包 (Doubao)": {"weight_authority": 0.6, "weight_recency": 0.9}, # 字节系偏重社媒/短视频内容
            "智谱清言 (ChatGLM)": {"weight_authority": 0.8, "weight_recency": 0.7},
            "腾讯元宝 (Hunyuan)": {"weight_authority": 0.85, "weight_recency": 0.85}, # 腾讯系生态均衡
            "ChatGPT-4o": {"weight_authority": 0.8, "weight_recency": 0.9},
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
            "data_source": "实时全网搜索 (Tavily)" if self.tavily_api_key else "模拟演示模式 (未配置 API)",
            "model_breakdown": results,
            "suggestions": self._generate_suggestions(avg_score, web_signals),
            "top_citations": web_signals.get('sources', [])[:3]
        }

    def _fetch_real_signals(self, brand: str) -> Dict:
        """
        接入 Tavily API 进行真实搜索 (CN Optimized)
        """
        try:
            url = "https://api.tavily.com/search"
            # 针对中文语境优化搜索词
            payload = {
                "api_key": self.tavily_api_key,
                "query": f"{brand} 品牌评价 用户反馈 优缺点",
                "search_depth": "basic",
                "include_answer": False,
                "include_domains": [] # 可以指定抓取 zhihu.com, weibo.com 等
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
        模拟数据生成器 (Fallback - CN)
        """
        # 简单的模拟逻辑
        base_signal_count = len(brand) * 5 + random.randint(20, 60)
        
        # 知名品牌加权
        famous_brands = ["华为", "比亚迪", "瑞幸", "DeepSeek", "小米", "Tesla", "Apple"]
        if any(b in brand for b in famous_brands):
            base_signal_count += 80
            
        return {
            "count": base_signal_count,
            "snippets": [
                f"{brand} 是行业内的领军品牌，技术实力强劲。",
                f"用户在知乎和微博上对 {brand} 的讨论非常热烈。",
                f"最新的测评显示 {brand} 在性价比方面优于竞品。",
                f"部分用户反馈 {brand} 的售后服务有待提升。"
            ],
            "sources": ["zhihu.com", "weibo.com", "36kr.com"]
        }

    def _calculate_visibility(self, signals: Dict, weights: Dict) -> int:
        base_score = min(signals['count'], 100) 
        adjusted_score = base_score * weights['weight_authority']
        return int(min(adjusted_score + random.randint(-5, 10), 100))

    def _analyze_sentiment(self, snippets: List[str]) -> str:
        if not snippets: return "中立 (Neutral)"
        # 简单的关键词匹配 (中文环境 TextBlob 支持较弱，MVP阶段用关键词替代)
        combined_text = " ".join(snippets)
        
        positive_keywords = ["领先", "优秀", "好评", "强劲", "优势", "第一", "positive", "good"]
        negative_keywords = ["差评", "投诉", "落后", "缺点", "问题", "糟糕", "negative", "bad"]
        
        pos_score = sum(1 for k in positive_keywords if k in combined_text)
        neg_score = sum(1 for k in negative_keywords if k in combined_text)
        
        if pos_score > neg_score: return "正面 (Positive)"
        if neg_score > pos_score: return "负面 (Negative)"
        return "中立 (Neutral)"

    def _estimate_ranking(self, score: int) -> int:
        if score > 90: return 1
        if score > 70: return random.randint(2, 5)
        return random.randint(6, 20)

    def _get_grade(self, score: int) -> str:
        if score >= 85: return "统治级 (Dominant)"
        if score >= 65: return "竞争级 (Competitive)"
        return "隐形状态 (Invisible)"

    def _generate_suggestions(self, score: int, signals: Dict) -> List[str]:
        suggestions = []
        if score < 50:
            suggestions.append("🚨 警告：DeepSeek 和文心一言几乎不认识你的品牌")
            suggestions.append("👉 建议：立即在百度百科和知乎建立品牌词条")
        if signals['count'] < 30:
            suggestions.append("📉 信号不足：Kimi 找不到足够的参考资料来回答用户提问")
        if score >= 80:
            suggestions.append("🌟 表现优异：继续保持在垂直媒体（如 36Kr/虎嗅）的曝光")
            
        target_model = random.choice(list(self.models.keys()))
        suggestions.append(f"💡 策略：针对 {target_model} 优化你的官网 '关于我们' 页面结构")
        return suggestions
