import sqlite3
import pandas as pd
from datetime import datetime, date
import os

class FinanceDatabase:
    def __init__(self, db_name="finance_tracker.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                source_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Monthly summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                income REAL DEFAULT 0,
                expenses REAL DEFAULT 0,
                savings REAL DEFAULT 0,
                net_worth REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(month, year)
            )
        ''')
        
        # Goals and gamification table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_type TEXT NOT NULL,
                target_amount REAL,
                current_amount REAL DEFAULT 0,
                target_date DATE,
                achieved BOOLEAN DEFAULT FALSE,
                streak_count INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Stock portfolio table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                company_name TEXT,
                shares REAL NOT NULL,
                purchase_price REAL NOT NULL,
                purchase_date DATE NOT NULL,
                is_ai_stock BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_transaction(self, date, amount, category, transaction_type, description="", source_file=""):
        """Insert a new transaction"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (date, amount, category, type, description, source_file)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, amount, category, transaction_type, description, source_file))
        
        conn.commit()
        conn.close()
    
    def get_transactions(self, start_date=None, end_date=None, category=None):
        """Get transactions with optional filtering"""
        conn = sqlite3.connect(self.db_name)
        
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY date DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_monthly_summary(self, year, month):
        """Get or create monthly summary"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM monthly_summaries 
            WHERE year = ? AND month = ?
        ''', (year, month))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'income': result[3],
                'expenses': result[4],
                'savings': result[5],
                'net_worth': result[6]
            }
        else:
            return self.calculate_monthly_summary(year, month)
    
    def calculate_monthly_summary(self, year, month):
        """Calculate monthly summary from transactions"""
        conn = sqlite3.connect(self.db_name)
        
        # Get transactions for the month
        query = '''
            SELECT type, SUM(amount) as total
            FROM transactions 
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY type
        '''
        
        df = pd.read_sql_query(query, conn, params=[str(year), f"{month:02d}"])
        
        income = df[df['type'] == 'income']['total'].sum() if len(df[df['type'] == 'income']) > 0 else 0
        expenses = abs(df[df['type'] == 'expense']['total'].sum()) if len(df[df['type'] == 'expense']) > 0 else 0
        savings = income - expenses
        
        # Insert or update monthly summary
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO monthly_summaries (month, year, income, expenses, savings, net_worth)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (f"{month:02d}", year, income, expenses, savings, savings))
        
        conn.commit()
        conn.close()
        
        return {
            'income': income,
            'expenses': expenses,
            'savings': savings,
            'net_worth': savings
        }
    
    def get_categories(self):
        """Get all unique transaction categories"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT category FROM transactions ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return categories
    
    def insert_stock(self, symbol, company_name, shares, purchase_price, purchase_date, is_ai_stock=True):
        """Insert stock purchase"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO stock_portfolio (symbol, company_name, shares, purchase_price, purchase_date, is_ai_stock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (symbol, company_name, shares, purchase_price, purchase_date, is_ai_stock))
        
        conn.commit()
        conn.close()
    
    def get_portfolio(self):
        """Get current stock portfolio"""
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query("SELECT * FROM stock_portfolio ORDER BY purchase_date DESC", conn)
        conn.close()
        return df
    
    def update_goal(self, goal_type, target_amount, current_amount=0):
        """Update or insert a goal"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO goals (goal_type, target_amount, current_amount)
            VALUES (?, ?, ?)
        ''', (goal_type, target_amount, current_amount))
        
        conn.commit()
        conn.close()
    
    def get_goals(self):
        """Get all goals"""
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query("SELECT * FROM goals ORDER BY created_at DESC", conn)
        conn.close()
        return df
