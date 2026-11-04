def decide(asset, tf, data):
    if "error" in data:
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "Not enough data."}

    macd = data.get('MACD_Trend', 'Neutral')
    rsi = data.get('RSI', 50)
    struct_tags = data.get('Structure_Tags', 'None')
    wicks = data.get('Candle_Wicks', 'None')
    fib = data.get('Fib_Level', 'None')
    price_vs_sma = data.get('Price_vs_SMA', 'Above')

    score = 0
    reasons = []
    signal = "NEUTRAL"

    # 1. MACD (+30)
    if macd == "Bullish":
        signal = "CALL"
        score += 30
        reasons.append("Bullish MACD")
    elif macd == "Bearish":
        signal = "PUT"
        score += 30
        reasons.append("Bearish MACD")
    else:
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "MACD neutral."}

    # 2. SMA (+10)
    if signal == "CALL" and price_vs_sma == "Above": score += 10; reasons.append("Price>SMA")
    elif signal == "PUT" and price_vs_sma == "Below": score += 10; reasons.append("Price<SMA")

    # 3. RSI (+15)
    if signal == "CALL" and rsi < 45: score += 15; reasons.append("RSI Oversold")
    elif signal == "PUT" and rsi > 55: score += 15; reasons.append("RSI Overbought")

    # 4. Fib (+20)
    if "Support" in fib and signal == "CALL": score += 20; reasons.append("Fib Support")
    elif "Resistance" in fib and signal == "PUT": score += 20; reasons.append("Fib Resistance")

    # 5. Structure (+15)
    if signal == "CALL" and any(x in struct_tags for x in ["Bullish", "Bottom", "FVG"]): score += 15; reasons.append("Bullish Struct")
    elif signal == "PUT" and any(x in struct_tags for x in ["Bearish", "Top", "FVG"]): score += 15; reasons.append("Bearish Struct")

    # 6. Patterns (+15)
    if signal == "CALL" and any(x in wicks for x in ["Hammer", "Bullish Engulfing", "Breakout Up"]): score += 15; reasons.append("Bullish Pattern")
    elif signal == "PUT" and any(x in wicks for x in ["Shooting Star", "Bearish Engulfing", "Breakout Down"]): score += 15; reasons.append("Bearish Pattern")

    score = max(0, min(score, 95))

    if score < 50:
        return {"signal": "NEUTRAL", "confidence": score, "reason": f"Weak: {', '.join(reasons)}"}

    # Fast Reason Generation (No API Call)
    final_reason = f"{signal} setup confirmed by: {', '.join(reasons)}."
    
    return {
        "signal": signal,
        "confidence": score,
        "reason": f"{final_reason} (Score: {score}/100)"
    }
