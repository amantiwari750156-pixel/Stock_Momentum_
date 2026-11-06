from pathlib import Path
import sys, time
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from scanner.data_fetcher import fetch_universe, fetch_history
from scanner.indicators import add_indicators
from scanner.crossover import crossover_events, dema_crossover_events, price_crossover_events
from scanner.scanner_engine import scan_symbols
from database.database import init_db, save_scan, list_scans, get_scan_results

st.set_page_config(page_title="India Momentum Scanner", page_icon="📈", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.4rem; max-width: 1500px;}
[data-testid="stMetric"] {background: #151d2b; border: 1px solid #263247; padding: 14px; border-radius: 12px;}
[data-testid="stSidebar"] {background: #0d1421;}
.stApp {background: #0a101b;}
h1, h2, h3 {letter-spacing: -0.02em;}
div[data-testid="stDataFrame"] {border: 1px solid #263247; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)
init_db(BASE / "data" / "scans.db")

st.title("INDIA MOMENTUM SCANNER")
st.caption("NSE EQUITIES  /  TECHNICAL RESEARCH TERMINAL  /  LOCAL WORKSPACE")
top_a, top_b, top_c = st.columns([1, 1, 2])
top_a.metric("Strategy engine", "EMA + Momentum")
top_b.metric("Workspace", "LOCAL")
top_c.info("Research signals only · Adjusted historical data · No trade execution")
with st.sidebar:
    st.header("Scanner configuration")
    universe_choice = st.selectbox("Stock universe", ["NSE EQ — all available", "Nifty 50 (static list)", "First 500 NSE EQ (subset)", "Fallback sample"])
    include_sme = st.checkbox("Include SME stocks (where available)", value=False, disabled=True,
                              help="SME coverage is not reliably exposed by the free NSE equity list.")
    consolidation = st.selectbox("Consolidation period", ["100 trading days", "200 trading days", "1 year (252 sessions)", "No consolidation filter"])
    max_cons = st.slider("Maximum consolidation range (%)", 5, 50, 20, 1)
    st.subheader("Moving-average crossover")
    crossovers = st.multiselect("Bullish EMA crossover conditions", ["50/100", "50/200", "100/200"], default=["50/100", "50/200", "100/200"])
    dema_crossovers = st.multiselect("50 DEMA vs EMA bullish crossovers", ["DEMA50/EMA100", "DEMA50/EMA50", "DEMA50/EMA200"], default=[])
    st.subheader("Price crossover")
    price_direction = st.selectbox("Price crossover direction", ["Bullish (price crosses above)", "Bearish (price crosses below)", "Both directions"])
    price_direction_code = {"Bullish (price crosses above)": "BULLISH", "Bearish (price crosses below)": "BEARISH", "Both directions": "BOTH"}[price_direction]
    price_choices = []
    for average in ["DEMA50", "EMA50", "EMA100", "EMA200"]:
        if price_direction_code in ("BULLISH", "BOTH"):
            price_choices.append(f"Price/{average} ABOVE")
        if price_direction_code in ("BEARISH", "BOTH"):
            price_choices.append(f"Price/{average} BELOW")
    price_crossovers = st.multiselect("Find stocks where price crossed", price_choices, default=[])
    cross_mode = st.radio("Selected signal matching", ["ANY", "ALL"], horizontal=True,
                          help="ANY = at least one selected crossover occurred. ALL = every selected crossover occurred within the lookback.")
    lookback = st.select_slider("Crossover lookback (trading sessions)", options=[1,3,5,10,20], value=5)
    st.divider()
    use_rsi = st.checkbox("Enable RSI filter", value=True)
    rsi_min, rsi_max = st.slider("RSI range", 0, 100, (50, 70))
    use_volume = st.checkbox("Enable volume confirmation", value=False)
    volume_mult = st.slider("Minimum volume / 20D average", 0.5, 5.0, 1.5, 0.1)
    use_trend = st.checkbox("Enable trend confirmation", value=False)
    ema_rising = st.checkbox("Require rising 200 EMA", value=False, disabled=not use_trend)
    use_liquidity = st.checkbox("Enable liquidity filters", value=False)
    min_avg_vol = st.number_input("Minimum average daily volume (shares)", min_value=0, value=100000, step=50000, disabled=not use_liquidity)
    min_avg_value = st.number_input("Minimum average traded value (₹)", min_value=0, value=10000000, step=1000000, disabled=not use_liquidity)
    min_price = st.number_input("Minimum stock price (₹)", min_value=0.0, value=10.0, step=5.0)
    use_strength = st.checkbox("Enable price-strength filter", value=False)
    min_1m = st.number_input("Minimum 1-month return (%)", value=0.0, step=1.0, disabled=not use_strength)
    min_3m = st.number_input("Minimum 3-month return (%)", value=0.0, step=1.0, disabled=not use_strength)
    st.divider()
    max_symbols = st.number_input("Maximum stocks to scan (0 = all)", min_value=0, value=0, step=100,
                                  help="Useful for a quicker test run. Zero scans the selected universe.")

cfg = {"consolidation_period": consolidation, "max_consolidation": max_cons,
       "crossovers": crossovers, "dema_crossovers": dema_crossovers,
       "price_crossovers": price_crossovers, "price_cross_direction": price_direction_code,
       "crossover_mode": cross_mode, "lookback": lookback,
       "use_rsi": use_rsi, "rsi_min": rsi_min, "rsi_max": rsi_max,
       "use_volume": use_volume, "volume_multiplier": volume_mult,
       "use_trend": use_trend, "ema200_rising": ema_rising,
       "use_liquidity": use_liquidity, "min_avg_volume": min_avg_vol, "min_avg_value": min_avg_value,
       "min_price": min_price, "use_price_strength": use_strength,
       "min_1m_return": min_1m, "min_3m_return": min_3m}

tab_scan, tab_chart, tab_history, tab_data = st.tabs(["Scanner", "Stock chart", "Scan history", "Data & methodology"])
with tab_scan:
    c1, c2 = st.columns([1, 3])
    with c1:
        refresh_universe = st.button("Refresh NSE stock list")
    with c2:
        st.caption("The NSE list is cached locally. Yahoo Finance data is fetched on scan and can be rate-limited.")
    universe = fetch_universe(BASE / "data" / "stock_universe.csv", refresh=refresh_universe)
    if universe.attrs.get("universe_warning"):
        st.warning(universe.attrs["universe_warning"])
    symbols = universe["SYMBOL"].astype(str).str.strip()
    if universe_choice == "Nifty 50 (static list)":
        nifty = ["ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BEL","BHARTIARTL","CIPLA","COALINDIA","DRREDDY","EICHERMOT","ETERNAL","GRASIM","HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO","HINDUNILVR","ICICIBANK","INDUSINDBK","INFY","ITC","JIOFIN","JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","NESTLEIND","NTPC","ONGC","POWERGRID","RELIANCE","SBILIFE","SBIN","SHRIRAMFIN","SUNPHARMA","TATACONSUM","TATASTEEL","TCS","TECHM","TITAN","TRENT","ULTRACEMCO","WIPRO"]
        universe = universe[universe["SYMBOL"].isin(nifty)]
    elif universe_choice == "First 500 NSE EQ (subset)":
        st.info("This is the first 500 rows of the available NSE EQ list, not verified Nifty 500 index membership.")
        universe = universe.head(500)
    elif universe_choice == "Fallback sample":
        sample = ["RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","ITC","SBIN","BHARTIARTL","LT","AXISBANK","KOTAKBANK","SUNPHARMA","MARUTI","TATAMOTORS","NTPC"]
        universe = universe[universe["SYMBOL"].isin(sample)]
    if max_symbols:
        universe = universe.head(int(max_symbols))
    st.write(f"Universe loaded: **{len(universe):,} stocks**")
    force_refresh = st.checkbox("Force refresh downloaded price history", value=False,
                                help="Bypass the local cache and request fresh history from Yahoo Finance.")
    if st.button("▶ Run momentum scan", type="primary", use_container_width=True):
        progress = st.progress(0.0, text="Preparing scan…")
        status = st.empty()
        def update(p, message):
            progress.progress(min(p, 1.0), text=message)
            status.caption(message)
        with st.spinner("Downloading data and calculating indicators. A full-universe scan can take a while."):
            results, failures = scan_symbols(universe, cfg, update, refresh=force_refresh)
        scan_id = save_scan(results, cfg, BASE / "data" / "scans.db")
        st.session_state["results"] = results
        st.session_state["failures"] = failures
        st.session_state["last_scan_id"] = scan_id
        st.session_state["last_scan_time"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        progress.progress(1.0, text="Scan complete")
    if "results" in st.session_state:
        results = st.session_state["results"]
        failures = st.session_state.get("failures", pd.DataFrame())
        m1,m2,m3 = st.columns(3)
        m1.metric("Qualifying stocks", len(results))
        m2.metric("Download / quality failures", len(failures))
        m3.metric("Last scan", st.session_state.get("last_scan_time", "—"))
        if not results.empty:
            preferred = ["Stock Symbol","Company Name","Current Price","DEMA 50","EMA 50","EMA 100","EMA 200","Price vs DEMA50","Price vs EMA50","Price vs EMA100","Price vs EMA200","Crossover Signal","Crossover Date","RSI","Volume Ratio","Consolidation Period","Consolidation Range %","Consolidation High","Consolidation Low","Distance from High %","Distance from Low %","1M Return %","3M Return %","6M Return %","Relative Strength %","Data Date"]
            display = results[[c for c in preferred if c in results.columns]].copy()
            st.dataframe(display, use_container_width=True, hide_index=True,
                         column_config={"Current Price": st.column_config.NumberColumn(format="₹%.2f"),
                                        "Consolidation Range %": st.column_config.NumberColumn(format="%.2f%%"),
                                        "RSI": st.column_config.NumberColumn(format="%.1f"),
                                        "Volume Ratio": st.column_config.NumberColumn(format="%.2fx")})
            st.download_button("Download qualifying stocks (CSV)", results.to_csv(index=False).encode("utf-8"),
                               file_name=f"momentum_scan_{pd.Timestamp.now():%Y%m%d_%H%M}.csv", mime="text/csv")
        else:
            st.info("No stocks met the selected conditions. Relax filters or widen the crossover lookback.")
        if not failures.empty:
            with st.expander(f"Data-quality / failed-download report ({len(failures)})"):
                st.dataframe(failures, use_container_width=True, hide_index=True)
                st.download_button("Download failure report", failures.to_csv(index=False).encode("utf-8"),
                                   file_name="scan_failures.csv", mime="text/csv")
with tab_chart:
    st.subheader("Individual stock chart")
    symbol_input = st.text_input("NSE symbol", value="RELIANCE").strip().upper()
    if st.button("Load stock chart"):
        try:
            raw = fetch_history(symbol_input, period="3y", cache_dir=BASE / "data" / "price_cache")
            chart_df = add_indicators(raw).dropna(subset=["DEMA50","EMA50","EMA100","EMA200"])
            st.session_state["chart_df"] = chart_df
            st.session_state["chart_symbol"] = symbol_input
        except Exception as exc:
            st.error(f"Could not load {symbol_input}: {exc}")
    if "chart_df" in st.session_state:
        df = st.session_state["chart_df"]
        sym = st.session_state["chart_symbol"]
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=.04,
                            row_heights=[.75,.25], specs=[[{"secondary_y": False}],[{"secondary_y": False}]])
        fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name="Price"), row=1,col=1)
        for col in ["DEMA50", "EMA50", "EMA100", "EMA200"]:
            fig.add_trace(go.Scatter(x=df.index,y=df[col],name=col,mode="lines"),row=1,col=1)
        marker_events = {}
        marker_events.update(crossover_events(df, 20))
        marker_events.update(dema_crossover_events(df, 20))
        marker_events.update(price_crossover_events(df, 20, "BOTH"))
        for signal, cross_date in marker_events.items():
            if cross_date is not None and cross_date in df.index:
                fig.add_trace(go.Scatter(x=[cross_date], y=[df.loc[cross_date, "Close"]],
                                         mode="markers+text", text=[signal],
                                         textposition="top center", name=signal,
                                         marker={"size": 10, "symbol": "triangle-up"}), row=1, col=1)
        if consolidation != "No consolidation filter":
            n = {"100 trading days":100,"200 trading days":200,"1 year (252 sessions)":252}[consolidation]
            recent = df.tail(n)
            fig.add_hline(y=recent.High.max(), line_dash="dash", annotation_text="Consolidation high", row=1,col=1)
            fig.add_hline(y=recent.Low.min(), line_dash="dash", annotation_text="Consolidation low", row=1,col=1)
        fig.add_trace(go.Bar(x=df.index,y=df.Volume,name="Volume"),row=2,col=1)
        fig.update_layout(title=f"{sym} — adjusted daily price and EMA", height=750, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        rsi_fig = go.Figure(go.Scatter(x=df.index,y=df.RSI,name="RSI 14"))
        rsi_fig.add_hline(y=70,line_dash="dash"); rsi_fig.add_hline(y=30,line_dash="dash")
        rsi_fig.update_layout(title="14-day RSI",height=250)
        st.plotly_chart(rsi_fig,use_container_width=True)
        st.caption(f"Latest data date: {df.index[-1].date()} • Adjusted historical prices • Yahoo Finance unofficial")
with tab_history:
    st.subheader("Saved local scans")
    history = list_scans(BASE / "data" / "scans.db")
    if history.empty:
        st.info("No saved scans yet. Run a scan to create the first history record.")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)
        selected_id = st.selectbox("Inspect saved scan ID", history["id"].astype(int).tolist())
        past = get_scan_results(int(selected_id), BASE / "data" / "scans.db")
        st.dataframe(past, use_container_width=True, hide_index=True)
with tab_data:
    st.subheader("Data source and calculation notes")
    st.markdown("""
- **Historical data:** Yahoo Finance via `yfinance`; unofficial, may be delayed, incomplete, throttled or unavailable for some securities.
- **Universe:** NSE public equity CSV where accessible; cached locally. The standard file filters to EQ series. SME coverage is not guaranteed.
- **Prices:** `auto_adjust=True` adjusted OHLCV series, consistently used for technical calculations.
- **EMA:** Exponential moving average with `adjust=False`; 50, 100 and 200 trading observations.
- **DEMA 50:** Double EMA, calculated as `2 × EMA50 − EMA(EMA50, 50)`.
- **Moving-average crossover:** Fresh bullish event where the prior fast average was at/below the slow average and the current fast average is above it. The scanner supports EMA 50/100, 50/200, 100/200 and DEMA50 against EMA100, EMA50 and EMA200.
- **Price crossover:** Fresh close-price cross above or below DEMA50, EMA50, EMA100 or EMA200. The lookback is measured in trading sessions.
- **RSI:** 14-period Wilder-style exponentially smoothed RSI.
- **Consolidation:** (highest high − lowest low) / average closing price × 100, over the selected number of trading sessions.
- **Volume ratio:** Latest session volume divided by the 20-session average volume.
- **Relative strength:** 3-month stock return less 3-month Nifty 50 return, in percentage points.
- **No look-ahead:** Indicators use data through the latest downloaded session only.
- **Breakouts:** This version measures consolidation; it does not label a breakout unless a separate breakout rule is implemented.
""")
    st.warning("This is a screening and research tool, not investment advice or an order-management system. Verify signals, corporate actions, liquidity and data quality independently.")
