#pip install -r requirements.txt
#python -m streamlit run test.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import mplfinance as mpf

def yoy_pct(current, previous):
    if previous == 0 or pd.isna(previous):
        return np.nan
    return (current - previous) / abs(previous) * 100

def to_round(value, ndigits=2):
    return round(value, ndigits) if isinstance(value, (int, float)) else "N/A"
 

# Initialize session state
if "start_date" not in st.session_state:
    #6M = Default
    st.session_state.start_date = datetime.date.today() - datetime.timedelta(days=182)
if "selected_ticker" not in st.session_state:  # Add this line
    st.session_state.selected_ticker = ""
if "day_text" not in st.session_state:
    st.session_state.day_text = "6M"


st.title("🔎 Security Analysis")

# Input for the stock ticker
ticker_input = st.text_input("Enter ticker Here ⬇️", "").upper()

# Button to trigger the search and analysis
if st.button("Search"):
    st.session_state.selected_ticker = ticker_input
    st.write("")

# Fetch stock data
today = datetime.date.today()
start_date = st.session_state.start_date
end_date = today
selected_ticker = st.session_state.selected_ticker # get the ticker
day_txt = "6M"

# Fetch and display data
if selected_ticker == "":
    st.write("")
    st.warning("Please enter the ticker to see chart and fundamental factors")

else:
        
        data = yf.download(selected_ticker, start=start_date, end=end_date)
        if data is not None and not data.empty:
            data.columns = data.columns.get_level_values(0)
            ticker = yf.Ticker(selected_ticker)  # Create yf.Ticker instance here
            price_tg = ticker.analyst_price_targets
            name = ticker.info.get('longName')
            currency = ticker.info.get('currency')
            industry = ticker.info.get('industry')
            sector = ticker.info.get('sector')

            st.write("")
            st.success(f"***NOTE:** The currency will be adjusted to match the denomination of the security. ({currency})")

            st.divider()
            
            st.markdown(f"## ⭐ {name} ({ticker_input})")
            st.write(f"➡️ **Sector**: {sector}")
            st.write(f"➡️ **Industry**: {industry}")
            with st.expander(f"About the company"):
                st.write(ticker.info.get("longBusinessSummary"))

            # Fetch analyst price targets

            diff = round(((price_tg['median']-price_tg['current'])/price_tg['current']*100),2)
            color_text = "red" if price_tg["current"] > price_tg["median"] else "green"
            signal_text = "Sell" if price_tg["current"] > price_tg["median"] else "Buy"
            

            st.divider()  
            st.markdown(f"### 💰Price ({currency})")          
            st.markdown(
                f"""
                <div>
                    <p><strong>➡️ Current Price: </strong> {round(price_tg['current'],2):,.2f}</p>
                    <p><strong>➡️ Target Price: </strong> {round(price_tg['median'],2):,.2f}</p>
                    <p><strong>➡️ Price Differential: </strong> {diff}% 
                        <span style='color:{color_text};'><strong>({signal_text})</strong></span></p>
                    
                </div>
                """,
                unsafe_allow_html=True)             
            df_download = yf.download(ticker_input, start=start_date, end=end_date)

            # Calculate EMAs
            data["EMA20"] = data["Close"].ewm(span=20, adjust=False).mean()
            data["EMA50"] = data["Close"].ewm(span=50, adjust=False).mean()

            ema20 = mpf.make_addplot(data["EMA20"], color="blue", label="EMA20", alpha = 0.5)
            ema50 = mpf.make_addplot(data["EMA50"], color="red", label="EMA50", alpha = 0.5)

            if 'median' in price_tg:
                fair_value = price_tg['median']
                fair_line = mpf.make_addplot([fair_value] * len(data), color='green', linestyle='--', label="Fair Value")

            else:
                add_plots = [ema20, ema50]
                st.warning("Analyst price target data is not available.")

            # Signal
            buy_signals = []
            sell_signals = []

            for i in range(len(data)):
                if (data['EMA20'].iloc[i] > data['EMA50'].iloc[i]) and (data['EMA20'].iloc[i-1] < data['EMA50'].iloc[i-1]):
                    buy_signals.append(data.iloc[i]['Close'] * 0.90)
                else:
                    buy_signals.append(np.nan)
                
                if (data['EMA20'].iloc[i] < data['EMA50'].iloc[i]) and (data['EMA20'].iloc[i-1] > data['EMA50'].iloc[i-1]):
                    sell_signals.append(data.iloc[i]['Close'] * 1.10)
                else:
                    sell_signals.append(np.nan)

            buy_markers = mpf.make_addplot(buy_signals, type='scatter', markersize=70, alpha = 0.5, marker='^',color='green',label="Buy")
            sell_markers = mpf.make_addplot(sell_signals, type='scatter', markersize=70, alpha = 0.5, marker='v',color='red',label="Sell")
            add_plots = [ema20, ema50, fair_line, buy_markers, sell_markers]       

            # Create the candlestick chart
            fig, axlist = mpf.plot(
                data,
                type="candle",
                style="yahoo",
                addplot=add_plots,
                mav=(200),
                volume=True,
                returnfig=True,
                figsize=(12, 6),
                
            )

            axlist[0].set_title(f"{ticker_input} - ({st.session_state.day_text})", fontsize=20, color='black', loc='left')  # loc = left, center, right

            st.divider()           
            st.markdown(f"### 📊Chart of {ticker_input} ({st.session_state.day_text})")
            #Time Range
            st.write("")         
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                if st.button("6M"):
                    st.session_state.start_date = today - datetime.timedelta(days=182)
                    st.session_state.day_text = "6M"
                    st.rerun()
            with col2:
                if st.button("YTD"):
                    st.session_state.start_date = datetime.date(today.year, 1, 1)
                    st.session_state.day_text = "YTD"
                    st.rerun()
            with col3:
                if st.button("1Y"):
                    st.session_state.start_date = today - datetime.timedelta(days=365)
                    st.session_state.day_text = "1Y"
                    st.rerun()
            with col4:
                if st.button("3Y"):
                    st.session_state.start_date = today - datetime.timedelta(days=365 * 3)
                    st.session_state.day_text = "3Y"
                    st.rerun()
            with col5:
                if st.button("Max"):
                    st.session_state.start_date = datetime.date(2000, 1, 1)
                    st.session_state.day_text = "All Time"    
                    st.rerun()  
            
            ### Plotting
            st.pyplot(fig)          
            
            df_download = yf.download(ticker_input, start=start_date, end=end_date)
            st.write("")
            if not df_download.empty:
                csv = df_download.to_csv().encode('utf-8')

                st.download_button(
                    label=f"📄 Download CSV - {ticker_input} Historical Price ({st.session_state.day_text})",
                    data=csv,
                    file_name=f"{ticker_input}_{st.session_state.day_text}_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data found for this ticker.")
            
            
            st.write("")
            st.caption(f" * **Exponential Moving Average (EMA)** is similar to Simple Moving Average (SMA), measuring trend direction over a period of time. EMA applies more weight to data that is more current.")
            st.caption(f" * **Fair value** is determined by the price at which an asset is bought or sold when both the buyer and seller freely agree on the price.")

            st.divider()    
            st.markdown("### 🪙Fundamental Index (Million)")

        else:
            st.warning("No data found for the selected ticker.")



