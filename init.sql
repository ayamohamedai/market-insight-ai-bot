-- ============================================
-- Market Insight AI Bot - Database Schema
-- PostgreSQL 15+
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============ Users Table ============
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user', -- user, premium, admin
    is_active BOOLEAN DEFAULT true,
    api_key VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key ON users(api_key);

-- ============ Companies Table ============
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    description TEXT,
    website VARCHAR(255),
    logo_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_companies_ticker ON companies(ticker);
CREATE INDEX idx_companies_sector ON companies(sector);

-- ============ Market Data Table ============
CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    open_price DECIMAL(12, 4),
    close_price DECIMAL(12, 4),
    high_price DECIMAL(12, 4),
    low_price DECIMAL(12, 4),
    volume BIGINT,
    adjusted_close DECIMAL(12, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, date)
);

CREATE INDEX idx_market_data_company_date ON market_data(company_id, date DESC);
CREATE INDEX idx_market_data_date ON market_data(date DESC);

-- ============ AI Analysis Cache ============
CREATE TABLE IF NOT EXISTS ai_analysis_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_hash VARCHAR(64) UNIQUE NOT NULL, -- MD5/SHA256 of query params
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    analysis_result JSONB NOT NULL,
    confidence_score DECIMAL(3, 2),
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    hit_count INTEGER DEFAULT 0
);

CREATE INDEX idx_ai_cache_hash ON ai_analysis_cache(query_hash);
CREATE INDEX idx_ai_cache_company ON ai_analysis_cache(company_id);
CREATE INDEX idx_ai_cache_expires ON ai_analysis_cache(expires_at);

-- ============ User Queries Log ============
CREATE TABLE IF NOT EXISTS user_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50), -- market_analysis, competitor, general
    company_ticker VARCHAR(10),
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_queries_user ON user_queries(user_id);
CREATE INDEX idx_queries_created ON user_queries(created_at DESC);

-- ============ Watchlists ============
CREATE TABLE IF NOT EXISTS watchlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_watchlists_user ON watchlists(user_id);

-- ============ Watchlist Items ============
CREATE TABLE IF NOT EXISTS watchlist_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    watchlist_id UUID REFERENCES watchlists(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    notes TEXT,
    target_price DECIMAL(12, 4),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(watchlist_id, company_id)
);

CREATE INDEX idx_watchlist_items_list ON watchlist_items(watchlist_id);

-- ============ Alerts ============
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL, -- price_above, price_below, volume_spike, news_sentiment
    condition_value DECIMAL(12, 4),
    is_active BOOLEAN DEFAULT true,
    triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_user_active ON alerts(user_id, is_active);
CREATE INDEX idx_alerts_company ON alerts(company_id);

-- ============ News Sentiment ============
CREATE TABLE IF NOT EXISTS news_sentiment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    title VARCHAR(500),
    source VARCHAR(100),
    url VARCHAR(1000),
    published_at TIMESTAMP WITH TIME ZONE,
    sentiment_score DECIMAL(3, 2), -- -1.0 to 1.0
    sentiment_label VARCHAR(20), -- positive, negative, neutral
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_news_company_date ON news_sentiment(company_id, published_at DESC);
CREATE INDEX idx_news_sentiment_score ON news_sentiment(sentiment_score);

-- ============ API Usage Tracking ============
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_usage_user ON api_usage(user_id);
CREATE INDEX idx_api_usage_timestamp ON api_usage(timestamp DESC);

-- ============ System Metrics ============
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100),
    metric_value DECIMAL(12, 4),
    metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_name_time ON system_metrics(metric_name, recorded_at DESC);

-- ============ Functions & Triggers ============

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watchlists_updated_at BEFORE UPDATE ON watchlists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============ Initial Data ============

-- Insert popular companies
INSERT INTO companies (ticker, name, sector, industry) VALUES
    ('AAPL', 'Apple Inc.', 'Technology', 'Consumer Electronics'),
    ('MSFT', 'Microsoft Corporation', 'Technology', 'Software'),
    ('GOOGL', 'Alphabet Inc.', 'Technology', 'Internet Services'),
    ('AMZN', 'Amazon.com Inc.', 'Consumer Cyclical', 'E-commerce'),
    ('TSLA', 'Tesla Inc.', 'Automotive', 'Electric Vehicles'),
    ('META', 'Meta Platforms Inc.', 'Technology', 'Social Media'),
    ('NVDA', 'NVIDIA Corporation', 'Technology', 'Semiconductors'),
    ('JPM', 'JPMorgan Chase & Co.', 'Financial', 'Banking'),
    ('V', 'Visa Inc.', 'Financial', 'Payment Processing'),
    ('WMT', 'Walmart Inc.', 'Consumer Defensive', 'Retail')
ON CONFLICT (ticker) DO NOTHING;

