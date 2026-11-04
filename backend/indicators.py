import pandas as pd

# --- Helper Functions for Advanced Logic ---
def rsi_calc(s, n=14):
    if len(s) < n: return 50.0
    g_avg = l_avg = 0.0
    for i in range(1, len(s)):
        d = s[i] - s[i - 1]
        g, l = max(d, 0), max(-d, 0)
        if i <= n:
            g_avg += g
            l_avg += l
            if i == n:
                g_avg /= n
                l_avg /= n
        else:
            g_avg = (g_avg * (n - 1) + g) / n
            l_avg = (l_avg * (n - 1) + l) / n
    return 100.0 if l_avg == 0 else 100 - 100 / (1 + g_avg / l_avg)

def ema_series(s, n):
    k = 2 / (n + 1)
    e = s[0]
    out = [e]
    for x in s[1:]:
        e = k * x + (1 - k) * e
        out.append(e)
    return out

def macd_full(close):
    e12 = ema_series(close, 12)
    e26 = ema_series(close, 26)
    m = [x - y for x, y in zip(e12, e26)]
    sg = ema_series(m, 9)
    return m, sg

def bb_calc(close, n=20, k=2):
    if len(close) < n: return close[-1], close[-1], close[-1]
    w = close[-n:]
    mid = sum(w) / len(w)
    sd = (sum((x - mid) ** 2 for x in w) / len(w)) ** 0.5
    return mid, mid + k * sd, mid - k * sd

def swings(cl, k=2):
    hs, ls = [], []
    for i in range(k, len(cl) - k):
        h = cl[i]["High"]
        l = cl[i]["Low"]
        if all(h > cl[i - j]["High"] and h > cl[i + j]["High"] for j in range(1, k + 1)): hs.append((i, h))
        if all(l < cl[i - j]["Low"] and l < cl[i + j]["Low"] for j in range(1, k + 1)): ls.append((i, l))
    return hs, ls

def structure_calc(cl, avg_rng):
    tags = []
    n = len(cl)
    if n < 30 or avg_rng <= 0: return tags
    c1, c2, c3 = cl[-1], cl[-2], cl[-3]
    if c1["Low"] > c3["High"] and c2["Close"] > c2["Open"]: tags.append(("FVG Bullish", 1))
    elif c1["High"] < c3["Low"] and c2["Close"] < c2["Open"]: tags.append(("FVG Bearish", -1))
    
    hs, ls = swings(cl)
    tol = 0.5 * avg_rng
    if len(ls) >= 2:
        (i1, l1), (i2, l2) = ls[-2], ls[-1]
        if 4 <= i2 - i1 <= 40 and abs(l1 - l2) <= tol and i2 >= n - 12 and c1["Close"] > max(l1, l2): tags.append(("Double Bottom", 1))
    if len(hs) >= 2:
        (i1, h1), (i2, h2) = hs[-2], hs[-1]
        if 4 <= i2 - i1 <= 40 and abs(h1 - h2) <= tol and i2 >= n - 12 and c1["Close"] < min(h1, h2): tags.append(("Double Top", -1))
    
    if len(hs) >= 2 and len(ls) >= 2:
        up = hs[-1][1] > hs[-2][1] and ls[-1][1] > ls[-2][1]
        down = hs[-1][1] < hs[-2][1] and ls[-1][1] < ls[-2][1]
        lh, ll = hs[-1][1], ls[-1][1]
        if c1["Close"] > lh and c2["Close"] <= lh:
            if up: tags.append(("BOS Bullish", 1))
            elif down: tags.append(("CHoCH Bullish", 1))
        if c1["Close"] < ll and c2["Close"] >= ll:
            if down: tags.append(("BOS Bearish", -1))
            elif up: tags.append(("CHoCH Bearish", -1))
    return tags