## VI
if selected_ticker: # Check if ticker is not empty
    try:
        ticker = yf.Ticker(selected_ticker)
        income = ticker.financials.T
        info = ticker.info

        if "Total Revenue" in income.columns and "Net Income" in income.columns:
            df = income[["Total Revenue", "Net Income"]].copy()
            df = df.sort_index()
            df.index = df.index.year

            df["Prev Revenue"] = df["Total Revenue"].shift(1)
            df["Prev Net Income"] = df["Net Income"].shift(1)

            df["Revenue YoY %"] = df.apply(
                lambda row: yoy_pct(row["Total Revenue"], row["Prev Revenue"]), axis=1)
            df["Net Income YoY %"] = df.apply(
                lambda row: yoy_pct(row["Net Income"], row["Prev Net Income"]), axis=1)

            # Format numbers
            df["Total Revenue"] = (df["Total Revenue"] / 1e9).round(2)
            df["Revenue YoY %"] = df["Revenue YoY %"].round(2)
            df["Net Income"] = (df["Net Income"] / 1e6).round(2)
            df["Net Income YoY %"] = df["Net Income YoY %"].round(2)

            eps = info.get("trailingEps")      # EPS (Trailing 12 months)
            peg = info.get("pegRatio")         # PEG ratio
            debt_equity = info.get("debtToEquity")  # Debt to Equity ratio
            fcf = info.get("freeCashflow")
            shares_outstanding = info.get("sharesOutstanding")
            fcfps = fcf / shares_outstanding

            st.write("")
            st.write(f"➡️ **EPS (TTM):** {to_round(info.get('trailingEps')):,.2f}")
            st.write(f"➡️ **PEG Ratio:** {to_round(info.get('pegRatio'))}")
            st.write(f"➡️ **Debt to Equity (mrq):** {to_round(info.get('debtToEquity')/100):,.2f}")
            st.write(f"➡️ **Price to Book:** {to_round(info.get('priceToBook')):,.2f}")
            st.write(f"➡️ **Free Cash Flow per Share:** {round(fcfps,2):,.2f}")
            st.write(f"➡️ **ROE**: {round(info.get('returnOnEquity')*100,2)}%")
            st.write("")

            st.write("##### **Revenue and Income** (Last 4 Year)")
            st.dataframe(df.drop(columns=["Prev Revenue", "Prev Net Income"]).tail(4))

    except Exception as e:
        st.error(f"Error fetching financial data: {e}")
