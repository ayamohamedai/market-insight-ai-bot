# ⚡ Quick Start Guide - 5 Minutes to Your First Analysis

Get Market Insight AI Bot running in under 5 minutes!

---

## 🎯 Prerequisites Checklist

Before you start, make sure you have:

- [ ] **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- [ ] **Docker Desktop** installed ([Download](https://www.docker.com/products/docker-desktop))
- [ ] **Git** installed ([Download](https://git-scm.com/downloads))

**Cost:** ~$0.50 for testing (OpenAI credits needed)

---

## 🚀 Installation Steps

### Step 1: Clone the Project (30 seconds)

```bash
# Clone repository
git clone https://github.com/ayamohamedai/market-insight-ai-bot.git

# Navigate to project
cd market-insight-ai-bot

# Verify files
ls -la
```

✅ You should see: `docker-compose.yml`, `.env.example`, `README.md`

---

### Step 2: Configure API Keys (1 minute)

```bash
# Create environment file
cp .env.example .env

# Open in text editor (choose one)
nano .env        # Linux/Mac
notepad .env     # Windows
code .env        # VS Code
```

**Minimum Required Configuration:**

```bash
# ========== REQUIRED ==========
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE

# ========== AUTO-CONFIGURED ==========
DATABASE_URL=postgresql://postgres:password@postgres:5432/marketdb
REDIS_URL=redis://redis:6379
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# ========== OPTIONAL (for enhanced features) ==========
ALPHA_VANTAGE_KEY=your_key_here
PINECONE_API_KEY=your_key_here
```

**💡 Tip:** For testing, only `OPENAI_API_KEY` is required!

---

### Step 3: Launch Everything (2 minutes)

```bash
# Start all services with Docker
docker-compose up -d

# This will download images and start:
# - PostgreSQL database
# - Redis cache
# - Backend API
# - Frontend app
# - Celery workers
# - Flower monitoring
```

**Wait for services to start (check status):**

```bash
# Check if all containers are running
docker-compose ps

# Expected output:
# NAME                    STATUS
# market-insight-api      Up
# market-insight-frontend Up
# market-insight-db       Up (healthy)
# market-insight-redis    Up
# market-insight-celery   Up
# market-insight-flower   Up
```

---

### Step 4: Initialize Database (30 seconds)

```bash
# Run database migrations
docker-compose exec backend python -c "
from sqlalchemy import create_engine, text
import os

engine = create_engine(os.getenv('DATABASE_URL'))
with open('init.sql', 'r') as f:
    sql = f.read()
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
print('✅ Database initialized!')
"

# Or simply restart backend to auto-init
docker-compose restart backend
```

---

### Step 5: Access the Application! (instant)

Open your browser and visit:

| Service | URL | Purpose |
|---------|-----|---------|
| 🎨 **Frontend Dashboard** | http://localhost:3000 | Main application |
| 📊 **API Documentation** | http://localhost:8000/docs | Interactive API docs |
| 🌸 **Flower (Monitoring)** | http://localhost:5555 | Task queue monitor |
| 🔧 **API Health Check** | http://localhost:8000/api/v2/health | System status |

---

## 🎯 Your First AI Analysis

### Via Web Interface

1. **Open Dashboard**: http://localhost:3000

2. **Select a Stock**:
   - Click dropdown: "Select Company"
   - Choose: "Apple (AAPL)"

3. **Go to AI Assistant Tab**:
   - Click "AI Assistant" in navigation

4. **Ask a Question**:
   ```
   Should I invest in AAPL right now?
   ```

5. **Get AI Analysis**:
   - Wait 3-5 seconds
   - See detailed analysis with confidence score!

### Via API (cURL)

```bash
# Test API directly
curl -X POST http://localhost:8000/api/v2/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze Apple stock performance",
    "company": "AAPL",
    "time_range": "1mo"
  }'
```

**Expected Response:**
```json
{
  "analysis": "Apple Inc. (AAPL) shows strong performance...",
  "insights": [
    "Price increased 5.2% over the past month",
    "Trading above 50-day moving average",
    "Strong institutional buying detected"
  ],
  "confidence_score": 0.87,
  "data": {
    "current_price": 178.45,
    "market_cap": 2800000000000,
    "pe_ratio": 29.5
  }
}
```

---

## 🔍 Verify Everything Works

### Quick Health Check

```bash
# Run comprehensive test
curl http://localhost:8000/api/v2/health

# Expected output:
{
  "status": "healthy",
  "redis": true,
  "timestamp": "2024-10-22T10:30:00Z"
}
```

### Check Services Status

```bash
# Check all containers
docker-compose ps

# Check logs (if something fails)
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery-worker
```

### Test Database Connection

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d marketdb

# Run query
SELECT COUNT(*) FROM companies;

# Expected: 10 (pre-loaded companies)
# Exit: \q
```

### Test Redis Cache

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Test connection
PING
# Expected: PONG

# Exit
exit
```

---

## 🎨 Explore Features

### 1. Dashboard Analytics
- View real-time stock prices
- See market cap and P/E ratios
- Interactive price charts
- Performance indicators

### 2. Competitor Analysis
- Compare multiple companies
- Side-by-side metrics
- AI-powered insights
- Market positioning

### 3. AI Chat Assistant
- Natural language queries
- Real-time analysis
- Confidence scores
- Historical context

### 4. Price Alerts (Coming in UI)
```bash
# Test via API
curl -X POST http://localhost:8000/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "company": "AAPL",
    "alert_type": "price_above",
    "condition_value": 180.00
  }'
```

---

## 🐛 Troubleshooting

### Issue: "OpenAI API Error"

**Solution:**
```bash
# Verify API key is set
docker-compose exec backend env | grep OPENAI

# If empty, add to .env and restart
docker-compose down
# Edit .env file
docker-compose up -d
```

### Issue: "Database Connection Failed"

**Solution:**
```bash
# Wait for PostgreSQL to fully start
docker-compose logs postgres | grep "ready to accept"

# If not ready, wait 30 seconds and retry
sleep 30
docker-compose restart backend
```

### Issue: "Frontend Can't Connect to Backend"

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/api/v2/health

# If failed, check backend logs
docker-compose logs backend

# Common fix: Restart backend
docker-compose restart backend
```

### Issue: "Port Already in Use"

**Solution:**
```bash
# Check what's using the port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL

# Stop the conflicting service or change ports in docker-compose.yml
# Example: Change "3000:3000" to "3001:3000"
```

### Issue: "Docker Out of Memory"

**Solution:**
```bash
# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory: 4GB+

# Or cleanup unused containers
docker system prune -a
```

---

## 📊 Sample Queries to Try

### Market Analysis Queries
```
1. "What's the trend for Tesla stock?"
2. "Compare Apple vs Microsoft performance"
3. "Should I buy Amazon right now?"
4. "Analyze NVIDIA's recent growth"
5. "What are the risks of investing in Meta?"
```

### Technical Analysis
```
1. "Show me AAPL's 50-day moving average"
2. "Is Google overbought or oversold?"
3. "What's the RSI for Tesla?"
4. "Analyze volume trends for Amazon"
```

### Competitor Analysis
```
1. "Compare tech giants: AAPL, MSFT, GOOGL"
2. "Who has better profit margins: Tesla or Ford?"
3. "Market share analysis for streaming companies"
```

---

## 🎓 Next Steps

### Learn More
1. Read [Full Documentation](README.md)
2. Explore [API Documentation](http://localhost:8000/docs)
3. Check [Deployment Guide](DEPLOYMENT.md)

### Customize
1. Add more companies to database
2. Configure additional data sources
3. Customize UI theme
4. Add custom alerts

### Deploy to Production
1. Get production API keys
2. Configure cloud hosting (AWS/GCP/DO)
3. Set up SSL certificates
4. Enable monitoring

---

## 💡 Pro Tips

### Tip 1: Use Flower for Monitoring
```bash
# Open Flower dashboard
open http://localhost:5555

# Monitor:
# - Active tasks
# - Task history
# - Worker status
# - Success/failure rates
```

### Tip 2: Enable Auto-Restart
```bash
# Add to docker-compose.yml
services:
  backend:
    restart: always  # Auto-restart on crash
```

### Tip 3: View Real-time Logs
```bash
# Follow logs from all services
docker-compose logs -f

# Filter specific service
docker-compose logs -f backend

# Last 100 lines only
docker-compose logs --tail=100 backend
```

### Tip 4: Database Backup
```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres marketdb > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres marketdb < backup.sql
```

### Tip 5: Performance Monitoring
```bash
# Check resource usage
docker stats

# See which container uses most resources
docker stats --no-stream | sort -k3 -hr
```

---

## 🆘 Getting Help

### Check Status First
```bash
# System health
curl http://localhost:8000/api/v2/health

# Service status
docker-compose ps

# Recent errors
docker-compose logs --tail=50 backend | grep ERROR
```

### Common Commands
```bash
# Restart everything
docker-compose restart

# Stop everything
docker-compose down

# Start fresh (WARNING: deletes data)
docker-compose down -v
docker-compose up -d

# Update to latest version
git pull
docker-compose build
docker-compose up -d
```

### Get Support
- 📖 [Read Documentation](README.md)
- 🐛 [Report Bug](https://github.com/ayamohamedai/market-insight-ai-bot/issues)
- 💬 [Ask Question](https://github.com/ayamohamedai/market-insight-ai-bot/discussions)
- 📧 [Email Support](mailto:dodomoh2586@gmail.com)

---

## ✅ Success Checklist

- [x] Cloned repository
- [x] Configured `.env` with API keys
- [x] Started all Docker containers
- [x] Initialized database
- [x] Accessed frontend (http://localhost:3000)
- [x] Performed first AI analysis
- [x] Verified API works (http://localhost:8000/docs)
- [x] Checked Flower monitoring (http://localhost:5555)

**🎉 Congratulations! You're ready to use Market Insight AI Bot!**

---

## 📚 What's Next?

### Explore Features
- Try different stocks (MSFT, GOOGL, TSLA)
- Compare competitors
- Set up price alerts
- View historical trends

### Customize Your Setup
- Add your favorite companies
- Configure additional APIs
- Customize UI theme
- Set up email notifications

### Deploy to Production
- Choose hosting provider
- Configure domain and SSL
- Enable backups
- Set up monitoring

---

<div align="center">

**Need help?** Join our community!

[![Discord](https://img.shields.io/badge/Discord-Join-7289DA?logo=discord)](https://discord.gg/marketinsight)
[![Twitter](https://img.shields.io/badge/Twitter-Follow-1DA1F2?logo=twitter)](https://twitter.com/marketinsightai)

---

Made with ❤️ by [Aya Mohamed](https://github.com/ayamohamedai)

[⬅️ Back to README](README.md) | [📚 Full Docs](DEPLOYMENT.md) | [🐛 Report Issue](https://github.com/ayamohamedai/market-insight-ai-bot/issues)

</div>
