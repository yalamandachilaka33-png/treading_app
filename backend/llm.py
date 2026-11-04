import json
from openai import OpenAI
from config import GROQ_API_KEY

def decide(asset, tf, data):
    if "error" in data:
        return {"signal": "NEUTRAL", "reason": "Not enough data to analyze."}

    # Initialize Groq client
    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )

    prompt_text = f"""
    You are an expert binary options trader. Analyze the following data for {asset} on {tf} timeframe:
    - Current Price: {data['Current_Price']}
    - RSI (14): {data['RSI']}
    - MACD Trend: {data['MACD_Trend']}
    - Bollinger Bands: {data['BB_Status']}
    - Support Level: {data['Recent_Support']}
    - Resistance Level: {data['Recent_Resistance']}
    - Candle Pattern: {data['Candle_Pattern']}

    Based on this data, provide a trading signal.
    Your response MUST strictly follow this JSON format:
    {{
        "signal": "CALL" or "PUT" or "NEUTRAL",
        "reason": "A short 1-sentence explanation of why."
    }}
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are a helpful trading assistant that only outputs JSON."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        return result_json
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"signal": "NEUTRAL", "reason": str(e)}
