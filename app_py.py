import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use Streamlit secrets instead

# Import our custom modules
from database_py import FinanceDatabase
from pdf_processor.py import PDFProcessor
from stock_tracker_py import AIStockTracker
from dashboard_py import FinanceDashboard

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    """Initialize database and other components"""
    db = FinanceDatabase()
    pdf_processor = PDFProcessor()
    stock_tracker = AIStockTracker()
    dashboard = FinanceDashboard()
    return db, pdf_processor, stock_tracker, dashboard

def main():
    db, pdf_processor, stock_tracker, dashboard = init_components()
    
    # App title and description
    st.title("💰 Personal Finance Tracker")
    st.markdown("### Gamify your journey to financial freedom through AI investments!")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["📊 Dashboard", "📄 Upload PDF", "💹 AI Stocks", "🎯 Goals", "📝 Manual Entry", "⚙️ Settings"]
    )
    
    # API Key check
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))
    
    if not has_openai and not has_anthropic:
        st.sidebar.warning("⚠️ No AI API key configured. PDF processing will not work.")
        st.sidebar.info("Add OPENAI_API_KEY or ANTHROPIC_API_KEY to your environment variables.")
    
    # Main content based on selected page
    if page == "📊 Dashboard":
        show_dashboard(db, stock_tracker, dashboard)
    elif page == "📄 Upload PDF":
        show_pdf_upload(db, pdf_processor)
    elif page == "💹 AI Stocks":
        show_ai_stocks(db, stock_tracker)
    elif page == "🎯 Goals":
        show_goals(db)
    elif page == "📝 Manual Entry":
        show_manual_entry(db)
    elif page == "⚙️ Settings":
        show_settings()

def show_dashboard(db, stock_tracker, dashboard):
    """Main dashboard page"""
    st.header("📊 Financial Dashboard")
    
    # Get recent transactions
    transactions_df = db.get_transactions()
    portfolio_df = db.get_portfolio()
    
    # Calculate key metrics
    if not transactions_df.empty:
        total_income = transactions_df[transactions_df['type'] == 'income']['amount'].sum()
        total_expenses = abs(transactions_df[transactions_df['type'] == 'expense']['amount'].sum())
        total_savings = total_income - total_expenses
    else:
        total_income = total_expenses = total_savings = 0
    
    # Get portfolio value
    portfolio_data = stock_tracker.get_portfolio_value(portfolio_df)
    portfolio_value = portfolio_data['total_value']
    
    # Display key metrics
    dashboard.display_key_metrics(total_income, total_expenses, total_savings, portfolio_value)
    
    # Gamification section
    st.subheader("🎮 Your Financial Game")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Savings goal progress
        savings_goal = 10000  # You can make this configurable
        progress = min((total_savings / savings_goal * 100), 100) if savings_goal > 0 else 0
        st.metric("💎 Savings Progress", f"{progress:.1f}%")
        st.progress(progress / 100)
    
    with col2:
        # Streak counter (simplified - you can enhance this)
        streak_days = 15  # Placeholder - implement streak logic
        st.metric("🔥 Savings Streak", f"{streak_days} days")
        
    with col3:
        # Level system
        level = min(int(total_savings / 1000), 50)
        st.metric("⭐ Financial Level", f"Level {level}")
    
    # Charts section
    if not transactions_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Cash flow chart
            cash_flow_fig = dashboard.create_cash_flow_chart(transactions_df)
            st.plotly_chart(cash_flow_fig, use_container_width=True)
        
        with col2:
            # Expense breakdown
            expense_fig = dashboard.create_category_breakdown(transactions_df, 'expense')
            st.plotly_chart(expense_fig, use_container_width=True)
        
        # Spending heatmap
        st.subheader("🔥 Spending Heatmap")
        heatmap_fig = dashboard.create_spending_heatmap(transactions_df)
        st.plotly_chart(heatmap_fig, use_container_width=True)
    
    # Portfolio section
    if portfolio_value > 0:
        st.subheader("📈 AI Stock Portfolio")
        portfolio_fig = dashboard.create_portfolio_chart(portfolio_data)
        st.plotly_chart(portfolio_fig, use_container_width=True)
        
        # Portfolio metrics
        metrics = stock_tracker.calculate_portfolio_metrics(portfolio_data['holdings'])
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top Performers:**")
            for stock in metrics.get('top_performers', [])[:3]:
                st.write(f"• {stock['symbol']}: +{stock['gain_loss_percent']:.1f}%")
        
        with col2:
            st.write("**Sector Allocation:**")
            for sector, percentage in metrics.get('sector_allocation', {}).items():
                st.write(f"• {sector}: {percentage}%")
    
    # Recent transactions table
    if not transactions_df.empty:
        st.subheader("📋 Recent Transactions")
        recent_transactions = transactions_df.head(10)
        st.dataframe(recent_transactions, use_container_width=True, hide_index=True)

