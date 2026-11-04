import pandas as pd

def analyze(candles):
    if not candles or len(candles) < 50:
        return {"error": "Not enough data"}

    df = pd.DataFrame(candles)
    if 'open' in df.columns:
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)

    # 1. Indicators
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    current_rsi = df['RSI'].iloc[-1]

    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    macd_trend = "Bullish" if df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1] else "Bearish"

    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['STD_20'] = df['Close'].rolling(window=20).std()
    df['BBL'] = df['SMA_20'] - (2 * df['STD_20'])
    df['BBU'] = df['SMA_20'] + (2 * df['STD_20'])
    current_price = df['Close'].iloc[-1]
    
    bb_status = "Inside Bands"
    if current_price < df['BBL'].iloc[-1]: bb_status = "Oversold"
    elif current_price > df['BBU'].iloc[-1]: bb_status = "Overbought"

    # 2. Candle Body & Wicks
    last_candle = df.iloc[-1]
    body_size = abs(last_candle['Close'] - last_candle['Open'])
    total_size = last_candle['High'] - last_candle['Low']
    upper_wick = last_candle['High'] - max(last_candle['Close'], last_candle['Open'])
    lower_wick = min(last_candle['Close'], last_candle['Open']) - last_candle['Low']

    wick_analysis = "Normal"
    if total_size > 0:
        if lower_wick > (body_size * 2) and upper_wick < body_size: wick_analysis = "Hammer"
        elif upper_wick > (body_size * 2) and lower_wick < body_size: wick_analysis = "Shooting Star"
        elif body_size < (total_size * 0.1): wick_analysis = "Doji"

    # 3. Market State (Sideways)
    bb_width = (df['BBU'].iloc[-1] - df['BBL'].iloc[-1]) / df['SMA_20'].iloc[-1]
    market_state = "Trending"
    if bb_width < 0.001: 
        market_state = "Sideways / Choppy"

    # 4. Support & Resistance / Breakout
    recent_high = df['High'].tail(30).max()
    recent_low = df['Low'].tail(30).min()
    
    breakout = "None"
    if current_price > recent_high: breakout = "Bullish Breakout"
    elif current_price < recent_low: breakout = "Bearish Breakout"

    # 5. Reversal Logic
    prev_price = df['Close'].iloc[-5]
    prev_rsi = df['RSI'].iloc[-5]
    reversal = "None"
    if current_price > prev_price and current_rsi < prev_rsi: reversal = "Bearish Divergence"
    elif current_price < prev_price and current_rsi > prev_rsi: reversal = "Bullish Divergence"

    return {
        "RSI": round(current_rsi, 2),
        "MACD_Trend": macd_trend,
        "BB_Status": bb_status,
        "Current_Price": current_price,
        "Support": round(recent_low, 5),
        "Resistance": round(recent_high, 5),
        "Candle_Wicks": wick_analysis,
        "Market_State": market_state,
        "Breakout_Status": breakout,
        "Reversal_Status": reversal,
        "Price_vs_SMA": "Above" if current_price > df['SMA_20'].iloc[-1] else "Below",
        "Distance_to_Support": round(current_price - recent_low, 5),
        "Distance_to_Resistance": round(recent_high - current_price, 5)
    }
