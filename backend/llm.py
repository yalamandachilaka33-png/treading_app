import json
from openai import OpenAI
from config import GROQ_API_KEY

def decide(asset, tf, data):
    if "error" in data:
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "Not enough data."}

    # --- 1. STRICT PYTHON RULE ENGINE (Safe gets to avoid errors) ---
    macd = data.get('MACD_Trend', 'Unknown')
    price_vs_sma = data.get('Price_vs_SMA', 'Unknown')
    rsi = data.get('RSI', 50)
    current_price = data.get('Current_Price', 0)
    
    allowed_direction = None

    if macd == "Bullish" and price_vs_sma == "Above":
        allowed_direction = "CALL"
    elif macd == "Bearish" and price_vs_sma == "Below":
        allowed_direction = "PUT"
    
    dist_to_res = data.get('Distance_to_Resistance', 999)
    dist_to_sup = data.get('Distance_to_Support', 999)
    
    near_resistance = dist_to_res < (current_price * 0.0003)
    near_support = dist_to_sup < (current_price * 0.0003)

    if allowed_direction == "CALL" and near_resistance:
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "Blocked: Uptrend but price is at Resistance."}
    if allowed_direction == "PUT" and near_support:
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "Blocked: Downtrend but price is at Support."}

    if data.get('Market_State') == "Sideways / Choppy":
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "Blocked: Market is Sideways."}
    if data.get('Reversal_Status') != "None":
        return {"signal": "NEUTRAL", "confidence": 0, "reason": f"Blocked: {data.get('Reversal_Status')} detected."}

    if rsi > 75: allowed_direction = "PUT"
    if rsi < 25: allowed_direction = "CALL"

    if not allowed_direction:
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "Trend is not clear. Waiting for setup."}

    # --- 2. LLM AS A CONFIRMER ---
    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

    prompt_text = f"""
    The technical analysis engine has already determined the trade direction is {allowed_direction}.
    The current candle is about to close in 30 seconds. Analyze this almost-complete data to predict the NEXT candle.
    
    Data: RSI={rsi}, MACD={macd}, Price is {price_vs_sma} SMA.
    Your job is to write a 1-sentence reason confirming why a {allowed_direction} trade makes sense based on this data.
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
            "reason": llm_data.get("reason", f"Trend is {macd}")
        }
    except Exception as e:
        return {"signal": allowed_direction, "confidence": 80, "reason": f"Trend Confirmed ({macd})."}
