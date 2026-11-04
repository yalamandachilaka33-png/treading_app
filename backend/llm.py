import json
from openai import OpenAI
from config import GROQ_API_KEY

def decide(asset, tf, data):
    if "error" in data:
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "Not enough data."}

    macd = data.get('MACD_Trend', 'Unknown')
    price_vs_sma = data.get('Price_vs_SMA', 'Unknown')
    rsi = data.get('RSI', 50)
    struct_tags = data.get('Structure_Tags', 'None')
    wicks = data.get('Candle_Wicks', 'None')

    # --- STRICT PYTHON RULE ENGINE ---
    allowed_direction = None
    if macd == "Bullish" and price_vs_sma == "Above": allowed_direction = "CALL"
    elif macd == "Bearish" and price_vs_sma == "Below": allowed_direction = "PUT"
    
    # Block fake signals based on Structure
    if "CHoCH Bearish" in struct_tags or "Double Top" in struct_tags:
         if allowed_direction == "CALL": return {"signal": "NEUTRAL", "confidence": 0, "reason": "Blocked: Bearish CHoCH/Top against uptrend."}
    if "CHoCH Bullish" in struct_tags or "Double Bottom" in struct_tags:
         if allowed_direction == "PUT": return {"signal": "NEUTRAL", "confidence": 0, "reason": "Blocked: Bullish CHoCH/Bottom against downtrend."}

    if not allowed_direction:
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "Trend is not clear. Waiting for setup."}

    # --- LLM CONFIRMATION ---
    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

    prompt_text = f"""
    The technical analysis engine has determined the trade direction is {allowed_direction}.
    Analyze this data to predict the NEXT candle.
    Data: RSI={rsi}, MACD={macd}, Structure={struct_tags}, Patterns={wicks}.
    Write a 1-sentence reason confirming why {allowed_direction} makes sense, referencing the structure tags.
    Output JSON: {{"reason": "your sentence here", "confidence": (between 70 and 95)}}
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        llm_data = json.loads(response.choices[0].message.content)
        return {
            "signal": allowed_direction,
            "confidence": llm_data.get("confidence", 80),
            "reason": llm_data.get("reason", f"Structure Confirmed ({macd})")
        }
    except Exception as e:
        return {"signal": allowed_direction, "confidence": 80, "reason": f"Trend Confirmed ({macd})."}
