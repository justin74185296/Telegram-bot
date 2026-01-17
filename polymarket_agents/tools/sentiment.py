"""
Sentiment Analysis Tools
========================

Tools for analyzing sentiment from social media (X/Twitter) and news sources.
Currently using mock data for simulation mode.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

from crewai.tools import tool


# Mock sentiment data
MOCK_X_SENTIMENTS = {
    "bitcoin": {
        "overall_sentiment": 0.65,  # -1 to 1 scale
        "sentiment_label": "BULLISH",
        "tweet_volume_24h": 125000,
        "volume_change": 0.15,
        "top_keywords": ["ETF", "halving", "moon", "100k", "institutional"],
        "influencer_sentiment": 0.72,
        "retail_sentiment": 0.58,
    },
    "federal reserve": {
        "overall_sentiment": -0.15,
        "sentiment_label": "SLIGHTLY_BEARISH",
        "tweet_volume_24h": 45000,
        "volume_change": 0.22,
        "top_keywords": ["rates", "inflation", "hawkish", "cuts", "economy"],
        "influencer_sentiment": -0.20,
        "retail_sentiment": -0.10,
    },
    "trump": {
        "overall_sentiment": 0.25,
        "sentiment_label": "SLIGHTLY_BULLISH",
        "tweet_volume_24h": 320000,
        "volume_change": 0.45,
        "top_keywords": ["election", "polls", "rally", "debate", "2024"],
        "influencer_sentiment": 0.15,
        "retail_sentiment": 0.32,
    },
    "ethereum": {
        "overall_sentiment": 0.45,
        "sentiment_label": "MODERATELY_BULLISH",
        "tweet_volume_24h": 85000,
        "volume_change": 0.08,
        "top_keywords": ["ETH", "DeFi", "staking", "layer2", "upgrade"],
        "influencer_sentiment": 0.52,
        "retail_sentiment": 0.40,
    },
}

MOCK_NEWS = {
    "bitcoin": [
        {
            "title": "Bitcoin ETF Sees Record Inflows as Institutional Interest Grows",
            "source": "CoinDesk",
            "published": (datetime.now() - timedelta(hours=2)).isoformat(),
            "sentiment": 0.8,
            "relevance": 0.95,
            "summary": "BlackRock's Bitcoin ETF recorded $500M in daily inflows, signaling strong institutional demand.",
        },
        {
            "title": "Analysts Predict Bitcoin Could Hit New ATH Before Halving",
            "source": "Bloomberg Crypto",
            "published": (datetime.now() - timedelta(hours=8)).isoformat(),
            "sentiment": 0.7,
            "relevance": 0.88,
            "summary": "Multiple analysts suggest Bitcoin may reach new all-time highs driven by ETF demand and upcoming halving.",
        },
        {
            "title": "Bitcoin Mining Difficulty Reaches Record High",
            "source": "The Block",
            "published": (datetime.now() - timedelta(hours=12)).isoformat(),
            "sentiment": 0.3,
            "relevance": 0.72,
            "summary": "Mining difficulty adjustment shows network health but concerns about miner profitability emerge.",
        },
    ],
    "federal reserve": [
        {
            "title": "Fed Officials Signal Patience on Rate Cuts",
            "source": "Wall Street Journal",
            "published": (datetime.now() - timedelta(hours=4)).isoformat(),
            "sentiment": -0.3,
            "relevance": 0.98,
            "summary": "Federal Reserve officials indicate they need more confidence inflation is under control before cutting rates.",
        },
        {
            "title": "Economic Data Supports Fed's Cautious Approach",
            "source": "Reuters",
            "published": (datetime.now() - timedelta(hours=6)).isoformat(),
            "sentiment": 0.1,
            "relevance": 0.85,
            "summary": "Latest employment and inflation data suggest the Fed's wait-and-see approach may continue.",
        },
    ],
    "trump": [
        {
            "title": "Trump Leads in Key Swing State Polls",
            "source": "RealClearPolitics",
            "published": (datetime.now() - timedelta(hours=3)).isoformat(),
            "sentiment": 0.6,
            "relevance": 0.95,
            "summary": "New polling shows Trump with narrow leads in Pennsylvania, Michigan, and Wisconsin.",
        },
        {
            "title": "Campaign Focuses on Economic Message",
            "source": "Politico",
            "published": (datetime.now() - timedelta(hours=10)).isoformat(),
            "sentiment": 0.4,
            "relevance": 0.78,
            "summary": "Trump campaign emphasizes inflation and economy in latest advertising push.",
        },
    ],
    "ethereum": [
        {
            "title": "Ethereum Layer 2 Solutions See Record Activity",
            "source": "CoinTelegraph",
            "published": (datetime.now() - timedelta(hours=5)).isoformat(),
            "sentiment": 0.6,
            "relevance": 0.85,
            "summary": "Arbitrum and Optimism record highest transaction volumes as scaling solutions gain traction.",
        },
        {
            "title": "Ethereum Staking Yields Remain Attractive",
            "source": "Decrypt",
            "published": (datetime.now() - timedelta(hours=14)).isoformat(),
            "sentiment": 0.5,
            "relevance": 0.75,
            "summary": "Staking rewards continue to draw institutional interest to Ethereum ecosystem.",
        },
    ],
}


def _find_matching_key(keywords: str) -> str:
    """Find the best matching key in mock data based on keywords."""
    keywords_lower = keywords.lower()
    
    for key in MOCK_X_SENTIMENTS.keys():
        if key in keywords_lower:
            return key
    
    # Default to a random key if no match
    return random.choice(list(MOCK_X_SENTIMENTS.keys()))


@tool("Search X/Twitter Sentiment")
def search_x_sentiment(event_keywords: str) -> str:
    """
    Search and analyze sentiment from X (formerly Twitter) posts related to given keywords.
    
    Args:
        event_keywords: Keywords to search for sentiment analysis (e.g., "bitcoin", "federal reserve")
        
    Returns:
        JSON string containing sentiment analysis including overall sentiment, volume, and key influencer opinions
    """
    # Find matching mock data
    matching_key = _find_matching_key(event_keywords)
    base_sentiment = MOCK_X_SENTIMENTS[matching_key].copy()
    
    # Add some randomization to simulate real-time changes
    variation = random.uniform(-0.1, 0.1)
    base_sentiment["overall_sentiment"] = round(
        max(-1, min(1, base_sentiment["overall_sentiment"] + variation)), 3
    )
    
    # Update label based on sentiment
    sentiment = base_sentiment["overall_sentiment"]
    if sentiment > 0.5:
        base_sentiment["sentiment_label"] = "BULLISH"
    elif sentiment > 0.2:
        base_sentiment["sentiment_label"] = "SLIGHTLY_BULLISH"
    elif sentiment > -0.2:
        base_sentiment["sentiment_label"] = "NEUTRAL"
    elif sentiment > -0.5:
        base_sentiment["sentiment_label"] = "SLIGHTLY_BEARISH"
    else:
        base_sentiment["sentiment_label"] = "BEARISH"
    
    # Generate sample tweets
    sample_tweets = _generate_sample_tweets(matching_key, sentiment)
    
    result = {
        "search_query": event_keywords,
        "timestamp": datetime.now().isoformat(),
        "sentiment_analysis": base_sentiment,
        "sample_tweets": sample_tweets,
        "confidence": round(random.uniform(0.75, 0.95), 2),
        "data_quality": "MOCK_DATA",
        "recommendation": _generate_sentiment_recommendation(sentiment),
    }
    
    return json.dumps(result, indent=2)


def _generate_sample_tweets(topic: str, sentiment: float) -> List[Dict[str, Any]]:
    """Generate sample tweets based on topic and sentiment."""
    bullish_templates = [
        f"🚀 {topic.title()} looking very strong! Expecting big moves soon. #bullish",
        f"Just increased my position in {topic}. The setup is perfect.",
        f"Everyone sleeping on {topic} right now. This is the opportunity of a lifetime.",
    ]
    
    bearish_templates = [
        f"⚠️ Be careful with {topic}. Seeing some concerning signs.",
        f"Reducing exposure to {topic}. Risk/reward not favorable here.",
        f"The {topic} hype is overblown. Time for a reality check.",
    ]
    
    neutral_templates = [
        f"Watching {topic} closely. Could go either way from here.",
        f"Interesting developments in {topic}. Need more data before making moves.",
        f"Mixed signals on {topic}. Staying on the sidelines for now.",
    ]
    
    tweets = []
    if sentiment > 0.3:
        templates = bullish_templates + neutral_templates[:1]
    elif sentiment < -0.3:
        templates = bearish_templates + neutral_templates[:1]
    else:
        templates = neutral_templates + bullish_templates[:1] + bearish_templates[:1]
    
    for i, template in enumerate(templates[:3]):
        tweets.append({
            "text": template,
            "engagement": random.randint(100, 10000),
            "author_followers": random.randint(1000, 500000),
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
        })
    
    return tweets


def _generate_sentiment_recommendation(sentiment: float) -> str:
    """Generate trading recommendation based on sentiment."""
    if sentiment > 0.6:
        return "Strong bullish sentiment suggests positive momentum. Consider long positions."
    elif sentiment > 0.3:
        return "Moderately bullish sentiment. Market favors upside but exercise caution."
    elif sentiment > -0.3:
        return "Neutral sentiment. No clear directional bias from social media."
    elif sentiment > -0.6:
        return "Moderately bearish sentiment. Consider defensive positions or shorts."
    else:
        return "Strong bearish sentiment. High risk environment for long positions."


@tool("Search News")
def web_search_news(event: str) -> str:
    """
    Search and aggregate news articles related to a specific event or topic.
    
    Args:
        event: The event or topic to search news for
        
    Returns:
        JSON string containing news articles with summaries, sentiment, and relevance scores
    """
    # Find matching mock data
    matching_key = _find_matching_key(event)
    news_items = MOCK_NEWS.get(matching_key, [])
    
    if not news_items:
        # Generate generic news if no match
        news_items = [
            {
                "title": f"Latest Developments in {event.title()}",
                "source": "General News",
                "published": datetime.now().isoformat(),
                "sentiment": random.uniform(-0.3, 0.3),
                "relevance": 0.7,
                "summary": f"Recent updates regarding {event} show mixed signals for market participants.",
            }
        ]
    
    # Calculate aggregate metrics
    avg_sentiment = sum(n["sentiment"] for n in news_items) / len(news_items)
    avg_relevance = sum(n["relevance"] for n in news_items) / len(news_items)
    
    result = {
        "search_query": event,
        "timestamp": datetime.now().isoformat(),
        "total_articles": len(news_items),
        "aggregate_metrics": {
            "average_sentiment": round(avg_sentiment, 3),
            "average_relevance": round(avg_relevance, 3),
            "sentiment_label": "POSITIVE" if avg_sentiment > 0.2 else "NEGATIVE" if avg_sentiment < -0.2 else "NEUTRAL",
        },
        "articles": news_items,
        "key_themes": _extract_key_themes(news_items),
        "data_quality": "MOCK_DATA",
    }
    
    return json.dumps(result, indent=2)


def _extract_key_themes(articles: List[Dict[str, Any]]) -> List[str]:
    """Extract key themes from articles."""
    # In production, this would use NLP
    themes = []
    for article in articles:
        title_words = article["title"].lower().split()
        themes.extend([w for w in title_words if len(w) > 5])
    
    # Return unique themes
    return list(set(themes))[:5]


@tool("Analyze Combined Sentiment")
def analyze_combined_sentiment(market_keywords: str) -> str:
    """
    Perform comprehensive sentiment analysis combining social media and news sources.
    
    Args:
        market_keywords: Keywords related to the market being analyzed
        
    Returns:
        JSON string with comprehensive sentiment analysis and trading implications
    """
    # Get both sentiment sources
    x_sentiment_raw = search_x_sentiment(market_keywords)
    news_raw = web_search_news(market_keywords)
    
    x_sentiment = json.loads(x_sentiment_raw)
    news = json.loads(news_raw)
    
    # Combine sentiments with weighting
    social_sentiment = x_sentiment["sentiment_analysis"]["overall_sentiment"]
    news_sentiment = news["aggregate_metrics"]["average_sentiment"]
    
    # Weighted average (news slightly higher weight for reliability)
    combined_sentiment = (social_sentiment * 0.4 + news_sentiment * 0.6)
    
    # Calculate sentiment momentum (difference between sources)
    sentiment_divergence = abs(social_sentiment - news_sentiment)
    
    result = {
        "market_keywords": market_keywords,
        "timestamp": datetime.now().isoformat(),
        "combined_analysis": {
            "combined_sentiment_score": round(combined_sentiment, 3),
            "social_media_sentiment": round(social_sentiment, 3),
            "news_sentiment": round(news_sentiment, 3),
            "sentiment_divergence": round(sentiment_divergence, 3),
            "confidence_level": "HIGH" if sentiment_divergence < 0.2 else "MEDIUM" if sentiment_divergence < 0.4 else "LOW",
        },
        "interpretation": _interpret_combined_sentiment(combined_sentiment, sentiment_divergence),
        "trading_implications": _generate_trading_implications(combined_sentiment, sentiment_divergence),
        "risk_factors": _identify_sentiment_risks(social_sentiment, news_sentiment),
    }
    
    return json.dumps(result, indent=2)


def _interpret_combined_sentiment(combined: float, divergence: float) -> str:
    """Interpret the combined sentiment analysis."""
    direction = "bullish" if combined > 0 else "bearish" if combined < 0 else "neutral"
    strength = "strongly" if abs(combined) > 0.5 else "moderately" if abs(combined) > 0.2 else "slightly"
    
    confidence = "high confidence" if divergence < 0.2 else "moderate confidence" if divergence < 0.4 else "low confidence"
    
    return f"Market sentiment is {strength} {direction} with {confidence}."


def _generate_trading_implications(combined: float, divergence: float) -> Dict[str, Any]:
    """Generate trading implications from sentiment analysis."""
    return {
        "suggested_bias": "LONG" if combined > 0.2 else "SHORT" if combined < -0.2 else "NEUTRAL",
        "position_size_modifier": 1.0 if divergence < 0.2 else 0.75 if divergence < 0.4 else 0.5,
        "entry_timing": "FAVORABLE" if abs(combined) > 0.3 and divergence < 0.3 else "WAIT",
        "contrarian_opportunity": divergence > 0.4,
    }


def _identify_sentiment_risks(social: float, news: float) -> List[str]:
    """Identify potential risks from sentiment analysis."""
    risks = []
    
    if abs(social) > 0.7:
        risks.append("Extreme social media sentiment may indicate crowded trade")
    
    if social > 0 and news < 0:
        risks.append("Social vs news sentiment divergence - potential fake news or manipulation")
    
    if abs(social - news) > 0.5:
        risks.append("Large sentiment divergence suggests high uncertainty")
    
    if not risks:
        risks.append("No significant sentiment-based risks identified")
    
    return risks
