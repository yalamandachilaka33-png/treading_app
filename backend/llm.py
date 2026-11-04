import json
from openai import OpenAI
from config import GROQ_API_KEY

def decide(asset, tf, data):
    if "error" in data:
        return {"signal": "NEUTRAL", "confidence": 0, "reason": "Not enough data."}

    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

    prompt_text = f"""
    You are an expert binary options trader. Analyze this data for {asset} on {tf} timeframe:
    - Current Price: {data['Current_Price']}
    - RSI (14): {data['RSI']}
    - MACD Trend: {data['MACD_Trend']}
    - Bollinger Bands: {data['BB_Status']}
    - Support: {data['Recent_Support']}, Resistance: {data['Recent_Resistance']}
    - Candle Pattern: {data['Candle_Pattern']}

    Based on this data, provide a trading signal.
    Your response MUST strictly follow this JSON format:
    {{
        "signal": "CALL" or "PUT" or "NEUTRAL",
        "confidence": (An integer between 0 and 100 representing your confidence level, e.g., 85),
        "reason": "A short 1-sentence explanation."
    }}
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You only output JSON."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"signal": "NEUTRAL", "confidence": 0, "reason": str(e)}
