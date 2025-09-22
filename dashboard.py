import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import calendar

class FinanceDashboard:
    def __init__(self):
        self.colors = {
            'income': '#2E8B57',      # Green
            'expense': '#DC143C',      # Red
            'savings': '#4169E1',      # Blue
            'investment': '#9932CC',   # Purple
            'background': '#FFFFFF',
            'text': '#333333'
        }
    
    def create_cash_flow_chart(self, transactions_df):
        """Create monthly cash flow chart"""
        if transactions_df.empty:
            return self.create_empty_chart("No transaction data available")
        
        # Convert date column to datetime
        transactions_df['date'] = pd.to_datetime(transactions_df['date'])
        transactions_df['month'] = transactions_df['date'].dt.to_period('M')
        
        # Group by month and type
        monthly_flow = transactions_df.groupby(['month', 'type'])['amount'].sum().reset_index()
        monthly_flow['month_str'] = monthly_flow['month'].astype(str)
        
        # Separate income and expenses
        income_data = monthly_flow[monthly_flow['type'] == 'income']
        expense_data = monthly_flow[monthly_flow['type'] == 'expense']
        expense_data['amount'] = expense_data['amount'].abs()  # Make expenses positive for display
        
        fig = go.Figure()
        
        # Add income bars
        if not income_data.empty:
            fig.add_trace(go.Bar(
                name='Income',
                x=income_data['month_str'],
                y=income_data['amount'],
                marker_color=self.colors['income'],
                text=[f"${x:,.0f}" for x in income_data['amount']],
                textposition='auto',
            ))
        
        # Add expense bars
        if not expense_data.empty:
            fig.add_trace(go.Bar(
                name='Expenses',
                x=expense_data['month_str'],
                y=expense_data['amount'],
                marker_color=self.colors['expense'],
                text=[f"${x:,.0f}" for x in expense_data['amount']],
                textposition='auto',
            ))
        
        fig.update_layout(
            title="Monthly Cash Flow",
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            barmode='group',
            hovermode='x unified',
            showlegend=True,
            height=400
        )
        
        return fig
    
    def create_category_breakdown(self, transactions_df, transaction_type='expense'):
        """Create pie chart for expense/income categories"""
        if transactions_df.empty:
            return self.create_empty_chart("No transaction data available")
        
        # Filter by transaction type and group by category
        filtered_df = transactions_df[transactions_df['type'] == transaction_type].copy()
        
        if filtered_df.empty:
            return self.create_empty_chart(f"No {transaction_type} data available")
        
        filtered_df['amount'] = filtered_df['amount'].abs()  # Make amounts positive
        category_totals = filtered_df.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        fig = px.pie(
            values=category_totals.values,
            names=category_totals.index,
            title=f"{transaction_type.title()} Breakdown",
            hole=0.4
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont_size=12
        )
        
        fig.update_layout(height=400, showlegend=True)
        
        return fig
    
    def create_savings_trend(self, monthly_summaries):
        """Create savings trend line chart"""
        if not monthly_summaries:
            return self.create_empty_chart("No monthly summary data available")
        
        months = list(monthly_summaries.keys())
        savings = [monthly_summaries[month]['savings'] for month in months]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=savings,
            mode='lines+markers',
            line=dict(color=self.colors['savings'], width=3),
            marker=dict(size=8, color=self.colors['savings']),
            name='Monthly Savings',
            text=[f"${x:,.0f}" for x in savings],
            textposition='top center'
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title="Savings Trend Over Time",
            xaxis_title="Month",
            yaxis_title="Savings ($)",
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def create_net_worth_chart(self, monthly_summaries):
        """Create cumulative net worth chart"""
        if not monthly_summaries:
            return self.create_empty_chart("No net worth data available")
        
        months = list(monthly_summaries.keys())
        net_worth = []
        cumulative = 0
        
        for month in months:
            cumulative += monthly_summaries[month]['savings']
            net_worth.append(cumulative)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=net_worth,
            mode='lines+markers',
            fill='tonexty',
            line=dict(color=self.colors['investment'], width=3),
            marker=dict(size=8, color=self.colors['investment']),
            name='Net Worth',
            text=[f"${x:,.0f}" for x in net_worth],
            textposition='top center'
        ))
        
        fig.update_layout(
            title="Net Worth Growth",
            xaxis_title="Month",
            yaxis_title="Net Worth ($)",
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def create_portfolio_chart(self, portfolio_data):
        """Create stock portfolio visualization"""
        if not portfolio_data['holdings']:
            return self.create_empty_chart("No portfolio data available")
        
        holdings = portfolio_data['holdings']
        symbols = [h['symbol'] for h in holdings]
        values = [h['current_value'] for h in holdings]
        gains = [h['gain_loss_percent'] for h in holdings]
        
        # Create subplot with portfolio allocation and performance
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "bar"}]],
            subplot_titles=("Portfolio Allocation", "Performance %")
        )
        
        # Portfolio allocation pie chart
        fig.add_trace(
            go.Pie(
                labels=symbols,
                values=values,
                hole=0.4,
                textinfo='label+percent',
                textposition='auto'
            ),
            row=1, col=1
        )
        
        # Performance bar chart
        colors = [self.colors['income'] if g >= 0 else self.colors['expense'] for g in gains]
        
        fig.add_trace(
            go.Bar(
                x=symbols,
                y=gains,
                marker_color=colors,
                text=[f"{g:+.1f}%" for g in gains],
                textposition='auto',
                name='Gain/Loss %'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title="AI Stock Portfolio Overview",
            height=500,
            showlegend=False
        )
        
        # Add zero line to performance chart
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=2)
        
        return fig
    
    def create_gamification_metrics(self, current_savings, savings_goal, streak_days):
        """Create gamification display with progress bars and achievements"""
        
        # Calculate progress percentage
        progress = min((current_savings / savings_goal * 100), 100) if savings_goal > 0 else 0
        
        # Achievement levels
        achievements = []
        if current_savings >= 1000:
            achievements.append("🎯 First $1K Saved!")
        if current_savings >= 5000:
            achievements.append("🏆 $5K Milestone!")
        if current_savings >= 10000:
            achievements.append("💎 $10K Club!")
        if streak_days >= 30:
            achievements.append("🔥 30-Day Streak!")
        if streak_days >= 90:
            achievements.append("⚡ 90-Day Master!")
        
        return {
            'progress_percent': round(progress, 1),
            'achievements': achievements,
            'streak_days': streak_days,
            'level': min(int(current_savings / 1000), 50),  # Level up every $1K
            'next_milestone': ((int(current_savings / 1000) + 1) * 1000) if current_savings < 50000 else 50000
        }
    
    def create_spending_heatmap(self, transactions_df):
        """Create monthly spending heatmap by category"""
        if transactions_df.empty:
            return self.create_empty_chart("No spending data available")
        
        # Filter expenses only
        expenses_df = transactions_df[transactions_df['type'] == 'expense'].copy()
        
        if expenses_df.empty:
            return self.create_empty_chart("No expense data available")
        
        expenses_df['date'] = pd.to_datetime(expenses_df['date'])
        expenses_df['month'] = expenses_df['date'].dt.strftime('%Y-%m')
        expenses_df['amount'] = expenses_df['amount'].abs()
        
        # Create pivot table
        heatmap_data = expenses_df.pivot_table(
            values='amount',
            index='category',
            columns='month',
            aggfunc='sum',
            fill_value=0
        )
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='Reds',
            text=[[f"${val:,.0f}" if val > 0 else "" for val in row] for row in heatmap_data.values],
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Monthly Spending Heatmap by Category",
            xaxis_title="Month",
            yaxis_title="Category",
            height=400
        )
        
        return fig
    
    def create_empty_chart(self, message):
        """Create empty chart with message"""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        return fig
    
    def display_key_metrics(self, total_income, total_expenses, total_savings, portfolio_value):
        """Display key financial metrics in columns"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Total Income",
                value=f"${total_income:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="💸 Total Expenses", 
                value=f"${total_expenses:,.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="💎 Total Savings",
                value=f"${total_savings:,.2f}",
                delta=f"${total_income - total_expenses:,.2f}" if total_income > 0 else None
            )
        
        with col4:
            st.metric(
                label="📈 Portfolio Value",
                value=f"${portfolio_value:,.2f}",
                delta=None
            )
    
    def display_ai_stock_watchlist(self, ai_stocks_data):
        """Display AI stocks watchlist table"""
        if not ai_stocks_data:
            st.info("No AI stock data available")
            return
        
        # Create DataFrame for display
        df = pd.DataFrame(ai_stocks_data)
        
        # Format for display
        display_df = df[['symbol', 'company_name', 'current_price', 'change', 'change_percent']].copy()
        display_df.columns = ['Symbol', 'Company', 'Price', 'Change', 'Change %']
        
        # Color code the change columns
        def highlight_changes(val):
            if isinstance(val, (int, float)):
                color = 'color: green' if val >= 0 else 'color: red'
                return color
            return ''
        
        styled_df = display_df.style.applymap(highlight_changes, subset=['Change', 'Change %'])
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
