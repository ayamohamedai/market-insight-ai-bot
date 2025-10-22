/**
 * Market Insight AI Bot - Production Frontend
 * Real API Integration with Advanced Features
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Users, MessageSquare, Search, AlertCircle, CheckCircle, Loader } from 'lucide-react';

// ============ API Configuration ============
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class MarketAPI {
  static async analyzeMarket(query, company, timeRange = '1mo') {
    const response = await fetch(`${API_BASE_URL}/api/v2/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, company, time_range: timeRange })
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  static async getMarketData(ticker, period = '1mo') {
    const response = await fetch(`${API_BASE_URL}/api/v2/market-data/${ticker}?period=${period}`);
    return await response.json();
  }
  
  static async compareCompetitors(company, competitors) {
    const response = await fetch(`${API_BASE_URL}/api/v2/competitor-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company, competitors, metrics: {} })
    });
    return await response.json();
  }
}

// ============ Main App Component ============
export default function MarketInsightApp() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // State for real data
  const [marketData, setMarketData] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [competitorData, setCompetitorData] = useState(null);
  
  // Chat state
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m your AI market analyst. Ask me anything about stocks, competitors, or market trends.' }
  ]);
  const [userInput, setUserInput] = useState('');
  
  // Selected company
  const [selectedCompany, setSelectedCompany] = useState('AAPL');
  const [competitors, setCompetitors] = useState(['MSFT', 'GOOGL', 'AMZN']);

  // ============ Load Initial Data ============
  useEffect(() => {
    loadDashboardData();
  }, [selectedCompany]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load market data
      const data = await MarketAPI.getMarketData(selectedCompany, '3mo');
      setMarketData(data);
      
      // Load competitor analysis
      const compData = await MarketAPI.compareCompetitors(selectedCompany, competitors);
      setCompetitorData(compData);
      
    } catch (err) {
      setError(err.message);
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  // ============ AI Chat Handler ============
  const handleSendMessage = async () => {
    if (!userInput.trim()) return;
    
    const newMessage = { role: 'user', content: userInput };
    setMessages(prev => [...prev, newMessage]);
    setUserInput('');
    setLoading(true);
    
    try {
      const result = await MarketAPI.analyzeMarket(userInput, selectedCompany);
      
      const aiResponse = {
        role: 'assistant',
        content: result.analysis,
        insights: result.insights,
        confidence: result.confidence_score,
        data: result.data
      };
      
      setMessages(prev => [...prev, aiResponse]);
      setAnalysis(result);
      
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.message}. Please try again.`,
        error: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  // ============ Dashboard Component ============
  const Dashboard = () => {
    if (!marketData) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader className="animate-spin h-8 w-8 text-blue-500" />
          <span className="ml-3 text-gray-600">Loading market data...</span>
        </div>
      );
    }

    const kpis = [
      {
        title: 'Current Price',
        value: `$${marketData.current_price?.toFixed(2) || '0.00'}`,
        change: calculateChange(marketData),
        icon: DollarSign,
        color: 'blue'
      },
      {
        title: 'Market Cap',
        value: formatMarketCap(marketData.market_cap),
        change: '+2.3%',
        icon: TrendingUp,
        color: 'green'
      },
      {
        title: 'P/E Ratio',
        value: marketData.pe_ratio?.toFixed(2) || 'N/A',
        change: '-0.5%',
        icon: Users,
        color: 'purple'
      },
      {
        title: '52W Range',
        value: `$${marketData['52_week_low']?.toFixed(2)} - $${marketData['52_week_high']?.toFixed(2)}`,
        change: '+8.2%',
        icon: TrendingUp,
        color: 'orange'
      }
    ];

    return (
      <div className="space-y-6">
        {/* Company Selector */}
        <div className="bg-white p-4 rounded-lg shadow">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Company
          </label>
          <select
            value={selectedCompany}
            onChange={(e) => setSelectedCompany(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="AAPL">Apple (AAPL)</option>
            <option value="MSFT">Microsoft (MSFT)</option>
            <option value="GOOGL">Google (GOOGL)</option>
            <option value="AMZN">Amazon (AMZN)</option>
            <option value="TSLA">Tesla (TSLA)</option>
            <option value="META">Meta (META)</option>
          </select>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {kpis.map((kpi, idx) => (
            <KPICard key={idx} {...kpi} />
          ))}
        </div>

        {/* Price Chart */}
        {marketData.historical && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Price History (90 Days)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={formatHistoricalData(marketData.historical)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Real-time Insights */}
        {analysis && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-3 flex items-center">
              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              AI Insights (Confidence: {(analysis.confidence_score * 100).toFixed(1)}%)
            </h3>
            <p className="text-gray-700 mb-4">{analysis.analysis}</p>
            
            {analysis.insights && analysis.insights.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-medium text-gray-800">Key Points:</h4>
                {analysis.insights.map((insight, idx) => (
                  <div key={idx} className="flex items-start">
                    <span className="text-blue-500 mr-2">•</span>
                    <span className="text-gray-700">{insight.text || insight}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // ============ Competitor Analysis Component ============
  const CompetitorAnalysis = () => {
    if (!competitorData) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader className="animate-spin h-8 w-8 text-blue-500" />
        </div>
      );
    }

    const comparisonData = competitorData.comparison_data;
    const aiAnalysis = competitorData.ai_analysis;

    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Competitor Analysis</h2>
        
        {/* Comparison Table */}
        <div className="bg-white p-6 rounded-lg shadow overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 px-4">Company</th>
                <th className="text-right py-2 px-4">Price</th>
                <th className="text-right py-2 px-4">Market Cap</th>
                <th className="text-right py-2 px-4">P/E Ratio</th>
                <th className="text-right py-2 px-4">Profit Margin</th>
              </tr>
            </thead>
            <tbody>
              {Object.values(comparisonData.Company).map((company, idx) => (
                <tr key={idx} className="border-b hover:bg-gray-50">
                  <td className="py-2 px-4 font-medium">{company}</td>
                  <td className="text-right py-2 px-4">
                    ${Object.values(comparisonData.Price)[idx]?.toFixed(2)}
                  </td>
                  <td className="text-right py-2 px-4">
                    {formatMarketCap(Object.values(comparisonData['Market Cap'])[idx])}
                  </td>
                  <td className="text-right py-2 px-4">
                    {Object.values(comparisonData['P/E Ratio'])[idx]?.toFixed(2)}
                  </td>
                  <td className="text-right py-2 px-4">
                    {(Object.values(comparisonData['Profit Margin'])[idx] * 100)?.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* AI Analysis */}
        {aiAnalysis && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">AI Competitive Intelligence</h3>
            <div className="prose max-w-none">
              <p className="text-gray-700">{aiAnalysis.executive_summary}</p>
              
              {aiAnalysis.key_insights && (
                <div className="mt-4">
                  <h4 className="font-medium">Strategic Insights:</h4>
                  <ul className="list-disc pl-5 space-y-1">
                    {aiAnalysis.key_insights.map((insight, idx) => (
                      <li key={idx}>{insight}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  // ============ AI Chat Component ============
  const AIChat = () => (
    <div className="bg-white rounded-lg shadow h-[600px] flex flex-col">
      <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-lg">
        <h3 className="font-semibold flex items-center">
          <MessageSquare className="h-5 w-5 mr-2" />
          AI Market Assistant
        </h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : msg.error
                  ? 'bg-red-50 text-red-800 border border-red-200'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <p>{msg.content}</p>
              {msg.confidence && (
                <div className="mt-2 text-xs opacity-75">
                  Confidence: {(msg.confidence * 100).toFixed(1)}%
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center space-x-2 text-gray-500">
            <Loader className="animate-spin h-4 w-4" />
            <span>AI is analyzing...</span>
          </div>
        )}
      </div>
      
      <div className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask about market trends, stocks, or competitors..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            disabled={loading}
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !userInput.trim()}
            className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            <Search className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );

  // ============ Helper Components ============
  const KPICard = ({ title, value, change, icon: Icon, color }) => {
    const isPositive = change?.startsWith('+');
    const colorClasses = {
      blue: 'from-blue-500 to-blue-600',
      green: 'from-green-500 to-green-600',
      purple: 'from-purple-500 to-purple-600',
      orange: 'from-orange-500 to-orange-600'
    };

    return (
      <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-lg bg-gradient-to-r ${colorClasses[color]}`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
          {change && (
            <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {change}
            </span>
          )}
        </div>
        <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
        <p className="text-2xl font-bold text-gray-800 mt-1">{value}</p>
      </div>
    );
  };

  // ============ Helper Functions ============
  const calculateChange = (data) => {
    if (!data.historical?.Close) return '+0.00%';
    
    const prices = Object.values(data.historical.Close);
    if (prices.length < 2) return '+0.00%';
    
    const oldPrice = prices[0];
    const newPrice = prices[prices.length - 1];
    const change = ((newPrice - oldPrice) / oldPrice) * 100;
    
    return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
  };

  const formatMarketCap = (value) => {
    if (!value) return 'N/A';
    if (value >= 1e12) return `${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
    return `${value.toFixed(2)}`;
  };

  const formatHistoricalData = (historical) => {
    if (!historical?.Close) return [];
    
    const dates = Object.keys(historical.Close);
    const prices = Object.values(historical.Close);
    
    return dates.map((date, idx) => ({
      date: new Date(parseInt(date)).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      price: prices[idx]
    })).slice(-30); // Last 30 days for better visualization
  };

  // ============ Main Render ============
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Market Insight AI</h1>
              <p className="text-blue-100 mt-1">Professional Market Intelligence Platform</p>
            </div>
            <div className="flex items-center space-x-2 bg-white/20 px-4 py-2 rounded-lg">
              <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm">Live Data</span>
            </div>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4">
          <div className="container mx-auto flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-3" />
            <p className="text-red-700">{error}</p>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="bg-white shadow">
        <div className="container mx-auto px-4">
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: TrendingUp },
              { id: 'competitor', label: 'Competitor Analysis', icon: Users },
              { id: 'chat', label: 'AI Assistant', icon: MessageSquare }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-2 border-b-2 transition ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-800'
                }`}
              >
                <tab.icon className="h-5 w-5" />
                <span className="font-medium">{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'competitor' && <CompetitorAnalysis />}
        {activeTab === 'chat' && <AIChat />}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white mt-12">
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-bold text-lg mb-3">Market Insight AI</h3>
              <p className="text-gray-400 text-sm">
                Professional AI-powered market analysis platform with real-time data integration.
              </p>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-3">Features</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>• Real-time market data</li>
                <li>• AI-powered analysis</li>
                <li>• Competitor intelligence</li>
                <li>• Predictive insights</li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-3">Data Sources</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>• Yahoo Finance API</li>
                <li>• Alpha Vantage</li>
                <li>• OpenAI GPT-4</li>
                <li>• Real-time news feeds</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-700 mt-8 pt-6 text-center text-sm text-gray-400">
            <p>© 2024 Market Insight AI | Created by Aya Mohamed</p>
            <p className="mt-2">AI & Prompt Engineering Specialist</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
