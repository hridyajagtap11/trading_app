import streamlit as st
from authenticator import check_password, create_user
from db_manager import create_tables, get_portfolio
import yfinance as yf
import datetime
import pandas as pd

# --- Initialize Database ---
create_tables()

# --- Page Configuration ---
st.set_page_config(
    page_title='Trading Guide App',
    page_icon='📈',
    layout='wide'
)

# --- THEME: Hot Pink & Onyx (Dark Theme) ---
# A modern, high-contrast theme with a black background and pink accents.
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background-color: #121212; /* Onyx Black */
        color: #E0E0E0; /* Light Gray Text */
    }
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1E1E1E; /* Slightly Lighter Black */
    }
    /* Metric styling */
    .stMetric {
        background-color: #2C2C2C; /* Dark Gray */
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 15px;
    }
    /* Button styling */
    .stButton>button {
        background-color: #E91E63; /* Hot Pink */
        color: #FFFFFF; /* White text */
        font-weight: bold;
        border-radius: 8px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #C2185B; /* Darker Pink on hover */
        color: #FFFFFF;
        border: none;
    }
    /* Titles and Headers */
    h1, h2, h3 {
        color: #FFFFFF; /* White */
    }
    /* Main title accent */
    h1 {
        color: #E91E63; /* Hot Pink */
    }
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

# --- Login/Signup Interface ---
if not st.session_state['logged_in']:
    st.title("Welcome to the Trading Guide App")
    st.markdown("Your ultimate platform to empower investment decisions.")
    
    choice = st.selectbox("Login or Signup", ["Login", "Signup"])

    if choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if check_password(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    else:
        st.subheader("Create a New Account")
        new_username = st.text_input("Choose a Username")
        new_password = st.text_input("Choose a Password", type="password")
        
        if st.button("Signup"):
            if create_user(new_username, new_password):
                st.success("Account created successfully! Please login.")
            else:
                st.error("Username already exists.")

# --- Main Application Dashboard (Shown after login) ---
else:
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
    st.title("📈 Dashboard")
    st.markdown("---")

    # --- Market Overview Section ---
    st.header("Market Overview")
    market_tickers = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "Dow Jones": "^DJI"
    }
    
    cols = st.columns(len(market_tickers))
    for i, (name, ticker) in enumerate(market_tickers.items()):
        try:
            data = yf.Ticker(ticker).history(period="2d")
            if not data.empty:
                price = data['Close'].iloc[-1]
                delta = data['Close'].diff().iloc[-1]
                cols[i].metric(label=name, value=f"{price:,.2f}", delta=f"{delta:,.2f}")
        except Exception:
            cols[i].metric(label=name, value="N/A", delta="Error")

    st.markdown("---")

    # --- Portfolio Snapshot Section ---
    st.header("Your Portfolio Snapshot")
    portfolio_df = get_portfolio(st.session_state['username'])

    if portfolio_df.empty:
        st.info("Your portfolio is empty. Navigate to the 'Portfolio Tracker' page from the sidebar to add your first transaction.")
    else:
        tickers = portfolio_df['ticker'].unique().tolist()
        live_prices_df = yf.download(tickers, start=datetime.date.today() - datetime.timedelta(days=5), progress=False)['Close']
        current_prices = {ticker: live_prices_df[ticker].dropna().iloc[-1] for ticker in tickers if not live_prices_df[ticker].dropna().empty}

        portfolio_df['cost_basis'] = portfolio_df['shares'] * portfolio_df['purchase_price']
        summary_df = portfolio_df.groupby('ticker').agg(total_cost=('cost_basis', 'sum')).reset_index()
        summary_df['current_price'] = summary_df['ticker'].map(current_prices)
        summary_df.dropna(subset=['current_price'], inplace=True)
        
        # We need total shares from the original df for current value calculation
        shares_summary = portfolio_df.groupby('ticker')['shares'].sum().reset_index()
        summary_df = pd.merge(summary_df, shares_summary, on='ticker')

        summary_df['current_value'] = summary_df['shares'] * summary_df['current_price']
        
        total_portfolio_value = summary_df['current_value'].sum()
        total_portfolio_cost = summary_df['total_cost'].sum()
        total_gain_loss = total_portfolio_value - total_portfolio_cost
        
        p_col1, p_col2, p_col3 = st.columns(3)
        p_col1.metric("Total Portfolio Value", f"${total_portfolio_value:,.2f}")
        p_col2.metric("Total Cost Basis", f"${total_portfolio_cost:,.2f}")
        p_col3.metric("Total Gain/Loss", f"${total_gain_loss:,.2f}", f"{((total_gain_loss / total_portfolio_cost) * 100):.2f}%" if total_portfolio_cost > 0 else "0.00%")

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.rerun()