def pattern_calc(cl, rsi, pb, avg_rng):
    ents = []
    if len(cl) < 25: return 0, []
    def parts(c):
        r = c["High"] - c["Low"]
        if r <= 0: return None
        b = abs(c["Close"] - c["Open"])
        return (r, b, c["High"] - max(c["Open"], c["Close"]), min(c["Open"], c["Close"]) - c["Low"], c["Close"] > c["Open"])
    
    c1, c2, c3 = cl[-1], cl[-2], cl[-3]
    p1, p2, p3 = parts(c1), parts(c2), parts(c3)
    if p1 and p2:
        r1, b1, u1, l1, g1 = p1
        r2, b2, u2, l2, g2 = p2
        low_z = pb <= 0.3 or rsi <= 40
        high_z = pb >= 0.7 or rsi >= 60
        if b1 > 0 and l1 >= 2 * b1 and u1 <= 0.3 * r1: ents.append((35 if low_z else 12, "Hammer"))
        if b1 > 0 and u1 >= 2 * b1 and l1 <= 0.3 * r1: ents.append((-35 if high_z else -12, "Shooting Star"))
        if g1 and (not g2) and c1["Close"] >= c2["Open"] and c1["Open"] <= c2["Close"] and b1 > b2: ents.append((35 if low_z else 15, "Bullish Engulfing"))
        if (not g1) and g2 and c1["Close"] <= c2["Open"] and c1["Open"] >= c2["Close"] and b1 > b2: ents.append((-35 if high_z else -15, "Bearish Engulfing"))
    
    rs = [c["Close"] for c in cl]
    mp, upp, lop = bb_calc(rs)
    if c1["High"] - c1["Low"] > 0 and avg_rng > 0:
        if c1["Close"] > upp and c1["Close"] > c1["Open"]: ents.append((30, "Breakout Up"))
        elif c1["Close"] < lop and c1["Close"] < c1["Open"]: ents.append((-30, "Breakout Down"))

    ents.sort(key=lambda e: -abs(e[0]))
    tot = max(-80, min(80, sum(e[0] for e in ents)))
    return tot, [e[1] for e in ents]

# --- MAIN FUNCTION ---
def analyze(candles):
    if not candles or len(candles) < 50:
        return {"error": "Not enough data"}

    df = pd.DataFrame(candles)
    if 'open' in df.columns:
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)

    cl = df.to_dict('records')
    close_prices = df['Close'].tolist()
    current_price = close_prices[-1]

    rsi = rsi_calc(close_prices)
    macd_line, macd_signal = macd_full(close_prices)
    macd_trend = "Bullish" if macd_line[-1] > macd_signal[-1] else "Bearish"
    mid, up, lo = bb_calc(close_prices)
    pb = (current_price - lo) / (up - lo) if up > lo else 0.5
    
    bb_status = "Inside Bands"
    if current_price < lo: bb_status = "Oversold"
    elif current_price > up: bb_status = "Overbought"

    rngs = [c["High"] - c["Low"] for c in cl[-21:-1]]
    avg_rng = sum(rngs) / len(rngs) if rngs else 0
    
    tags = structure_calc(cl, avg_rng)
    psc, pn = pattern_calc(cl, rsi, pb, avg_rng)
    pat_txt = ", ".join(pn) if pn else "None"

    recent_high = max(c["High"] for c in cl[-30:])
    recent_low = min(c["Low"] for c in cl[-30:])

    return {
        "RSI": round(rsi, 2),
        "MACD_Trend": macd_trend,
        "BB_Status": bb_status,
        "Current_Price": current_price,
        "Support": round(recent_low, 5),
        "Resistance": round(recent_high, 5),
        "Candle_Wicks": pat_txt,
        "Structure_Tags": ", ".join([t[0] for t in tags]) if tags else "None",
        "Price_vs_SMA": "Above" if current_price > mid else "Below",
        "Distance_to_Support": round(current_price - recent_low, 5),
        "Distance_to_Resistance": round(recent_high - current_price, 5)
    }
