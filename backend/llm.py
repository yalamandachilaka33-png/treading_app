import json
from openai import OpenAI
from config import GROQ_API_KEY

def decide(asset, tf, data):
    if "error" in data:
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "Not enough data."}

    # --- SCORING SYSTEM ---
    score = 0
    reasons = []
    signal = "NEUTRAL"

    macd = data.get('MACD_Trend', 'Neutral')
    rsi = data.get('RSI', 50)
    struct_tags = data.get('Structure_Tags', 'None')
    fib = data.get('Fib_Level', 'None')
    price_vs_sma = data.get('Price_vs_SMA', 'Above')

    # 1. Trend & MACD (Max +30 / -30)
    if macd == "Bullish" and price_vs_sma == "Above":
        score += 30
        signal = "CALL"
        reasons.append("Bullish MACD & Price above SMA")
    elif macd == "Bearish" and price_vs_sma == "Below":
        score += 30
        signal = "PUT"
        reasons.append("Bearish MACD & Price below SMA")
    else:
        reasons.append("MACD/SMA mixed (Choppy)")

    # 2. RSI Filter (Max +20)
    if signal == "CALL" and rsi < 40:
        score += 20
        reasons.append("RSI Oversold")
    elif signal == "PUT" and rsi > 60:
        score += 20
        reasons.append("RSI Overbought")
    elif (signal == "CALL" and rsi > 70) or (signal == "PUT" and rsi < 30):
        score -= 20 # Divergence risk
        reasons.append("RSI against trend (Risky)")

    # 3. Fibonacci Confirmation (Max +25)
    if "Support" in fib and signal == "CALL":
        score += 25
        reasons.append("Price at Fib Support")
    elif "Resistance" in fib and signal == "PUT":
        score += 25
        reasons.append("Price at Fib Resistance")

    # 4. Structure Confirmation (Max +25)
    if signal == "CALL" and ("CHoCH Bullish" in struct_tags or "BOS Bullish" in struct_tags or "Double Bottom" in struct_tags):
        score += 25
        reasons.append("Bullish Structure Confirmed")
    elif signal == "PUT" and ("CHoCH Bearish" in struct_tags or "BOS Bearish" in struct_tags or "Double Top" in struct_tags):
        score += 25
        reasons.append("Bearish Structure Confirmed")

    # --- FINAL DECISION ---
    if score < 50:
        return {"signal": "NEUTRAL", "confidence": score, "reason": f"Weak Setup: {', '.join(reasons)}"}
    
    # Ask LLM to write a nice summary
    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    prompt_text = f"""
    Based on technical data, the signal is {signal} with a score of {score}/100.
    Reasons: {', '.join(reasons)}.
    Write a short 1-sentence trading justification.
    Output JSON: {{"reason": "your sentence here"}}
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        llm_reason = json.loads(response.choices[0].message.content).get("reason", "Analysis complete.")
        final_reason = f"{llm_reason} (Score: {score}/100)"
    except:
        final_reason = f"{', '.join(reasons)} (Score: {score}/100)"

    return {
        "signal": signal,
        "confidence": min(score, 95), # Max 95%
        "reason": final_reason
    }
