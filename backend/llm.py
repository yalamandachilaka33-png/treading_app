import requests
import json
from config import GEMINI_API_KEY

def decide(asset, tf, data):
    if "error" in data:
        return {"signal": "NEUTRAL", "reason": "Not enough data to analyze."}

    # Using Google Gemini REST API directly to avoid SDK bugs with new AQ keys
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

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

    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() # This will raise an error for bad status codes
        
        result_json = response.json()
        # Extract the text from the response
        result_text = result_json['candidates'][0]['content']['parts'][0]['text']
        
        # Clean the response to parse JSON properly
        result_text = result_text.strip().replace('```json', '').replace('```', '')
        parsed_result = json.loads(result_text)
        return parsed_result

    except Exception as e:
        print(f"LLM Error: {e}")
        return {"signal": "NEUTRAL", "reason": f"Error: {str(e)}"}
