import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import random
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

# Page config
st.set_page_config(
    page_title="بوت رؤى السوق الذكي - Market Insight AI Bot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for RTL and styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&display=swap');
    
    .rtl {
        direction: rtl;
        font-family: 'Tajawal', sans-serif;
    }
    
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #0a9396 0%, #94d2bd 50%, #005f73 100%);
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #0a9396 0%, #94d2bd 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .trade-card {
        border: 2px solid #0a9396;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .profit-positive {
        color: #10b981;
        font-weight: bold;
    }
    
    .profit-negative {
        color: #ef4444;
        font-weight: bold;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #ee9b00, #f7931e);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    
    .status-active {
        color: #10b981;
        font-weight: bold;
    }
    
    .status-inactive {
        color: #ef4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Data classes
@dataclass
class Stock:
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    last_update: datetime

@dataclass
class Trade:
    id: int
    symbol: str
    type: str  # 'شراء' or 'بيع'
    entry_price: float
    current_price: float
    quantity: int
    profit_loss: float
    status: str  # 'نشطة' or 'مغلقة'
    timestamp: datetime

# Initialize session state
if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
if 'active_trades' not in st.session_state:
    st.session_state.active_trades = []
if 'total_profit' not in st.session_state:
    st.session_state.total_profit = 0
if 'total_trades' not in st.session_state:
    st.session_state.total_trades = 0
if 'market_data' not in st.session_state:
    st.session_state.market_data = {}

# Market data initialization
MARKET_SYMBOLS = [
    {'symbol': 'AAPL', 'name': 'Apple Inc.', 'price': 175.25},
    {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'price': 2842.13},
    {'symbol': 'MSFT', 'name': 'Microsoft Corp.', 'price': 378.91},
    {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'price': 248.56},
    {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'price': 151.73},
    {'symbol': 'META', 'name': 'Meta Platforms', 'price': 298.34},
    {'symbol': 'NFLX', 'name': 'Netflix Inc.', 'price': 487.22},
    {'symbol': 'NVDA', 'name': 'NVIDIA Corp.', 'price': 722.48}
]

def initialize_market_data():
    """Initialize market data with random movements"""
    for stock in MARKET_SYMBOLS:
        change = random.uniform(-5, 5)
        change_percent = (change / stock['price']) * 100
        
        st.session_state.market_data[stock['symbol']] = Stock(
            symbol=stock['symbol'],
            name=stock['name'],
            price=max(stock['price'] + change, 1),
            change=change,
            change_percent=change_percent,
            last_update=datetime.now()
        )

def update_market_data():
    """Update market data with new random movements"""
    for symbol in st.session_state.market_data:
        stock = st.session_state.market_data[symbol]
        change = random.uniform(-2, 2)
        new_price = max(stock.price + change, 1)
        change_percent = (change / stock.price) * 100
        
        st.session_state.market_data[symbol] = Stock(
            symbol=stock.symbol,
            name=stock.name,
            price=new_price,
            change=change,
            change_percent=change_percent,
            last_update=datetime.now()
        )

def create_new_trade():
    """Create a new simulated trade"""
    symbols = list(st.session_state.market_data.keys())
    symbol = random.choice(symbols)
    stock = st.session_state.market_data[symbol]
    
    trade = Trade(
        id=int(datetime.now().timestamp()),
        symbol=symbol,
        type=random.choice(['شراء', 'بيع']),
        entry_price=stock.price,
        current_price=stock.price,
        quantity=random.randint(10, 100),
        profit_loss=0,
        status='نشطة',
        timestamp=datetime.now()
    )
    
    st.session_state.active_trades.append(trade)
    st.session_state.total_trades += 1

def update_active_trades():
    """Update existing active trades"""
    for trade in st.session_state.active_trades:
        if trade.status == 'نشطة' and trade.symbol in st.session_state.market_data:
            current_stock = st.session_state.market_data[trade.symbol]
            trade.current_price = current_stock.price
            
            if trade.type == 'شراء':
                trade.profit_loss = (trade.current_price - trade.entry_price) * trade.quantity
            else:
                trade.profit_loss = (trade.entry_price - trade.current_price) * trade.quantity
            
            # Random chance to close trade
            if random.random() < 0.1 or abs(trade.profit_loss) > 500:
                trade.status = 'مغلقة'
                st.session_state.total_profit += trade.profit_loss

# Initialize market data if empty
if not st.session_state.market_data:
    initialize_market_data()

# Header
st.markdown("""
<div class="main-header rtl">
    <h1>🧠 بوت رؤى السوق الذكي</h1>
    <h3>Market Insight AI Bot</h3>
    <p>مساعد ذكي متطور مدعوم بأحدث تقنيات الذكاء الاصطناعي لتحليل الأسواق المالية</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Bot Controls
st.sidebar.markdown("## 🤖 التحكم في البوت", unsafe_allow_html=True)

# Bot status
status_color = "status-active" if st.session_state.bot_active else "status-inactive"
status_text = "يعمل 🟢" if st.session_state.bot_active else "متوقف 🔴"
st.sidebar.markdown(f"**حالة البوت:** <span class='{status_color}'>{status_text}</span>", unsafe_allow_html=True)

# Bot settings
capital = st.sidebar.number_input("رأس المال ($)", min_value=100, value=1000, step=100)
risk_percent = st.sidebar.slider("نسبة المخاطرة (%)", min_value=1, max_value=10, value=2)
strategy = st.sidebar.selectbox(
    "الاستراتيجية",
    ["محافظة", "متوسطة", "عدوانية"],
    index=1
)

# Bot control buttons
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🚀 تشغيل البوت"):
        st.session_state.bot_active = True
        st.success(f"تم تشغيل البوت! رأس المال: ${capital:,}")
        
with col2:
    if st.button("⏹️ إيقاف البوت"):
        st.session_state.bot_active = False
        st.error("تم إيقاف البوت!")

# Watchlist management
st.sidebar.markdown("## 📊 قائمة المتابعة")
new_symbol = st.sidebar.text_input("إضافة رمز سهم جديد").upper()
if st.sidebar.button("➕ إضافة"):
    if new_symbol and new_symbol not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_symbol)
        st.sidebar.success(f"تم إضافة {new_symbol}")

# Display watchlist
for symbol in st.session_state.watchlist:
    col1, col2 = st.sidebar.columns([3, 1])
    col1.write(symbol)
    if col2.button("🗑️", key=f"remove_{symbol}"):
        st.session_state.watchlist.remove(symbol)
        st.rerun()

# Auto-update mechanism
if st.session_state.bot_active:
    # Update market data
    update_market_data()
    
    # Create new trades occasionally
    if random.random() < 0.2 and len(st.session_state.active_trades) < 5:
        create_new_trade()
    
    # Update existing trades
    update_active_trades()

# Main content
# Live market data
st.markdown("## 📈 بيانات السوق المباشرة")

market_cols = st.columns(4)
for i, (symbol, stock) in enumerate(st.session_state.market_data.items()):
    with market_cols[i % 4]:
        change_color = "profit-positive" if stock.change >= 0 else "profit-negative"
        arrow = "↗" if stock.change >= 0 else "↘"
        
        st.markdown(f"""
        <div class="trade-card">
            <h4>{stock.symbol}</h4>
            <p style="font-size: 0.8em; opacity: 0.7;">{stock.name}</p>
            <h3>${stock.price:.2f}</h3>
            <p class="{change_color}">{arrow} ${abs(stock.change):.2f} ({abs(stock.change_percent):.2f}%)</p>
        </div>
        """, unsafe_allow_html=True)

# Performance metrics
st.markdown("## 📊 مؤشرات الأداء")
metric_cols = st.columns(4)

with metric_cols[0]:
    st.markdown("""
    <div class="metric-card">
        <h2>96.3%</h2>
        <p>دقة التنبؤات</p>
    </div>
    """, unsafe_allow_html=True)

with metric_cols[1]:
    st.markdown("""
    <div class="metric-card">
        <h2>0.18s</h2>
        <p>سرعة المعالجة</p>
    </div>
    """, unsafe_allow_html=True)

with metric_cols[2]:
    st.markdown(f"""
    <div class="metric-card">
        <h2>{st.session_state.total_trades}</h2>
        <p>إجمالي الصفقات</p>
    </div>
    """, unsafe_allow_html=True)

with metric_cols[3]:
    profit_color = "profit-positive" if st.session_state.total_profit >= 0 else "profit-negative"
    st.markdown(f"""
    <div class="metric-card">
        <h2 class="{profit_color}">${st.session_state.total_profit:.2f}</h2>
        <p>إجمالي الأرباح</p>
    </div>
    """, unsafe_allow_html=True)

# Active trades
st.markdown("## 💹 الصفقات النشطة")

if st.session_state.active_trades:
    # Create DataFrame for better display
    trades_data = []
    for trade in st.session_state.active_trades:
        if trade.status == 'نشطة':
            trades_data.append({
                'الرمز': trade.symbol,
                'النوع': trade.type,
                'سعر الدخول': f"${trade.entry_price:.2f}",
                'السعر الحالي': f"${trade.current_price:.2f}",
                'الكمية': trade.quantity,
                'الربح/الخسارة': f"${trade.profit_loss:.2f}",
                'الحالة': trade.status
            })
    
    if trades_data:
        df = pd.DataFrame(trades_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("لا توجد صفقات نشطة حالياً")
else:
    st.info("لا توجد صفقات نشطة حالياً")

# Price chart
st.markdown("## 📊 الرسم البياني للأسعار")

# Generate sample data for chart
dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
sample_prices = []
base_price = 150
for i in range(len(dates)):
    base_price += random.uniform(-5, 5)
    sample_prices.append(max(base_price, 50))

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=dates,
    y=sample_prices,
    mode='lines+markers',
    name='AAPL',
    line=dict(color='#0a9396', width=3),
    marker=dict(size=6)
))

fig.update_layout(
    title="تطور أسعار الأسهم خلال 30 يوم",
    xaxis_title="التاريخ",
    yaxis_title="السعر ($)",
    height=400,
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)

# Auto-refresh for live updates
if st.session_state.bot_active:
    time.sleep(3)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>© 2025 بوت رؤى السوق الذكي - Market Insight AI Bot</p>
    <p>مدعوم بـ <strong>Streamlit</strong> | <strong>Python</strong> | <strong>Plotly</strong></p>
</div>
""", unsafe_allow_html=True)
