import asyncio
import json
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from BinaryOptionsToolsV2 import PocketOptionAsync
from config import SSID, PAIRS, TF
from indicators import analyze
from llm import decide

app = FastAPI(title="Zerox Trader AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_api = None
_lock = asyncio.Lock()

async def get_api():
    global _api
    async with _lock:
        if _api is None:
            _api = PocketOptionAsync(ssid=SSID)
            await _api.__aenter__()
            await asyncio.sleep(5) # Wait for connection to stabilize
        return _api

@app.get("/api/pairs")
def pairs():
    return PAIRS

@app.get("/api/signal")
async def signal(asset: str = Query("EURUSD_otc"), tf: str = Query("1m")):
    if asset not in PAIRS or tf not in TF:
        raise HTTPException(400, "Unknown asset or timeframe")
    try:
        api = await get_api()
        period = TF[tf]
        raw = await api.get_candles(asset, period=period, count=100)
        data = analyze(raw)
        verdict = decide(asset, tf, data)
    except Exception as e:
        raise HTTPException(502, f"{type(e).__name__}: {str(e)}")
    return {"asset": asset, "tf": tf, **verdict, "indicators": data}

class Trade(BaseModel):
    asset: str
    amount: float
    direction: str
    duration: int

@app.post("/api/trade")
async def trade(t: Trade):
    d = t.direction.upper()
    if t.asset not in PAIRS or d not in ("CALL", "PUT"):
        raise HTTPException(400, "Invalid trade parameters")
    try:
        api = await get_api()
        fn = api.buy if d == "CALL" else api.sell
        trade_id, deal = await fn(t.asset, t.amount, t.duration)
    except Exception as e:
        raise HTTPException(502, f"{type(e).__name__}: {str(e)}")
    return {"ok": True, "trade_id": str(trade_id), "deal": deal}

# ---------------- NEW SCANNER ENDPOINT ----------------
@app.get("/api/scanner")
async def scanner():
    api = await get_api()
    results = []
    
    # అన్ని 15 పెయిర్స్ ని చెక్ చేయడం
    for pair in PAIRS:
        try:
            # వేగం కోసం 1 నిమిషం (60) క్యాండిల్స్ తీసుకుంటున్నాం
            raw = await api.get_candles(pair, period=60, count=100)
            data = analyze(raw)
            if "error" in data: continue
            
            verdict = decide(pair, "1m", data)
            
            # కేవలం 50% కంటే ఎక్కువ ఉన్న సిగ్నల్స్ మాత్రమే తీసుకోవడం
            if verdict.get("signal") in ["CALL", "PUT"] and verdict.get("confidence", 0) >= 50:
                results.append({
                    "pair": pair,
                    "signal": verdict["signal"],
                    "confidence": verdict["confidence"],
                    "reason": verdict["reason"]
                })
        except Exception as e:
            print(f"Scanner error on {pair}: {e}")
            continue
            
    # కాన్ఫిడెన్స్ ఎక్కువ ఉన్నవి మొదట చూపించడం
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:6] # టాప్ 6 పెయిర్స్ మాత్రమే పంపుతున్నాం
# ------------------------------------------------------

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket, asset: str = "EURUSD_otc"):
    await websocket.accept()
    try:
        api = await get_api()
        while True:
            candles = await api.get_candles(asset, period=60, count=2)
            if len(candles) >= 2:
                current_candle = candles[-1]
                price_change = abs(current_candle['close'] - current_candle['open'])
                tick_volume = int(price_change * 100000) + 10 
                
                data = {
                    "price": current_candle['close'],
                    "volume": tick_volume,
                    "time": current_candle.get('time', None)
                }
                await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
