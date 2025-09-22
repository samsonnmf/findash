import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests

class AIStockTracker:
    def __init__(self):
        # Popular AI infrastructure stocks
        self.ai_stocks = {
            'NVDA': 'NVIDIA Corp',
            'AMD': 'Advanced Micro Devices',
            'GOOGL': 'Alphabet Inc',
            'MSFT': 'Microsoft Corp',
            'AMZN': 'Amazon.com Inc',
            'TSLA': 'Tesla Inc',
            'META': 'Meta Platforms Inc',
            'AAPL': 'Apple Inc',
            'PLTR': 'Palantir Technologies',
            'NET': 'Cloudflare Inc',
            'SNOW': 'Snowflake Inc',
            'CRM': 'Salesforce Inc',
            'ORCL': 'Oracle Corp',
            'IBM': 'IBM Corp',
            'INTC': 'Intel Corp'
        }
    
    def get_stock_price(self, symbol):
        """Get current stock price and basic info"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="1d")
            
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            previous_close = info.get('previousClose', current_price)
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', symbol),
                'current_price': round(current_price, 2),
                'previous_close': round(previous_close, 2),
                'change': round(current_price - previous_close, 2),
                'change_percent': round(((current_price - previous_close) / previous_close) * 100, 2),
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume', 0),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def get_portfolio_value(self, portfolio_df):
        """Calculate total portfolio value with current prices"""
        if portfolio_df.empty:
            return {
                'total_value': 0,
                'total_cost': 0,
                'total_gain_loss': 0,
                'total_gain_loss_percent': 0,
                'holdings': []
            }
        
        holdings = []
        total_value = 0
        total_cost = 0
        
        for _, row in portfolio_df.iterrows():
            stock_info = self.get_stock_price(row['symbol'])
            
            if stock_info:
                shares = row['shares']
                purchase_price = row['purchase_price']
                current_price = stock_info['current_price']
                
                cost = shares * purchase_price
                value = shares * current_price
                gain_loss = value - cost
                gain_loss_percent = (gain_loss / cost) * 100 if cost > 0 else 0
                
                holdings.append({
                    'symbol': row['symbol'],
                    'company_name': stock_info['company_name'],
                    'shares': shares,
                    'purchase_price': purchase_price,
                    'current_price': current_price,
                    'cost_basis': round(cost, 2),
                    'current_value': round(value, 2),
                    'gain_loss': round(gain_loss, 2),
                    'gain_loss_percent': round(gain_loss_percent, 2),
                    'purchase_date': row['purchase_date']
                })
                
                total_value += value
                total_cost += cost
        
        total_gain_loss = total_value - total_cost
        total_gain_loss_percent = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0
        
        return {
            'total_value': round(total_value, 2),
            'total_cost': round(total_cost, 2),
            'total_gain_loss': round(total_gain_loss, 2),
            'total_gain_loss_percent': round(total_gain_loss_percent, 2),
            'holdings': sorted(holdings, key=lambda x: x['current_value'], reverse=True)
        }
    
    def get_ai_stocks_overview(self):
        """Get overview of popular AI stocks for investment ideas"""
        stocks_data = []
        
        for symbol, name in self.ai_stocks.items():
            stock_info = self.get_stock_price(symbol)
            if stock_info:
                stocks_data.append(stock_info)
        
        # Sort by market cap (largest first)
        stocks_data.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
        
        return stocks_data
    
    def get_stock_history(self, symbol, period="1mo"):
        """Get historical price data for charting"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            
            if hist.empty:
                return None
            
            return {
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'prices': hist['Close'].round(2).tolist(),
                'volumes': hist['Volume'].tolist()
            }
        except Exception as e:
            print(f"Error fetching history for {symbol}: {str(e)}")
            return None
    
    def calculate_portfolio_metrics(self, holdings):
        """Calculate advanced portfolio metrics"""
        if not holdings:
            return {}
        
        total_value = sum(holding['current_value'] for holding in holdings)
        
        # Sector diversification (simplified)
        sector_map = {
            'NVDA': 'Semiconductors', 'AMD': 'Semiconductors', 'INTC': 'Semiconductors',
            'GOOGL': 'Software', 'MSFT': 'Software', 'META': 'Software', 'CRM': 'Software',
            'AMZN': 'Cloud/E-commerce', 'ORCL': 'Database', 'IBM': 'Enterprise',
            'TSLA': 'Automotive/Energy', 'PLTR': 'Analytics', 'NET': 'Infrastructure',
            'SNOW': 'Data', 'AAPL': 'Consumer Tech'
        }
        
        sectors = {}
        for holding in holdings:
            sector = sector_map.get(holding['symbol'], 'Other')
            if sector not in sectors:
                sectors[sector] = 0
            sectors[sector] += holding['current_value']
        
        # Convert to percentages
        sector_allocation = {
            sector: round((value / total_value) * 100, 1) 
            for sector, value in sectors.items()
        }
        
        # Top performers
        top_performers = sorted(holdings, key=lambda x: x['gain_loss_percent'], reverse=True)[:3]
        worst_performers = sorted(holdings, key=lambda x: x['gain_loss_percent'])[:3]
        
        return {
            'sector_allocation': sector_allocation,
            'top_performers': top_performers,
            'worst_performers': worst_performers,
            'total_positions': len(holdings)
        }
    
    def get_market_sentiment(self):
        """Get overall market sentiment for AI sector"""
        # Simple implementation using major AI stock performance
        major_ai_stocks = ['NVDA', 'GOOGL', 'MSFT', 'AMZN']
        positive_count = 0
        total_change = 0
        
        for symbol in major_ai_stocks:
            stock_info = self.get_stock_price(symbol)
            if stock_info and stock_info['change_percent']:
                total_change += stock_info['change_percent']
                if stock_info['change_percent'] > 0:
                    positive_count += 1
        
        avg_change = total_change / len(major_ai_stocks)
        positive_ratio = positive_count / len(major_ai_stocks)
        
        if avg_change > 2:
            sentiment = "Very Bullish 🚀"
        elif avg_change > 0.5:
            sentiment = "Bullish 📈"
        elif avg_change > -0.5:
            sentiment = "Neutral 😐"
        elif avg_change > -2:
            sentiment = "Bearish 📉"
        else:
            sentiment = "Very Bearish 🐻"
        
        return {
            'sentiment': sentiment,
            'avg_change': round(avg_change, 2),
            'positive_ratio': round(positive_ratio * 100, 1),
            'last_updated': datetime.now().strftime('%H:%M:%S')
        }