# 🔧 API Documentation

## Market Insight AI Bot API Reference

This documentation provides comprehensive information about the APIs and functions used in the Market Insight AI Bot project.

## 📋 Table of Contents

- [Core Functions](#core-functions)
- [Data Generation](#data-generation)
- [Component APIs](#component-apis)
- [Hooks Documentation](#hooks-documentation)
- [Utility Functions](#utility-functions)
- [Integration Examples](#integration-examples)

---

## 🎯 Core Functions

### Dashboard Analytics

#### `generateDashboardData()`
Generates mock dashboard data for KPI display.

```javascript
/**
 * Generates dashboard analytics data
 * @returns {Object} Dashboard data object
 */
const generateDashboardData = () => {
  return {
    revenue: {
      current: 2487500,
      growth: 12.5,
      trend: 'up'
    },
    marketShare: {
      current: 23.8,
      growth: 2.1,
      trend: 'up'
    },
    customers: {
      current: 15847,
      growth: 8.3,
      trend: 'up'
    },
    conversion: {
      current: 4.2,
      growth: -1.2,
      trend: 'down'
    }
  };
};
```

**Response Format:**
```json
{
  "revenue": {
    "current": 2487500,
    "growth": 12.5,
    "trend": "up"
  },
  "marketShare": {
    "current": 23.8,
    "growth": 2.1,
    "trend": "up"
  }
}
```

### Market Analysis

#### `generateMarketTrends()`
Creates time series data for market trend analysis.

```javascript
/**
 * Generates market trend data for charts
 * @param {number} months - Number of months to generate data for
 * @returns {Array} Array of market data points
 */
const generateMarketTrends = (months = 12) => {
  const data = [];
  const baseValue = 100000;
  
  for (let i = 0; i < months; i++) {
    const date = new Date();
    date.setMonth(date.getMonth() - (months - 1 - i));
    
    data.push({
      month: date.toLocaleDateString('en-US', { 
        month: 'short', 
        year: 'numeric' 
      }),
      revenue: baseValue + (Math.random() * 50000),
      profit: baseValue * 0.3 + (Math.random() * 15000),
      expenses: baseValue * 0.7 + (Math.random() * 20000)
    });
  }
  
  return data;
};
```

**Parameters:**
- `months` (number): Number of months to generate data for (default: 12)

**Response Format:**
```json
[
  {
    "month": "Jan 2024",
    "revenue": 125000,
    "profit": 45000,
    "expenses": 80000
  }
]
```

---

## 📊 Data Generation

### Competitor Analysis Data

#### `generateCompetitorData()`
Generates competitive landscape data for analysis.

```javascript
/**
 * Generates competitor analysis data
 * @returns {Array} Array of competitor data
 */
const generateCompetitorData = () => {
  const competitors = [
    { name: 'Our Company', share: 23.8, color: '#8b5cf6' },
    { name: 'Competitor A', share: 31.2, color: '#06b6d4' },
    { name: 'Competitor B', share: 19.5, color: '#10b981' },
    { name: 'Competitor C', share: 15.3, color: '#f59e0b' },
    { name: 'Others', share: 10.2, color: '#ef4444' }
  ];
  
  return competitors;
};
```

**Response Format:**
```json
[
  {
    "name": "Our Company",
    "share": 23.8,
    "color": "#8b5cf6"
  }
]
```

### Performance Metrics

#### `generatePerformanceData()`
Creates performance comparison data between companies.

```javascript
/**
 * Generates performance comparison data
 * @returns {Array} Performance metrics for multiple companies
 */
const generatePerformanceData = () => {
  const companies = ['Our Company', 'Competitor A', 'Competitor B', 'Competitor C'];
  const metrics = ['Revenue', 'Growth', 'Market Share', 'Customer Satisfaction'];
  
  return companies.map(company => {
    const data = { company };
    metrics.forEach(metric => {
      data[metric] = Math.floor(Math.random() * 100) + 20;
    });
    return data;
  });
};
```

---

## ⚛️ Component APIs

### Dashboard Component

#### Props
```typescript
interface DashboardProps {
  refreshInterval?: number;
  showTrends?: boolean;
  animationDuration?: number;
}
```

#### Methods
- `refreshData()`: Manually refresh dashboard data
- `exportData()`: Export current data as CSV/JSON

### Market Analysis Component

#### Props
```typescript
interface MarketAnalysisProps {
  timeframe?: 'monthly' | 'quarterly' | 'yearly';
  dataPoints?: number;
  chartType?: 'line' | 'area' | 'bar';
}
```

#### Methods
- `updateTimeframe(timeframe)`: Change analysis timeframe
- `exportChart()`: Export chart as PNG/SVG

### AI Assistant Component

#### Props
```typescript
interface AiAssistantProps {
  model?: 'gpt-3.5' | 'gpt-4' | 'claude';
  maxTokens?: number;
  temperature?: number;
}
```

#### Methods
- `sendMessage(message)`: Send message to AI
- `clearHistory()`: Clear conversation history
- `exportConversation()`: Export chat history

---

## 🪝 Hooks Documentation

### `useMarketData`

Custom hook for managing market data state and operations.

```javascript
/**
 * Custom hook for market data management
 * @param {Object} config - Configuration options
 * @returns {Object} Market data and methods
 */
const useMarketData = (config = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      // Simulate API call
      const newData = generateDashboardData();
      setData(newData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  return {
    data,
    loading,
    error,
    refetch: fetchData
  };
};
```

**Usage Example:**
```javascript
const { data, loading, error, refetch } = useMarketData();

if (loading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;
```

### `useAiChat`

Hook for managing AI chat functionality.

```javascript
/**
 * Custom hook for AI chat management
 * @param {Object} options - Chat configuration
 * @returns {Object} Chat state and methods
 */
const useAiChat = (options = {}) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const sendMessage = useCallback(async (message) => {
    setMessages(prev => [...prev, { type: 'user', content: message }]);
    setLoading(true);
    
    try {
      // Simulate AI response
      const response = await simulateAiResponse(message);
      setMessages(prev => [...prev, { type: 'ai', content: response }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: 'Failed to get AI response' 
      }]);
    } finally {
      setLoading(false);
    }
  }, []);
  
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);
  
  return {
    messages,
    loading,
    sendMessage,
    clearMessages
  };
};
```

---

## 🛠️ Utility Functions

### Data Formatting

#### `formatCurrency(value, currency)`
Formats numeric values as currency.

```javascript
/**
 * Formats a number as currency
 * @param {number} value - The numeric value
 * @param {string} currency - Currency code (default: 'USD')
 * @returns {string} Formatted currency string
 */
const formatCurrency = (value, currency = 'USD') => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

// Usage
formatCurrency(2487500); // "$2,487,500"
```

#### `formatPercentage(value, decimals)`
Formats numeric values as percentages.

```javascript
/**
 * Formats a number as percentage
 * @param {number} value - The numeric value
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted percentage string
 */
const formatPercentage = (value, decimals = 1) => {
  return `${value > 0 ? '+' : ''}${value.toFixed(decimals)}%`;
};

// Usage
formatPercentage(12.5); // "+12.5%"
```

### Animation Utilities

#### `animateValue(start, end, duration, callback)`
Animates numeric values with easing.

```javascript
/**
 * Animates a numeric value from start to end
 * @param {number} start - Starting value
 * @param {number} end - Ending value
 * @param {number} duration - Animation duration in ms
 * @param {function} callback - Callback function for each frame
 */
const animateValue = (start, end, duration, callback) => {
  const startTime = performance.now();
  const difference = end - start;
  
  const animate = (currentTime) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Easing function (ease-out)
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const currentValue = start + (difference * easeOut);
    
    callback(currentValue);
    
    if (progress < 1) {
      requestAnimationFrame(animate);
    }
  };
  
  requestAnimationFrame(animate);
};
```

---

## 🔗 Integration Examples

### Real API Integration

Replace mock data with real API calls:

```javascript
// Market data API integration
const fetchMarketData = async () => {
  const response = await fetch('/api/market-data', {
    headers: {
      'Authorization': `Bearer ${process.env.REACT_APP_API_KEY}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch market data');
  }
  
  return response.json();
};

// AI API integration
const sendToAI = async (message) => {
  const response = await fetch('/api/ai/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.REACT_APP_AI_API_KEY}`
    },
    body: JSON.stringify({
      message,
      model: 'gpt-4',
      max_tokens: 500
    })
  });
  
  return response.json();
};
```

### WebSocket Integration

For real-time data updates:

```javascript
const useWebSocket = (url) => {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const newData = JSON.parse(event.data);
      setData(newData);
    };
    
    ws.onclose = () => {
      setConnected(false);
      console.log('WebSocket disconnected');
    };
    
    return () => {
      ws.close();
    };
  }, [url]);
  
  return { data, connected };
};
```

---

## 📚 Additional Resources

- [React Hooks Documentation](https://reactjs.org/docs/hooks-intro.html)
- [Recharts API Reference](https://recharts.org/en-US/api)
- [Tailwind CSS Utilities](https://tailwindcss.com/docs/utility-first)
- [Lucide Icons List](https://lucide.dev/icons/)

## 🤝 Contributing to API

When adding new API functions:

1. Follow the existing naming conventions
2. Include comprehensive JSDoc comments
3. Add TypeScript types where applicable
4. Provide usage examples
5. Update this documentation

---

*Last updated: August 10, 2025*