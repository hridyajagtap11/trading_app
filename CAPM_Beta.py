from pages.utils.plotly_figure import interactive_plot, normalize, daily_return, calculate_beta
import streamlit as st
import datetime
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(page_title='CAPM - Beta & Return',
                   page_icon='chart_with_upwards_trend',
                   layout='wide')

# --- App Title (Updated to match image) ---
st.title('Calculate Beta and Return for Individual Stock')

# --- User Inputs ---
col1, col2 = st.columns([1, 1])
with col1:
    stock_list = ('TSLA', 'AAPL', 'NFLX', 'MSFT', 'MGM', 'AMZN', 'NVDA', 'GOOGL')
    selected_stock = st.selectbox('Choose a stock', stock_list)
with col2:
    year = st.number_input('Number of years', 1, 10, value=1)

# --- Main Logic Block ---
try:
    # --- Data Fetching ---
    end = datetime.date.today()
    start = datetime.date(datetime.date.today().year - year, datetime.date.today().month, datetime.date.today().day)
    
    SP500 = web.DataReader(['sp500'], 'fred', start, end)
    
    stocks_df = pd.DataFrame()

    data = yf.download(selected_stock, period=f'{year}y')
    stocks_df[f'{selected_stock}'] = data['Close']

    # --- Data Processing ---
    stocks_df.reset_index(inplace=True)
    SP500.reset_index(inplace=True)
    SP500.columns = ['Date', 'sp500']
    stocks_df['Date'] = stocks_df['Date'].astype('datetime64[ns]')
    stocks_df['Date'] = stocks_df['Date'].apply(lambda x: str(x)[:10])
    stocks_df['Date'] = pd.to_datetime(stocks_df['Date'])
    stocks_df = pd.merge(stocks_df, SP500, on='Date', how='inner')

    stocks_daily_return = daily_return(stocks_df)

    # --- Beta & Return Calculation ---
    beta, alpha = calculate_beta(stocks_daily_return, selected_stock)
    
    # Calculate historical annualized return for the stock
    historical_return = stocks_daily_return[selected_stock].mean() * 252

    # --- Display Results (Updated to increase font size) ---
    st.markdown(f"## **Beta :** **{beta}**")
    st.markdown(f"## **Return :** **{historical_return * 100:.2f}**")

    # --- Visualization Section (Updated to match image) ---
    fig = px.scatter(
        stocks_daily_return,
        x='sp500',
        y=selected_stock,
        title=f'{selected_stock}', # Title is now just the ticker
        labels={'sp500': 'Market Daily Returns (%)', 'stock': f'{selected_stock} Daily Returns (%)'},
        trendline='ols',
        trendline_color_override='red'
    )
    
    # Customizing the trendline name
    fig.data[1].name = 'Expected Return'
    fig.data[1].showlegend = True
    
    fig.update_layout(
        title_x=0.05, # Align title to the left
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98
        )
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"An error occurred. Please check your inputs. Error: {e}")