def show_pdf_upload(db, pdf_processor):
    """PDF upload and processing page"""
    st.header("📄 Upload Financial PDF")
    st.write("Upload bank statements, investment reports, or other financial PDFs to automatically extract transaction data.")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload bank statements, credit card statements, or investment reports"
    )
    
    if uploaded_file is not None:
        # Display file info
        st.success(f"File uploaded: {uploaded_file.name}")
        
        # LLM provider selection
        llm_provider = st.selectbox(
            "Choose AI provider:",
            ["openai", "anthropic"],
            help="Select which AI service to use for processing"
        )
        
        # Process button
        if st.button("🤖 Process PDF", type="primary"):
            with st.spinner("Processing PDF with AI..."):
                result = pdf_processor.process_pdf_file(uploaded_file, llm_provider)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.success(f"✅ Successfully extracted {result['transaction_count']} transactions!")
                
                # Display extracted transactions
                if result['transactions']:
                    st.subheader("Extracted Transactions")
                    transactions_df = pd.DataFrame(result['transactions'])
                    
                    # Allow user to review and edit
                    edited_df = st.data_editor(
                        transactions_df,
                        use_container_width=True,
                        num_rows="dynamic"
                    )
                    
                    # Save to database
                    if st.button("💾 Save to Database"):
                        saved_count = 0
                        for _, row in edited_df.iterrows():
                            try:
                                db.insert_transaction(
                                    row['date'],
                                    row['amount'],
                                    row['category'],
                                    row['type'],
                                    row.get('description', ''),
                                    uploaded_file.name
                                )
                                saved_count += 1
                            except Exception as e:
                                st.error(f"Error saving transaction: {e}")
                        
                        st.success(f"💾 Saved {saved_count} transactions to database!")
                        st.balloons()
                
                # Show text preview
                with st.expander("📄 Extracted Text Preview"):
                    st.text(result['extracted_text_preview'])

def show_ai_stocks(db, stock_tracker):
    """AI stocks tracking page"""
    st.header("💹 AI Infrastructure Stocks")
    
    # Market sentiment
    sentiment = stock_tracker.get_market_sentiment()
    st.metric("📊 AI Market Sentiment", sentiment['sentiment'], f"{sentiment['avg_change']:+.2f}%")
    
    # Portfolio overview
    portfolio_df = db.get_portfolio()
    if not portfolio_df.empty:
        st.subheader("📈 Your AI Portfolio")
        portfolio_data = stock_tracker.get_portfolio_value(portfolio_df)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Portfolio Value", f"${portfolio_data['total_value']:,.2f}")
        with col2:
            st.metric("Total Gain/Loss", f"${portfolio_data['total_gain_loss']:,.2f}")
        with col3:
            st.metric("Gain/Loss %", f"{portfolio_data['total_gain_loss_percent']:+.2f}%")
        
        # Holdings table
        if portfolio_data['holdings']:
            holdings_df = pd.DataFrame(portfolio_data['holdings'])
            st.dataframe(holdings_df, use_container_width=True, hide_index=True)
    
    # Add new stock purchase
    st.subheader("➕ Add Stock Purchase")
    with st.form("add_stock"):
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("Stock Symbol", placeholder="NVDA")
            shares = st.number_input("Number of Shares", min_value=0.01, step=0.01)
        with col2:
            purchase_price = st.number_input("Purchase Price per Share", min_value=0.01, step=0.01)
            purchase_date = st.date_input("Purchase Date", value=datetime.now().date())
        
        if st.form_submit_button("💰 Add Purchase"):
            if symbol and shares and purchase_price:
                try:
                    # Get company name
                    stock_info = stock_tracker.get_stock_price(symbol.upper())
                    company_name = stock_info['company_name'] if stock_info else symbol.upper()
                    
                    db.insert_stock(symbol.upper(), company_name, shares, purchase_price, purchase_date)
                    st.success(f"✅ Added {shares} shares of {symbol.upper()} to portfolio!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding stock: {e}")
    
    # AI Stocks Watchlist
    st.subheader("👀 AI Stocks Watchlist")
    with st.spinner("Loading AI stock data..."):
        ai_stocks_data = stock_tracker.get_ai_stocks_overview()
    
    if ai_stocks_data:
        dashboard = FinanceDashboard()
        dashboard.display_ai_stock_watchlist(ai_stocks_data)

