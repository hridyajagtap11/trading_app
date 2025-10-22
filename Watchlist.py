import streamlit as st
from db_manager import get_user_watchlist, add_to_watchlist, remove_from_watchlist
import yfinance as yf
import pandas as pd

st.set_page_config(page_title='My Watchlist', layout='wide')
st.title("📈 My Watchlist")

# Ensure the user is logged in to see this page
if not st.session_state.get('logged_in'):
    st.warning("Please log in to manage your watchlist.")
else:
    username = st.session_state['username']
    
    # --- Add to Watchlist Section ---
    st.header("Add a Stock to Your Watchlist")
    new_ticker = st.text_input("Enter a Stock Ticker (e.g., AAPL)", "").upper()
    if st.button("Add Ticker"):
        if new_ticker:
            if add_to_watchlist(username, new_ticker):
                st.success(f"Added {new_ticker} to your watchlist.")
            else:
                st.info(f"{new_ticker} is already in your watchlist.")
        else:
            st.warning("Please enter a ticker symbol.")

    st.markdown("---")

    # --- Display Watchlist Section ---
    st.header("Current Watchlist")
    watchlist = get_user_watchlist(username)

    if not watchlist:
        st.info("Your watchlist is empty. Add a stock ticker above to get started.")
    else:
        # Create a table-like display with columns
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        headers = ["Ticker", "Current Price", "% Change", "Remove"]
        for header, col in zip(headers, [col1, col2, col3, col4]):
            col.markdown(f"**{header}**")
        
        # Fetch and display data for each ticker
        for ticker in watchlist:
            with col1:
                st.write(ticker)
            
            try:
                data = yf.Ticker(ticker).history(period="2d")
                if not data.empty:
                    price = data['Close'].iloc[-1]
                    prev_price = data['Close'].iloc[-2]
                    change_pct = ((price - prev_price) / prev_price) * 100
                    
                    with col2:
                        st.write(f"${price:.2f}")
                    with col3:
                        st.markdown(f"<span style='color:{'green' if change_pct >= 0 else 'red'};'>{change_pct:.2f}%</span>", unsafe_allow_html=True)
                else:
                    with col2:
                        st.write("N/A")
                    with col3:
                        st.write("N/A")

            except Exception:
                with col2:
                    st.write("Error")
                with col3:
                    st.write("Error")
            
            with col4:
                if st.button(f"🗑️", key=f"del_{ticker}"):
                    remove_from_watchlist(username, ticker)
                    st.rerun()
