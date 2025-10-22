"""
Celery Background Tasks for Market Insight AI Bot
Handles: Data collection, analysis, alerts, and scheduled jobs
"""

from celery import Celery
from celery.schedules import crontab
import os
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from openai import OpenAI
import redis
import json
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ Celery Configuration ============
celery_app = Celery(
    'market_insight_tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# ============ Database & Cache ============
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost/marketdb')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# OpenAI Client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# ============ Helper Functions ============

def get_active_companies() -> List[Dict]:
    """Fetch all active companies from database"""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, ticker, name FROM companies WHERE is_active = true"
        ))
        return [{"id": str(row[0]), "ticker": row[1], "name": row[2]} for row in result]

def store_market_data(company_id: str, ticker: str, data: pd.DataFrame):
    """Store market data in database"""
    try:
        with engine.connect() as conn:
            for date, row in data.iterrows():
                conn.execute(text("""
                    INSERT INTO market_data 
                    (company_id, date, open_price, close_price, high_price, low_price, volume, adjusted_close)
                    VALUES (:company_id, :date, :open, :close, :high, :low, :volume, :adj_close)
                    ON CONFLICT (company_id, date) DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        close_price = EXCLUDED.close_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        volume = EXCLUDED.volume,
                        adjusted_close = EXCLUDED.adjusted_close
                """), {
                    'company_id': company_id,
                    'date': date.date(),
                    'open': float(row['Open']),
                    'close': float(row['Close']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'volume': int(row['Volume']),
                    'adj_close': float(row['Close'])  # Simplified
                })
            conn.commit()
        logger.info(f"Stored {len(data)} records for {ticker}")
    except Exception as e:
        logger.error(f"Error storing data for {ticker}: {str(e)}")

# ============ Task 1: Daily Market Data Collection ============

@celery_app.task(name='tasks.collect_market_data', bind=True, max_retries=3)
def collect_market_data(self, ticker: str = None):
    """
    Collect daily market data for all active companies
    Runs every day at market close
    """
    try:
        companies = get_active_companies()
        
        if ticker:
            companies = [c for c in companies if c['ticker'] == ticker]
        
        success_count = 0
        failed_count = 0
        
        for company in companies:
            try:
                stock = yf.Ticker(company['ticker'])
                
                # Get last 5 days to ensure we catch any missed data
                hist = stock.history(period='5d')
                
                if not hist.empty:
                    store_market_data(company['id'], company['ticker'], hist)
                    success_count += 1
                else:
                    logger.warning(f"No data returned for {company['ticker']}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to collect data for {company['ticker']}: {str(e)}")
                failed_count += 1
                
        logger.info(f"Market data collection complete: {success_count} success, {failed_count} failed")
        return {"success": success_count, "failed": failed_count}
        
    except Exception as e:
        logger.error(f"Market data collection error: {str(e)}")
        raise self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes

# ============ Task 2: News Sentiment Analysis ============

@celery_app.task(name='tasks.analyze_news_sentiment', bind=True)
def analyze_news_sentiment(self, ticker: str, news_items: List[Dict]):
    """
    Analyze sentiment of news articles using GPT-4
    """
    try:
        if not news_items:
            return {"ticker": ticker, "analyzed": 0}
        
        # Batch analyze for efficiency
        articles_text = "\n\n".join([
            f"Title: {item['title']}\nSummary: {item.get('summary', '')}"
            for item in news_items[:10]  # Limit to 10 most recent
        ])
        
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{
                "role": "system",
                "content": """You are a financial sentiment analyst. Analyze news articles and provide:
                1. Overall sentiment score (-1.0 to 1.0)
                2. Sentiment label (positive/negative/neutral)
                3. Key themes or concerns
                
                Return JSON format:
                {"sentiment_score": 0.5, "sentiment_label": "positive", "key_themes": ["growth", "innovation"]}"""
            }, {
                "role": "user",
                "content": f"Analyze sentiment for {ticker}:\n\n{articles_text}"
            }],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        # Store in database
        with engine.connect() as conn:
            for item in news_items:
                conn.execute(text("""
                    INSERT INTO news_sentiment 
                    (company_id, title, source, url, published_at, sentiment_score, sentiment_label, summary)
                    SELECT id, :title, :source, :url, :published_at, :score, :label, :summary
                    FROM companies WHERE ticker = :ticker
                    ON CONFLICT DO NOTHING
                """), {
                    'ticker': ticker,
                    'title': item['title'],
                    'source': item.get('source', 'Unknown'),
                    'url': item.get('url', ''),
                    'published_at': item.get('published_at', datetime.now()),
                    'score': analysis['sentiment_score'],
                    'label': analysis['sentiment_label'],
                    'summary': item.get('summary', '')
                })
            conn.commit()
        
        logger.info(f"Analyzed {len(news_items)} news items for {ticker}")
        return {"ticker": ticker, "analyzed": len(news_items), "sentiment": analysis}
        
    except Exception as e:
        logger.error(f"Sentiment analysis error for {ticker}: {str(e)}")
        return {"ticker": ticker, "analyzed": 0, "error": str(e)}

