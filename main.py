"""
Market Insight AI Bot - Production Backend
FastAPI + OpenAI + LangChain Integration
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv

# AI & Data Processing
from openai import AsyncOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import Pinecone as PineconeStore
from langchain_openai import OpenAIEmbeddings
import yfinance as yf
import pandas as pd
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

load_dotenv()

# ============ Configuration ============
class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/marketdb")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

settings = Settings()

# ============ FastAPI App ============
app = FastAPI(
    title="Market Insight AI API",
    version="2.0.0",
    description="Professional AI-powered market analysis platform"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Redis Cache
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# OpenAI Client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# ============ Data Models ============
class MarketQuery(BaseModel):
    query: str = Field(..., description="User's market analysis question")
    company: Optional[str] = Field(None, description="Company ticker symbol")
    competitors: Optional[List[str]] = Field(None, description="Competitor tickers")
    time_range: str = Field("1mo", description="Data time range: 1d, 5d, 1mo, 3mo, 1y")

class MarketAnalysisResponse(BaseModel):
    analysis: str
    insights: List[Dict[str, Any]]
    data: Dict[str, Any]
    confidence_score: float
    timestamp: datetime

class CompetitorAnalysis(BaseModel):
    company: str
    competitors: List[str]
    metrics: Dict[str, Any]

# ============ AI Prompt Engineering ============
class PromptTemplates:
    SYSTEM_PROMPT = """You are a senior market analyst with 15+ years of experience.
    Your expertise includes:
    - Financial statement analysis
    - Competitive intelligence
    - Market trend prediction
    - Risk assessment
    
    Provide insights that are:
    1. Data-driven and specific
    2. Actionable with clear recommendations
    3. Risk-aware with uncertainty quantification
    4. Industry-contextualized
    
    Format responses in JSON structure with:
    - Executive summary
    - Key insights (3-5 points)
    - Recommendations (prioritized)
    - Risk factors
    - Confidence level (0-100%)
    """
    
    MARKET_ANALYSIS = """Analyze the following market data:
    
    Company: {company}
    Time Period: {time_range}
    Current Price: ${current_price}
    Volume: {volume}
    Market Cap: ${market_cap}
    
    Historical Performance:
    {historical_data}
    
    Recent News Sentiment: {news_sentiment}
    
    User Question: {query}
    
    Provide comprehensive analysis covering:
    1. Price trend analysis
    2. Volume patterns
    3. Market sentiment
    4. Growth indicators
    5. Risk assessment
    """
    
    COMPETITOR_ANALYSIS = """Compare these companies in the market:
    
    Primary Company: {company}
    Competitors: {competitors}
    
    Metrics Comparison:
    {metrics_table}
    
    Market Share Data:
    {market_share}
    
    Analyze:
    1. Competitive positioning
    2. Strengths/Weaknesses
    3. Market opportunities
    4. Threats and risks
    5. Strategic recommendations
    """

# ============ Data Collection Services ============
class MarketDataService:
    """Real-time market data collection"""
    
    @staticmethod
    async def get_stock_data(ticker: str, period: str = "1mo") -> Dict[str, Any]:
        """Fetch real stock data from Yahoo Finance"""
        cache_key = f"stock:{ticker}:{period}"
        
        # Check cache first
        cached = redis_client.get(cache_key)
        if cached:
            return eval(cached)
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            info = stock.info
            
            data = {
                "ticker": ticker,
                "current_price": info.get("currentPrice", 0),
                "market_cap": info.get("marketCap", 0),
                "volume": info.get("volume", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "eps": info.get("trailingEps", 0),
                "revenue": info.get("totalRevenue", 0),
                "profit_margin": info.get("profitMargins", 0),
                "historical": hist.to_dict(),
                "52_week_high": info.get("fiftyTwoWeekHigh", 0),
                "52_week_low": info.get("fiftyTwoWeekLow", 0),
            }
            
            # Cache for 15 minutes
            redis_client.setex(cache_key, 900, str(data))
            return data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
    
    @staticmethod
    async def get_competitor_comparison(tickers: List[str]) -> pd.DataFrame:
        """Compare multiple companies"""
        data = []
        for ticker in tickers:
            stock_data = await MarketDataService.get_stock_data(ticker)
            data.append({
                "Company": ticker,
                "Price": stock_data["current_price"],
                "Market Cap": stock_data["market_cap"],
                "P/E Ratio": stock_data["pe_ratio"],
                "Profit Margin": stock_data["profit_margin"],
                "Revenue": stock_data["revenue"]
            })
        return pd.DataFrame(data)

# ============ AI Analysis Engine ============
class AIAnalysisEngine:
    """Advanced AI-powered analysis"""
    
    @staticmethod
    async def analyze_market(query: MarketQuery) -> MarketAnalysisResponse:
        """Main analysis function using GPT-4"""
        
        # 1. Collect real data
        stock_data = await MarketDataService.get_stock_data(
            query.company, 
            query.time_range
        )
        
        # 2. Prepare context for AI
        historical_summary = AIAnalysisEngine._summarize_historical_data(
            stock_data["historical"]
        )
        
        # 3. Build prompt
        analysis_prompt = PromptTemplates.MARKET_ANALYSIS.format(
            company=query.company,
            time_range=query.time_range,
            current_price=stock_data["current_price"],
            volume=stock_data["volume"],
            market_cap=stock_data["market_cap"],
            historical_data=historical_summary,
            news_sentiment="Positive (75%)",  # TODO: Integrate news API
            query=query.query
        )
        
        # 4. Call GPT-4 with structured output
        response = await openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": PromptTemplates.SYSTEM_PROMPT},
                {"role": "user", "content": analysis_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Lower for consistent analysis
        )
        
        analysis_result = eval(response.choices[0].message.content)
        
        return MarketAnalysisResponse(
            analysis=analysis_result.get("executive_summary", ""),
            insights=analysis_result.get("key_insights", []),
            data=stock_data,
            confidence_score=analysis_result.get("confidence_level", 0) / 100,
            timestamp=datetime.now()
        )
    
    @staticmethod
    def _summarize_historical_data(historical: Dict) -> str:
        """Convert historical data to readable summary"""
        if not historical or not historical.get("Close"):
            return "No historical data available"
        
        prices = list(historical["Close"].values())
        if len(prices) < 2:
            return f"Current price: ${prices[0]:.2f}"
        
        start_price = prices[0]
        end_price = prices[-1]
        change_pct = ((end_price - start_price) / start_price) * 100
        
        return f"""
        Start Price: ${start_price:.2f}
        End Price: ${end_price:.2f}
        Change: {change_pct:+.2f}%
        Trend: {'Upward' if change_pct > 0 else 'Downward'}
        """

# ============ API Endpoints ============

@app.get("/")
async def root():
    return {
        "message": "Market Insight AI API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.post("/api/v2/analyze", response_model=MarketAnalysisResponse)
async def analyze_market(query: MarketQuery):
    """
    Advanced market analysis endpoint
    
    Example:
    {
        "query": "Should I invest in AAPL?",
        "company": "AAPL",
        "time_range": "3mo"
    }
    """
    try:
        result = await AIAnalysisEngine.analyze_market(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/competitor-analysis")
async def compare_competitors(analysis: CompetitorAnalysis):
    """
    Compare company against competitors
    """
    try:
        tickers = [analysis.company] + analysis.competitors
        comparison_df = await MarketDataService.get_competitor_comparison(tickers)
        
        # AI-powered competitive analysis
        prompt = PromptTemplates.COMPETITOR_ANALYSIS.format(
            company=analysis.company,
            competitors=", ".join(analysis.competitors),
            metrics_table=comparison_df.to_string(),
            market_share="TODO: Integrate market share data"
        )
        
        response = await openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": PromptTemplates.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return {
            "comparison_data": comparison_df.to_dict(),
            "ai_analysis": eval(response.choices[0].message.content)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/market-data/{ticker}")
async def get_market_data(ticker: str, period: str = "1mo"):
    """Get raw market data for a company"""
    return await MarketDataService.get_stock_data(ticker, period)

@app.get("/api/v2/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "redis": redis_client.ping(),
        "timestamp": datetime.now().isoformat()
    }

# ============ Run Server ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
