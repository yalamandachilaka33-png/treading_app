import pandas as pd

def analyze(candles):
    if not candles or len(candles) < 50:
        return {"error": "Not enough data"}

    df = pd.DataFrame(candles)
    
    if 'open' in df.columns:
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)

    # 1. RSI (Manual Calculation)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    current_rsi = df['RSI'].iloc[-1]

    # 2. MACD (Manual Calculation)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    macd_trend = "Bullish" if df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1] else "Bearish"

    # 3. Bollinger Bands (Manual Calculation)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['STD_20'] = df['Close'].rolling(window=20).std()
    df['BBL'] = df['SMA_20'] - (2 * df['STD_20'])
    df['BBU'] = df['SMA_20'] + (2 * df['STD_20'])
    
    current_price = df['Close'].iloc[-1]
    
    if current_price < df['BBL'].iloc[-1]:
        bb_status = "Below Lower Band (Oversold)"
    elif current_price > df['BBU'].iloc[-1]:
        bb_status = "Above Upper Band (Overbought)"
    else:
        bb_status = "Inside Bands"

    # 4. Support & Resistance
    recent_high = df['High'].tail(20).max()
    recent_low = df['Low'].tail(20).min()
    
    # 5. Candle Pattern
    last_candle = df.iloc[-1]
    prev_candle = df.iloc[-2]
    pattern = "None"
    
    if (prev_candle['Close'] < prev_candle['Open']) and (last_candle['Close'] > last_candle['Open']) and (last_candle['Close'] > prev_candle['Open']):
        pattern = "Bullish Engulfing"
    elif (prev_candle['Close'] > prev_candle['Open']) and (last_candle['Close'] < last_candle['Open']) and (last_candle['Close'] < prev_candle['Open']):
        pattern = "Bearish Engulfing"

    return {
        "RSI": round(current_rsi, 2),
        "MACD_Trend": macd_trend,
        "BB_Status": bb_status,
        "Current_Price": current_price,
        "Recent_Resistance": recent_high,
        "Recent_Support": recent_low,
        "Candle_Pattern": pattern
    }