# ============ Task 3: Price Alert Monitoring ============

@celery_app.task(name='tasks.check_price_alerts')
def check_price_alerts():
    """
    Check active price alerts and notify users
    Runs every 15 minutes during market hours
    """
    try:
        with engine.connect() as conn:
            # Get active alerts with current prices
            alerts = conn.execute(text("""
                SELECT 
                    a.id,
                    a.user_id,
                    a.alert_type,
                    a.condition_value,
                    c.ticker,
                    c.name,
                    u.email,
                    (SELECT close_price FROM market_data 
                     WHERE company_id = a.company_id 
                     ORDER BY date DESC LIMIT 1) as current_price
                FROM alerts a
                JOIN companies c ON a.company_id = c.id
                JOIN users u ON a.user_id = u.id
                WHERE a.is_active = true
                AND a.triggered_at IS NULL
            """))
            
            triggered_alerts = []
            
            for alert in alerts:
                alert_id, user_id, alert_type, condition_value, ticker, name, email, current_price = alert
                
                triggered = False
                
                if alert_type == 'price_above' and current_price >= condition_value:
                    triggered = True
                elif alert_type == 'price_below' and current_price <= condition_value:
                    triggered = True
                
                if triggered:
                    # Mark as triggered
                    conn.execute(text("""
                        UPDATE alerts 
                        SET triggered_at = CURRENT_TIMESTAMP, is_active = false
                        WHERE id = :alert_id
                    """), {'alert_id': alert_id})
                    
                    triggered_alerts.append({
                        'email': email,
                        'ticker': ticker,
                        'name': name,
                        'alert_type': alert_type,
                        'condition_value': condition_value,
                        'current_price': current_price
                    })
            
            conn.commit()
            
            # Send notifications (you would integrate with email service here)
            for alert_data in triggered_alerts:
                send_alert_notification.delay(alert_data)
            
            logger.info(f"Checked alerts: {len(triggered_alerts)} triggered")
            return {"checked": alerts.rowcount, "triggered": len(triggered_alerts)}
            
    except Exception as e:
        logger.error(f"Alert checking error: {str(e)}")
        return {"error": str(e)}

# ============ Task 4: Send Alert Notifications ============

