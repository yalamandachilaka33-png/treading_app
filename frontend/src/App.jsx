import { useState, useEffect } from 'react';

const API_URL = "https://treading-app-1.onrender.com"; 

const TFS = { "1m": 60, "2m": 120, "3m": 180, "5m": 300 };
const PAIRS = [
  "EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc", "USDCAD_otc",
  "USDCHF_otc", "NZDUSD_otc", "EURGBP_otc", "EURJPY_otc", "GBPJPY_otc",
  "AUDJPY_otc", "AUDCAD_otc", "CADJPY_otc", "CHFJPY_otc", "EURCHF_otc"
];

function App() {
  const [asset, setAsset] = useState(PAIRS[0]);
  const [tf, setTf] = useState("1m");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  
  const [amount, setAmount] = useState(1);
  const [duration, setDuration] = useState(60);
  const [msg, setMsg] = useState("");
  
  const [timeLeft, setTimeLeft] = useState(TFS[tf]);

  // Live Market Time Sync (UTC)
  useEffect(() => {
    setDuration(TFS[tf]); // Update trade duration based on selected timeframe

    const tick = () => {
      const now = new Date();
      // Use UTC time to sync with the broker's server
      const currentSeconds = now.getUTCSeconds() + (now.getUTCMinutes() * 60) + (now.getUTCHours() * 3600);
      const tfSeconds = TFS[tf];
      
      // Calculate exact seconds remaining for the current candle to close
      const secondsToNext = tfSeconds - (currentSeconds % tfSeconds);
      setTimeLeft(secondsToNext);
    };

    tick(); // Run immediately on load
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [tf]);

  const generateSignal = async () => {
    setLoading(true);
    setErr("");
    setRes(null);
    try {
      const response = await fetch(`${API_URL}/api/signal?asset=${asset}&tf=${tf}`);
      if (!response.ok) throw new Error("Failed to fetch signal");
      const data = await response.json();
      setRes(data);
    } catch (error) {
      setErr(error.message);
    }
    setLoading(false);
  };

  const placeTrade = async (direction) => {
    try {
      setMsg(`Placing ${direction.toUpperCase()} trade...`);
      const response = await fetch(`${API_URL}/api/trade?asset=${asset}&direction=${direction}&amount=${amount}&duration=${duration}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error("Trade failed");
      setMsg(`✅ ${direction.toUpperCase()} trade placed!`);
      setTimeout(() => setMsg(""), 3000);
    } catch (error) {
      setMsg(`❌ Error: ${error.message}`);
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  // Calculate exact entry time based on UTC and time left
  const getEntryTime = () => {
    const now = new Date();
    const nextCandle = new Date(now.getTime() + (timeLeft * 1000));
    
    // Format as HH:MM:SS UTC
    const hours = String(nextCandle.getUTCHours()).padStart(2, '0');
    const minutes = String(nextCandle.getUTCMinutes()).padStart(2, '0');
    const seconds = String(nextCandle.getUTCSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds} UTC`;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans pb-10">
      
      {/* Header */}
      <header className="bg-gray-800 p-4 shadow-lg border-b border-gray-700 flex justify-between items-center sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <span className="text-neonblue text-2xl">⚡</span>
          <h1 className="text-xl font-bold tracking-wider">ZEROX<span className="text-neongreen">AI</span></h1>
        </div>
        <div className="flex flex-col items-end">
          <div className="bg-gray-700 px-3 py-1 rounded-full text-xs font-mono border border-gray-600">
            Next Candle: <span className={timeLeft <= 30 ? "text-neonred font-bold" : "text-neongreen"}>{formatTime(timeLeft)}</span>
          </div>
          {timeLeft <= 30 && <span className="text-[10px] text-neonred font-bold mt-1 animate-pulse">ENTRY WINDOW OPEN!</span>}
        </div>
      </header>

      <main className="p-4 max-w-md mx-auto space-y-6 mt-4">
        
        {/* Asset Selection */}
        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 shadow-lg">
          <label className="text-xs text-gray-400 mb-1 block">TRADING ASSET</label>
          <div className="flex justify-between items-center">
            <select value={asset} onChange={(e) => setAsset(e.target.value)} className="bg-gray-900 text-neonblue font-bold text-lg p-2 rounded border border-gray-600 outline-none w-full">
              {PAIRS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <span className="ml-2 bg-green-900/50 text-neongreen text-xs px-2 py-1 rounded border border-neongreen/30">+92%</span>
          </div>
        </div>

        {/* Timeframes */}
        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 shadow-lg">
          <label className="text-xs text-gray-400 mb-2 block">EXECUTION TIMEFRAME</label>
          <div className="flex gap-2">
            {Object.keys(TFS).map(t => (
              <button key={t} onClick={() => setTf(t)} className={`flex-1 py-2 rounded-full font-bold transition-all ${tf === t ? 'bg-neonblue text-black shadow-[0_0_10px_#00f3ff]' : 'bg-gray-700 text-gray-300'}`}>
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Signal Generator Card */}
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg text-center relative overflow-hidden">
          {timeLeft <= 30 && <div className="absolute inset-0 border-4 border-neonred animate-pulse rounded-xl pointer-events-none"></div>}
          
          <h2 className="text-lg font-bold mb-4">AI Technical Analysis</h2>
          
          <button onClick={generateSignal} disabled={loading} className="w-full bg-gradient-to-r from-neonblue to-blue-600 text-white font-bold py-3 px-4 rounded-full shadow-[0_0_15px_#00f3ff] disabled:opacity-50 flex justify-center items-center gap-2 mb-4">
            {loading ? "Analyzing Market..." : "✨ Generate AI Signal"}
          </button>

          {err && <p className="text-neonred text-sm">{err}</p>}

          {res && (
            <div className={`p-4 rounded-lg mt-4 border ${
              res.signal === 'CALL' ? 'bg-green-900/30 border-neongreen text-neongreen shadow-[0_0_15px_#39ff14]' :
              res.signal === 'PUT' ? 'bg-red-900/30 border-neonred text-neonred shadow-[0_0_15px_#ff3131]' :
              'bg-gray-700 border-gray-500 text-gray-300'
            }`}>
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-2xl font-black">{res.signal}</h3>
                {res.confidence !== undefined && (
                  <span className="text-sm font-bold bg-black/50 text-white px-3 py-1 rounded-full border border-current">
                    {res.confidence}% Match
                  </span>
                )}
              </div>
              <p className="text-sm mb-3">{res.reason}</p>
              
              <div className="bg-black/30 p-2 rounded mb-3 flex justify-between items-center">
                <div className="text-xs text-gray-400">Exact Entry Time:</div>
                <div className="text-lg font-mono text-white">{getEntryTime()}</div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-left bg-black/30 p-2 rounded">
                <div>RSI: {res.indicators?.RSI}</div>
                <div>MACD: {res.indicators?.MACD_Trend}</div>
                <div>Trend: {res.indicators?.BB_Status}</div>
                <div>Pattern: {res.indicators?.Candle_Pattern}</div>
              </div>
            </div>
          )}
        </div>

        {/* Manual Trading Panel */}
        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 shadow-lg space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="text-xs text-gray-400">Amount ($)</label>
              <input type="number" value={amount} onChange={e => setAmount(e.target.value)} className="w-full bg-gray-900 p-2 rounded border border-gray-600 text-center font-bold" />
            </div>
            <div className="flex-1">
              <label className="text-xs text-gray-400">Duration (Sec)</label>
              <input type="number" value={duration} readOnly className="w-full bg-gray-900 p-2 rounded border border-gray-600 text-center font-bold text-gray-500 cursor-not-allowed" />
            </div>
          </div>
          
          {msg && <p className="text-center text-sm font-bold text-neonblue animate-pulse">{msg}</p>}

          <div className="flex gap-2">
            <button onClick={() => placeTrade('call')} className="flex-1 bg-green-600 hover:bg-green-500 text-white font-bold text-xl py-4 rounded-lg shadow-[0_0_10px_#39ff14] transition">
              CALL ⬆
            </button>
            <button onClick={() => placeTrade('put')} className="flex-1 bg-red-600 hover:bg-red-500 text-white font-bold text-xl py-4 rounded-lg shadow-[0_0_10px_#ff3131] transition">
              PUT ⬇
            </button>
          </div>
        </div>

      </main>
    </div>
  );
}

export default App;