-- Create admin user (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash for 'admin123' using bcrypt
INSERT INTO users (email, username, password_hash, full_name, role) VALUES
    ('admin@marketinsight.ai', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU.qLK4xz1Lu', 'System Administrator', 'admin')
ON CONFLICT (email) DO NOTHING;

-- ============ Views for Analytics ============

-- Daily market summary view
CREATE OR REPLACE VIEW daily_market_summary AS
SELECT 
    c.ticker,
    c.name,
    md.date,
    md.close_price,
    md.volume,
    ROUND(((md.close_price - LAG(md.close_price) OVER (PARTITION BY c.id ORDER BY md.date)) / 
           LAG(md.close_price) OVER (PARTITION BY c.id ORDER BY md.date) * 100), 2) as daily_change_pct
FROM companies c
JOIN market_data md ON c.id = md.company_id
ORDER BY md.date DESC, c.ticker;

-- User activity summary view
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT 
    u.id,
    u.username,
    COUNT(DISTINCT uq.id) as total_queries,
    COUNT(DISTINCT w.id) as total_watchlists,
    COUNT(DISTINCT a.id) as active_alerts,
    MAX(uq.created_at) as last_query_at
FROM users u
LEFT JOIN user_queries uq ON u.id = uq.user_id
LEFT JOIN watchlists w ON u.id = w.user_id
LEFT JOIN alerts a ON u.id = a.user_id AND a.is_active = true
GROUP BY u.id, u.username;

-- Market performance view
CREATE OR REPLACE VIEW market_performance AS
SELECT 
    c.ticker,
    c.name,
    c.sector,
    MAX(md.close_price) as current_price,
    MIN(md.close_price) FILTER (WHERE md.date >= CURRENT_DATE - INTERVAL '52 weeks') as week_52_low,
    MAX(md.close_price) FILTER (WHERE md.date >= CURRENT_DATE - INTERVAL '52 weeks') as week_52_high,
    AVG(md.volume) FILTER (WHERE md.date >= CURRENT_DATE - INTERVAL '30 days') as avg_volume_30d
FROM companies c
JOIN market_data md ON c.id = md.company_id
GROUP BY c.id, c.ticker, c.name, c.sector;

-- ============ Materialized Views for Performance ============

-- Top performers (refreshed periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS top_performers AS
SELECT 
    c.ticker,
    c.name,
    c.sector,
    (SELECT close_price FROM market_data WHERE company_id = c.id ORDER BY date DESC LIMIT 1) as current_price,
    ROUND(
        (((SELECT close_price FROM market_data WHERE company_id = c.id ORDER BY date DESC LIMIT 1) -
          (SELECT close_price FROM market_data WHERE company_id = c.id AND date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY date ASC LIMIT 1)) /
         (SELECT close_price FROM market_data WHERE company_id = c.id AND date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY date ASC LIMIT 1) * 100)
    , 2) as change_30d_pct
FROM companies c
WHERE c.is_active = true
ORDER BY change_30d_pct DESC NULLS LAST
LIMIT 20;

CREATE INDEX idx_top_performers ON top_performers(change_30d_pct DESC);

-- ============ Cleanup Functions ============

-- Clean expired AI cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $
BEGIN
    DELETE FROM ai_analysis_cache
    WHERE expires_at < CURRENT_TIMESTAMP;
END;
$ LANGUAGE plpgsql;

-- Clean old logs (keep last 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS void AS $
BEGIN
    DELETE FROM api_usage
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
    DELETE FROM user_queries
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
END;
$ LANGUAGE plpgsql;

-- ============ Scheduled Jobs (using pg_cron extension) ============
-- Note: Requires pg_cron extension to be installed

-- Refresh materialized views every hour
-- SELECT cron.schedule('refresh-top-performers', '0 * * * *', 'REFRESH MATERIALIZED VIEW top_performers;');

-- Clean expired cache daily at 2 AM
-- SELECT cron.schedule('cleanup-cache', '0 2 * * *', 'SELECT cleanup_expired_cache();');

-- Clean old logs weekly
-- SELECT cron.schedule('cleanup-logs', '0 3 * * 0', 'SELECT cleanup_old_logs();');

-- ============ Grants & Permissions ============

-- Grant permissions to application user
-- CREATE USER market_app WITH PASSWORD 'secure_password_here';
-- GRANT CONNECT ON DATABASE marketdb TO market_app;
-- GRANT USAGE ON SCHEMA public TO market_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO market_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO market_app;

COMMENT ON DATABASE marketdb IS 'Market Insight AI Bot - Production Database';
COMMENT ON TABLE users IS 'User accounts and authentication data';
COMMENT ON TABLE companies IS 'Company master data';
COMMENT ON TABLE market_data IS 'Historical market data (OHLCV)';
COMMENT ON TABLE ai_analysis_cache IS 'Cached AI analysis results for performance';
COMMENT ON TABLE user_queries IS 'User query history and analytics';
COMMENT ON TABLE watchlists IS 'User-created stock watchlists';
COMMENT ON TABLE alerts IS 'Price and event alerts';
COMMENT ON TABLE news_sentiment IS 'News articles with sentiment analysis';
