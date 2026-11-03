import google.generativeai as genai
from config import GEMINI_API_KEY
import json

def decide(asset, tf, data):
    if "error" in data:
        return {"signal": "NEUTRAL", "reason": "Not enough data to analyze."}

    # Configure Gemini API
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
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
        response = model.generate_content(prompt)
        result_text = response.text.strip().replace('```json', '').replace('```', '')
        result_json = json.loads(result_text)
        return result_json
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"signal": "NEUTRAL", "reason": "AI analysis failed. Please try again."}
