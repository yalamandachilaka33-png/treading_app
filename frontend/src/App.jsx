import { useState, useEffect } from 'react';

const API_URL = "https://treading-app-1.onrender.com"; 
const WS_URL = "wss://treading-app-1.onrender.com/ws/live"; 

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
  
  const [timeLeft, setTimeLeft] = useState(TFS[tf]);
  const [liveData, setLiveData] = useState({ price: 0, volume: 0 });
  
  // Dynamic Scanner States
  const [scannedPairs, setScannedPairs] = useState([]);
  const [scanLoading, setScanLoading] = useState(true);

  // 1. Timer Sync
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      const currentSeconds = now.getUTCSeconds() + (now.getUTCMinutes() * 60) + (now.getUTCHours() * 3600);
      const tfSeconds = TFS[tf];
      setTimeLeft(tfSeconds - (currentSeconds % tfSeconds));
    };
    tick(); 
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [tf]);

  // 2. WebSocket for Live Price
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}?asset=${asset}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLiveData({ price: data.price, volume: data.volume });
    };
    return () => ws.close(); 
  }, [asset]);

  // 3. Fetch Live Scanner Data (Top 6 Pairs)
  const fetchScanner = async () => {
    setScanLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/scanner`);
      if (response.ok) {
        const data = await response.json();
        setScannedPairs(data);
      }
    } catch (error) {
      console.log("Scanner error:", error);
    }
    setScanLoading(false);
  };

  // 4. Run Scanner on load & every 3 minutes
  useEffect(() => {
    fetchScanner();
    const interval = setInterval(fetchScanner, 180000); 
    return () => clearInterval(interval);
  }, []);

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

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const getEntryTime = () => {
    const now = new Date();
    const nextCandle = new Date(now.getTime() + (timeLeft * 1000));
    return nextCandle.toLocaleTimeString('en-IN', { 
      timeZone: 'Asia/Kolkata', hour12: false, 
      hour: '2-digit', minute: '2-digit', second: '2-digit' 
    }) + ' IST';
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
        
        {/* Live Price */}
        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 shadow-lg flex justify-between items-center">
          <div>
            <div className="text-xs text-gray-400 mb-1">LIVE PRICE ({asset})</div>
            <div className="text-3xl font-black text-white font-mono">{liveData.price || "..."}</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-400 mb-1">TICK VOLUME</div>
            <div className="text-xl font-bold text-neonblue">{liveData.volume || "0"}</div>
          </div>
        </div>

        {/* Asset & Timeframe */}
        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 shadow-lg space-y-4">
          <select value={asset} onChange={(e) => setAsset(e.target.value)} className="bg-gray-900 text-neonblue font-bold text-lg p-2 rounded border border-gray-600 outline-none w-full">
            {PAIRS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <div className="flex gap-2">
            {Object.keys(TFS).map(t => (
              <button key={t} onClick={() => setTf(t)} className={`flex-1 py-2 rounded-full font-bold transition-all ${tf === t ? 'bg-neonblue text-black shadow-[0_0_10px_#00f3ff]' : 'bg-gray-700 text-gray-300'}`}>
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Signal Generator */}
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg text-center relative overflow-hidden">
          <button 
            onClick={generateSignal} 
            disabled={loading} 
            className={`w-full text-white font-bold py-3 px-4 rounded-full mb-4 transition-all duration-300 ${
              timeLeft <= 30 
                ? 'bg-gradient-to-r from-neonred to-red-600 shadow-[0_0_20px_#ff3131] animate-pulse' 
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
            } ${loading ? 'opacity-50' : ''}`}
          >
            {loading ? "Analyzing Market..." : (timeLeft <= 30 ? "🚨 GET SIGNAL NOW (30s Left)" : "Wait for 30s mark to Analyze")}
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
              <p className="text-sm mb-4">{res.reason}</p>
              
              <div className="bg-black/40 p-3 rounded-lg mb-3 flex justify-between items-center border border-current/30">
                <div>
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider">Entry Time</div>
                  <div className="text-lg font-mono text-white font-bold">{getEntryTime()}</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider">Duration</div>
                  <div className="text-lg font-mono text-white font-bold uppercase">{tf}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-left bg-black/30 p-2 rounded mb-2">
                <div>RSI: {res.indicators?.RSI}</div>
                <div>MACD: {res.indicators?.MACD_Trend}</div>
                <div>Struct: {res.indicators?.Structure_Tags}</div>
                <div>Pattern: {res.indicators?.Candle_Wicks}</div>
              </div>
              <div className="text-[10px] text-neonblue bg-black/20 p-2 rounded">
                Fib: {res.indicators?.Fib_Level}
              </div>
            </div>
          )}
        </div>

        {/* Live Dynamic Scanner (List Format) */}
        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider">🔥 Top Live Signals (Auto Scan)</h2>
            <button onClick={fetchScanner} className="text-xs text-neonblue border border-neonblue px-2 py-0.5 rounded-full hover:bg-neonblue hover:text-black transition">
              Refresh
            </button>
          </div>
          
          {scanLoading ? (
            <p className="text-center text-sm text-gray-400 py-4 animate-pulse">Scanning 15 pairs for best signals...</p>
          ) : scannedPairs.length === 0 ? (
            <p className="text-center text-sm text-gray-400 py-4">No strong signals right now. Market is Choppy.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {scannedPairs.map((item, index) => (
                <div 
                  key={index} 
                  onClick={() => setAsset(item.pair)}
                  className={`flex justify-between items-center p-3 rounded-lg border cursor-pointer transition-all ${
                    asset === item.pair 
                      ? 'bg-neonblue/10 border-neonblue shadow-[0_0_10px_rgba(0,243,255,0.3)]' 
                      : 'bg-gray-900 border-gray-600 hover:border-gray-400'
                  }`}
                >
                  <div className="text-sm font-bold text-white">{item.pair.replace('_otc', '_OTC')}</div>
                  <div className={`text-sm font-mono font-bold ${item.signal === 'CALL' ? 'text-neongreen' : 'text-neonred'}`}>
                    {item.signal} ({item.confidence}%)
                  </div>
                </div>
              ))}
            </div>
          )}
          <p className="text-[10px] text-gray-500 text-center mt-3">Click on a pair to select and analyze.</p>
        </div>

      </main>
    </div>
  );
}

export default App;
