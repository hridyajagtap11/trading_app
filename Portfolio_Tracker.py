import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
from db_manager import get_portfolio, add_transaction
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(page_title="Portfolio Tracker", layout="wide")
st.title("📈 My Portfolio Tracker")

# --- Authentication Check ---
if not st.session_state.get('logged_in'):
    st.warning("Please log in to manage and view your portfolio.")
else:
    username = st.session_state['username']

    # --- Add New Transaction Form ---
    st.header("Add New Transaction")
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ticker = st.text_input("Stock Ticker", placeholder="e.g., AAPL").upper()
        with col2:
            shares = st.number_input("Number of Shares", min_value=0.0001, format="%.4f")
        with col3:
            purchase_price = st.number_input("Purchase Price ($)", min_value=0.01, format="%.2f")
        with col4:
            purchase_date = st.date_input("Purchase Date", max_value=datetime.date.today())
        
        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            if ticker and shares > 0 and purchase_price > 0:
                add_transaction(username, ticker, shares, purchase_price, purchase_date)
                st.success(f"Successfully added transaction for {ticker}.")
            else:
                st.error("Please fill out all fields correctly.")

    st.markdown("---")

    # --- Portfolio Display ---
    st.header("Portfolio Overview")
    portfolio_df = get_portfolio(username)

    if portfolio_df.empty:
        st.info("Your portfolio is empty. Add a transaction above to get started.")
    else:
        tickers = portfolio_df['ticker'].unique().tolist()
        
        # Fetch current market prices for all tickers in the portfolio
        live_prices_df = yf.download(tickers, start=datetime.date.today() - datetime.timedelta(days=5), progress=False)['Close']
        
        # Get the most recent price for each ticker
        current_prices = {ticker: live_prices_df[ticker].dropna().iloc[-1] for ticker in tickers if not live_prices_df[ticker].dropna().empty}

        # --- Calculate Portfolio Metrics ---
        portfolio_df['cost_basis'] = portfolio_df['shares'] * portfolio_df['purchase_price']
        
        # Aggregate data by ticker
        summary_df = portfolio_df.groupby('ticker').agg(
            total_shares=('shares', 'sum'),
            total_cost=('cost_basis', 'sum')
        ).reset_index()
        
        summary_df['avg_purchase_price'] = summary_df['total_cost'] / summary_df['total_shares']
        summary_df['current_price'] = summary_df['ticker'].map(current_prices)
        summary_df.dropna(subset=['current_price'], inplace=True) # Drop if price fetch failed
        
        summary_df['current_value'] = summary_df['total_shares'] * summary_df['current_price']
        summary_df['gain_loss'] = summary_df['current_value'] - summary_df['total_cost']
        summary_df['gain_loss_pct'] = (summary_df['gain_loss'] / summary_df['total_cost']) * 100

        # --- Display Summary Metrics ---
        total_portfolio_value = summary_df['current_value'].sum()
        total_portfolio_cost = summary_df['total_cost'].sum()
        total_gain_loss = summary_df['gain_loss'].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Portfolio Value", f"${total_portfolio_value:,.2f}")
        col2.metric("Total Cost Basis", f"${total_portfolio_cost:,.2f}")
        col3.metric("Total Gain/Loss", f"${total_gain_loss:,.2f}", f"{((total_gain_loss / total_portfolio_cost) * 100):.2f}%" if total_portfolio_cost > 0 else "0.00%")

        # --- Visualizations & Detailed View ---
        st.markdown("---")
        tab1, tab2 = st.tabs(["📊 Asset Allocation", "📄 Detailed Holdings"])

        with tab1:
            st.subheader("Asset Allocation by Current Value")
            fig = px.pie(summary_df, names='ticker', values='current_value', title='Your Portfolio Mix')
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Detailed Holdings")
            # Format dataframe for better display
            display_df = summary_df[['ticker', 'total_shares', 'avg_purchase_price', 'current_price', 'current_value', 'gain_loss', 'gain_loss_pct']]
            display_df = display_df.rename(columns={
                'ticker': 'Ticker', 'total_shares': 'Shares', 'avg_purchase_price': 'Avg. Price',
                'current_price': 'Current Price', 'current_value': 'Current Value',
                'gain_loss': 'Gain/Loss ($)', 'gain_loss_pct': 'Gain/Loss (%)'
            })
            st.dataframe(display_df.style.format({
                'Avg. Price': '${:,.2f}', 'Current Price': '${:,.2f}', 'Current Value': '${:,.2f}',
                'Gain/Loss ($)': '${:,.2f}', 'Gain/Loss (%)': '{:.2f}%'
            }), use_container_width=True)