@celery_app.task(name='tasks.send_alert_notification')
def send_alert_notification(alert_data: Dict):
    """
    Send email notification for triggered alert
    """
    try:
        # Here you would integrate with SendGrid, AWS SES, or SMTP
        logger.info(f"Alert notification: {alert_data['ticker']} - {alert_data['alert_type']}")
        
        # Example: Log to console (replace with actual email service)
        message = f"""
        Price Alert Triggered!
        
        Stock: {alert_data['name']} ({alert_data['ticker']})
        Alert Type: {alert_data['alert_type']}
        Target Price: ${alert_data['condition_value']}
        Current Price: ${alert_data['current_price']}
        
        View details: https://your-domain.com/dashboard
        """
        
        print(message)
        
        return {"status": "sent", "email": alert_data['email']}
        
    except Exception as e:
        logger.error(f"Notification error: {str(e)}")
        return {"status": "failed", "error": str(e)}

# ============ Task 5: Clean Expired Cache ============

@celery_app.task(name='tasks.cleanup_expired_cache')
def cleanup_expired_cache():
    """
    Remove expired AI analysis cache entries
    Runs daily at 2 AM
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                DELETE FROM ai_analysis_cache
                WHERE expires_at < CURRENT_TIMESTAMP
                RETURNING id
            """))
            deleted_count = result.rowcount
            conn.commit()
        
        logger.info(f"Cleaned {deleted_count} expired cache entries")
        return {"deleted": deleted_count}
        
    except Exception as e:
        logger.error(f"Cache cleanup error: {str(e)}")
        return {"error": str(e)}

# ============ Task 6: Generate Daily Market Report ============

@celery_app.task(name='tasks.generate_daily_report')
def generate_daily_report():
    """
    Generate comprehensive daily market report using AI
    Runs daily at 5 PM (after market close)
    """
    try:
        # Get top movers
        with engine.connect() as conn:
            top_gainers = conn.execute(text("""
                SELECT ticker, name, 
                       (SELECT close_price FROM market_data WHERE company_id = c.id ORDER BY date DESC LIMIT 1) as price,
                       (SELECT ROUND(((close_price - LAG(close_price) OVER (ORDER BY date)) / 
                                      LAG(close_price) OVER (ORDER BY date) * 100), 2)
                        FROM market_data WHERE company_id = c.id ORDER BY date DESC LIMIT 1) as change_pct
                FROM companies c
                ORDER BY change_pct DESC NULLS LAST
                LIMIT 5
            """)).fetchall()
        
        # Generate AI report
        movers_text = "\n".join([
            f"{ticker} ({name}): ${price:.2f} ({change_pct:+.2f}%)"
            for ticker, name, price, change_pct in top_gainers
        ])
        
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{
                "role": "system",
                "content": "You are a senior market analyst. Create a concise daily market summary."
            }, {
                "role": "user",
                "content": f"Generate daily market report for {datetime.now().date()}.\n\nTop Movers:\n{movers_text}"
            }],
            temperature=0.7,
            max_tokens=500
        )
        
        report = response.choices[0].message.content
        
        # Store in Redis for quick access
        redis_client.setex(
            f"daily_report:{datetime.now().date()}",
            86400,  # 24 hours
            report
        )
        
        logger.info("Daily report generated")
        return {"status": "success", "report_length": len(report)}
        
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        return {"error": str(e)}

# ============ Periodic Task Schedule ============

celery_app.conf.beat_schedule = {
    # Market data collection - Every day at 5 PM EST (after market close)
    'collect-market-data-daily': {
        'task': 'tasks.collect_market_data',
        'schedule': crontab(hour=22, minute=0),  # 22:00 UTC = 5 PM EST
    },
    
    # Price alert monitoring - Every 15 minutes during market hours
    'check-price-alerts': {
        'task': 'tasks.check_price_alerts',
        'schedule': crontab(minute='*/15', hour='14-21'),  # 9:30 AM - 4 PM EST
    },
    
    # Cache cleanup - Daily at 2 AM
    'cleanup-cache-daily': {
        'task': 'tasks.cleanup_expired_cache',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Daily report - Every day at 5:30 PM EST
    'generate-daily-report': {
        'task': 'tasks.generate_daily_report',
        'schedule': crontab(hour=22, minute=30),
    },
}

if __name__ == '__main__':
    celery_app.start()
