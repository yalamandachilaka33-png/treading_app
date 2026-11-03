import { useEffect, useRef, useState } from "react";

const TFS = { "1m": 60, "2m": 120, "3m": 180, "5m": 300 };
const PAIRS = ["EURUSD_otc","GBPUSD_otc","USDJPY_otc","AUDUSD_otc","USDCAD_otc","USDCHF_otc","NZDUSD_otc","EURGBP_otc","EURJPY_otc","GBPJPY_otc","AUDJPY_otc","AUDCAD_otc","CADJPY_otc","CHFJPY_otc","EURCHF_otc"];
const SIG = {
  CALL: "bg-neongreen/15 text-neongreen border-neongreen shadow-[0_0_28px_#00ff9d77]",
  PUT: "bg-neonred/15 text-neonred border-neonred shadow-[0_0_28px_#ff3b5c77]",
  NEUTRAL: "bg-gray-500/15 text-gray-300 border-gray-500",
};

function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [0, 0.25, 0.5].forEach((t) => {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.frequency.value = 880; o.connect(g); g.connect(ctx.destination);
      g.gain.setValueAtTime(0.2, ctx.currentTime + t);
      o.start(ctx.currentTime + t); o.stop(ctx.currentTime + t + 0.15);
    });
    navigator.vibrate?.([200, 100, 200]);
  } catch {}
}

export default function App() {
  const [asset, setAsset] = useState(PAIRS[0]);
  const [tf, setTf] = useState("1m");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  const [amount, setAmount] = useState(10);
  const [duration, setDuration] = useState(1);
  const [remaining, setRemaining] = useState(60);
  const [warn, setWarn] = useState(false);
  const [msg, setMsg] = useState("");
  const alerted = useRef(false);

  useEffect(() => {
    alerted.current = false; setWarn(false);
    const secs = TFS[tf];
    const id = setInterval(() => {
      const rem = Math.ceil(secs - ((Date.now() / 1000) % secs));
      setRemaining(rem);
      if (rem <= 30 && !alerted.current) { alerted.current = true; setWarn(true); beep(); }
      if (rem > 30 && alerted.current) { alerted.current = false; setWarn(false); }
    }, 250);
    return () => clearInterval(id);
  }, [tf]);

  async function generate() {
    setLoading(true); setErr(""); setRes(null);
    try {
      const r = await fetch(`/api/signal?asset=${asset}&tf=${tf}`);
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "Request failed");
      setRes(j);
    } catch (e) { setErr(e.message); }
    setLoading(false);
  }

  async function trade(direction) {
    if (!window.confirm(`${direction} $${amount} on ${asset} for ${duration}m?`)) return;
    try {
      const r = await fetch("/api/trade", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ asset, amount: Number(amount), direction, duration: Number(duration) }) });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "Trade failed");
      setMsg(`✅ ${direction} placed (id ${j.trade_id})`);
    } catch (e) { setMsg("❌ " + e.message); }
    setTimeout(() => setMsg(""), 5000);
  }

  const mm = String(Math.floor(remaining / 60)).padStart(2, "0"), ss = String(remaining % 60).padStart(2, "0");
  const card = "mt-4 rounded-2xl border border-[#14304a] bg-panel p-4 shadow-[0_0_18px_#00d4ff22]";
  const input = "w-full rounded-xl border border-[#1d3a57] bg-[#0a1220] p-3 text-base text-white outline-none focus:border-neonblue";

  return (
    <div className="mx-auto min-h-screen max-w-md p-4 pb-10 font-sans text-slate-100">
      <h1 className="mb-3 text-center text-xl font-black tracking-widest text-neonblue drop-shadow-[0_0_8px_#00d4ff]">ZEROX TRADER AI</h1>
      <select className={input} value={asset} onChange={(e) => setAsset(e.target.value)}>
        {PAIRS.map((p) => <option key={p}>{p}</option>)}
      </select>

      <div className="mt-4 flex gap-2">
        {Object.keys(TFS).map((t) => (
          <button key={t} onClick={() => setTf(t)}
            className={`flex-1 rounded-full border py-2 font-bold ${t === tf ? "border-neonblue bg-neonblue text-ink shadow-[0_0_14px_#00d4ff]" : "border-[#1d3a57] text-slate-400"}`}>{t}</button>
        ))}
      </div>

      <div className={card}>
        <div className="text-xs tracking-widest text-slate-400">CANDLE CLOSES IN</div>
        <div className="text-center text-4xl font-extrabold text-neonblue drop-shadow-[0_0_10px_#00d4ff]">{mm}:{ss}</div>
        {warn && <div className="mt-3 animate-pulse rounded-xl border-2 border-yellow-400 bg-yellow-400/10 p-3 text-center font-extrabold text-yellow-300">⚠ 30 SECONDS TO CANDLE CLOSE — GET READY</div>}
      </div>

      <div className={card}>
        <button onClick={generate} disabled={loading}
          className="flex w-full items-center justify-center rounded-2xl bg-gradient-to-r from-neonblue to-neongreen py-4 text-lg font-extrabold text-ink shadow-[0_0_22px_#00d4ff88] disabled:opacity-70">
          {loading ? <span className="h-6 w-6 animate-spin rounded-full border-4 border-ink/30 border-t-ink" /> : "⚡ Generate AI Signal"}
        </button>
        {err && <p className="mt-3 text-sm text-neonred">{err}</p>}
        {res && (
          <>
            <div className={`mt-4 rounded-2xl border-2 p-6 text-center text-5xl font-black tracking-widest ${SIG[res.signal]}`}>
              {res.signal}
              {res.confidence != null && <div className="mt-1 text-sm font-semibold tracking-normal opacity-80">confidence {res.confidence}%</div>}
            </div>
            <p className="mt-4 text-sm leading-relaxed text-slate-300">{res.reasoning}</p>
            <div className="mt-3 grid grid-cols-2 gap-1 text-xs text-slate-400">
              <div>RSI: <b className="text-white">{res.indicators.rsi}</b></div>
              <div>Trend: <b className="text-white">{res.indicators.trend}</b></div>
              <div>Support: <b className="text-white">{res.indicators.support}</b></div>
              <div>Resist: <b className="text-white">{res.indicators.resistance}</b></div>
              <div>Breakout: <b className="text-white">{res.indicators.breakout}</b></div>
              <div>Divergence: <b className="text-white">{res.indicators.rsi_divergence}</b></div>
            </div>
          </>
        )}
      </div>

      <div className={card}>
        <div className="mb-2 text-xs tracking-widest text-slate-400">TRADE PANEL</div>
        <div className="flex gap-2">
          <input className={input} type="number" min="1" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="Amount $" />
          <input className={input} type="number" min="1" value={duration} onChange={(e) => setDuration(e.target.value)} placeholder="Minutes" />
        </div>
        <div className="mt-3 flex gap-3">
          <button onClick={() => trade("CALL")} className="flex-1 rounded-2xl bg-neongreen py-5 text-xl font-black text-ink shadow-[0_0_20px_#00ff9d88]">▲ CALL</button>
          <button onClick={() => trade("PUT")} className="flex-1 rounded-2xl bg-neonred py-5 text-xl font-black text-white shadow-[0_0_20px_#ff3b5c88]">▼ PUT</button>
        </div>
        {msg && <p className="mt-3 text-sm text-neonblue">{msg}</p>}
      </div>
    </div>
  );
}
