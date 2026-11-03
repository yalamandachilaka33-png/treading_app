import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

from config import AUTH_MESSAGE, PAIRS, TF
from indicators import analyze
from llm import decide

app = FastAPI(title="Zerox Trader AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_api, _lock = None, asyncio.Lock()


async def get_api():
    """One shared PocketOption WebSocket session, created on first use."""
    global _api
    async with _lock:
        if _api is None:
            _api = PocketOptionAsync(AUTH_MESSAGE)
            await asyncio.sleep(5)
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
        raw = await api.get_candles(asset, period, period * 260)
        data = analyze(raw)
        verdict = decide(asset, tf, data)
    except Exception as e:
        raise HTTPException(502, f"{type(e).__name__}: {e}")
    return {"asset": asset, "tf": tf, **verdict, "indicators": data}


class Trade(BaseModel):
    asset: str
    amount: float
    direction: str
    duration: int


@app.post("/api/trade")
async def trade(t: Trade):
    d = t.direction.upper()
    if t.asset not in PAIRS or d not in ("CALL", "PUT") or t.amount <= 0 or t.duration <= 0:
        raise HTTPException(400, "Invalid trade")
    try:
        api = await get_api()
        fn = api.buy if d == "CALL" else api.sell
        trade_id, deal = await fn(t.asset, t.amount, t.duration * 60)
    except Exception as e:
        raise HTTPException(502, f"{type(e).__name__}: {e}")
    return {"ok": True, "trade_id": str(trade_id), "deal": deal, "demo": True}