def show_goals(db):
    """Goals and gamification page"""
    st.header("🎯 Financial Goals")
    
    # Current goals
    goals_df = db.get_goals()
    
    if not goals_df.empty:
        st.subheader("📋 Current Goals")
        st.dataframe(goals_df, use_container_width=True, hide_index=True)
    
    # Add new goal
    st.subheader("➕ Set New Goal")
    with st.form("add_goal"):
        goal_type = st.selectbox(
            "Goal Type",
            ["Monthly Savings", "Emergency Fund", "Investment Target", "Debt Payoff", "Custom"]
        )
        target_amount = st.number_input("Target Amount ($)", min_value=1.0, step=100.0)
        target_date = st.date_input("Target Date")
        
        if st.form_submit_button("🎯 Set Goal"):
            db.update_goal(goal_type, target_amount)
            st.success(f"✅ Goal set: {goal_type} - ${target_amount:,.2f}")
            st.rerun()

def show_manual_entry(db):
    """Manual transaction entry page"""
    st.header("📝 Manual Transaction Entry")
    
    with st.form("manual_transaction"):
        col1, col2 = st.columns(2)
        
        with col1:
            transaction_date = st.date_input("Date", value=datetime.now().date())
            amount = st.number_input("Amount ($)", step=0.01)
            transaction_type = st.selectbox("Type", ["income", "expense", "transfer"])
        
        with col2:
            category = st.selectbox(
                "Category",
                ["salary", "freelance", "investment", "groceries", "dining", "gas", 
                 "utilities", "rent", "entertainment", "healthcare", "shopping", "other"]
            )
            description = st.text_input("Description", placeholder="Optional description")
        
        if st.form_submit_button("💾 Add Transaction"):
            if amount != 0:
                # Make expenses negative
                final_amount = -abs(amount) if transaction_type == "expense" else abs(amount)
                
                db.insert_transaction(
                    transaction_date,
                    final_amount,
                    category,
                    transaction_type,
                    description,
                    "manual_entry"
                )
                st.success("✅ Transaction added successfully!")
                st.rerun()

def show_settings():
    """Settings and configuration page"""
    st.header("⚙️ Settings")
    
    st.subheader("🔑 API Configuration")
    st.info("API keys should be set as environment variables for security.")
    
    # Check API key status
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))
    
    col1, col2 = st.columns(2)
    with col1:
        status = "✅ Configured" if has_openai else "❌ Not configured"
        st.write(f"**OpenAI API:** {status}")
    
    with col2:
        status = "✅ Configured" if has_anthropic else "❌ Not configured"
        st.write(f"**Anthropic API:** {status}")
    
    st.subheader("💾 Data Management")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Data"):
            # You can implement data export functionality here
            st.info("Export functionality coming soon!")
    
    with col2:
        if st.button("🗑️ Clear All Data", type="secondary"):
            st.warning("This would clear all data. Implementation needed.")
    
    st.subheader("ℹ️ About")
    st.write("""
    **Personal Finance Tracker v1.0**
    
    This app helps you track your finances and gamify your savings journey toward AI infrastructure investments.
    
    Features:
    - PDF processing with AI
    - Automated transaction categorization
    - Stock portfolio tracking
    - Gamified savings goals
    - Interactive dashboards
    """)

if __name__ == "__main__":
    main()
