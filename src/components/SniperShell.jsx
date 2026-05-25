import React from 'react';
import { Cpu } from 'lucide-react';

export default function SniperShell({ sniperState, sniperLogs }) {
  return (
    <div className="lg:col-span-3 glass-panel rounded-3xl p-6 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl" />
      
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 rounded-2xl">
            <Cpu className="h-5 w-5 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Live Sniper Queue (Simulation Sandbox)</h3>
            <p className="text-xs text-slate-400">Observing high priority target ending within 30s</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <span className={`text-xs px-3 py-1 rounded-full font-semibold uppercase tracking-wider ${
            sniperState === "secured" ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20" :
            sniperState === "sniping" ? "bg-rose-500/15 text-rose-400 border border-rose-500/20 animate-pulse" :
            sniperState === "priming" ? "bg-amber-500/15 text-amber-400 border border-amber-500/20" :
            "bg-white/5 text-slate-400"
          }`}>
            {sniperState === "waiting" && "Monitoring (15s sniping range)"}
            {sniperState === "priming" && "Priming (Target Lock)"}
            {sniperState === "sniping" && "SNIPING NOW!"}
            {sniperState === "secured" && "CARDS SECURED!"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* The sniper target summary */}
        <div className="bg-white/[0.01] border border-white/5 rounded-2xl p-4 flex gap-4 items-center">
          <div className="w-12 h-16 bg-slate-900 rounded overflow-hidden flex-shrink-0 border border-white/5">
            <img 
              src="https://images.unsplash.com/photo-1546519638-68e109498ffc?w=100" 
              alt="Jordan preview"
              className="w-full h-full object-cover"
            />
          </div>
          <div className="flex-1 min-w-0">
            <span className="text-[10px] text-amber-400 font-bold uppercase">1986 Fleer #57 PSA 8</span>
            <h4 className="text-sm font-bold text-white truncate mt-0.5">Michael Jordan Rookie</h4>
            <div className="flex justify-between items-center mt-2 text-xs">
              <span className="text-slate-400">Max Sniper Bid:</span>
              <span className="font-semibold text-slate-200">$4,935.00</span>
            </div>
          </div>
        </div>

        {/* Simulated terminal logs showing agent steps */}
        <div className="lg:col-span-2 bg-black/40 border border-white/5 rounded-2xl p-4 font-mono text-xs max-h-[160px] overflow-y-auto flex flex-col gap-2">
          <div className="text-indigo-400 border-b border-white/5 pb-2 font-semibold">
            [Card Scout Sniper Shell v1.0.0]
          </div>
          {sniperLogs.length === 0 ? (
            <div className="text-slate-500 italic">Initializing sniper logs... Clock ticking.</div>
          ) : (
            sniperLogs.map((log, index) => (
              <div key={index} className="flex gap-3 leading-relaxed">
                <span className="text-slate-500 select-none">[{log.time}]</span>
                <span className={
                  log.message.includes("WINNER") ? "text-emerald-400 font-bold" :
                  log.message.includes("Firing") || log.message.includes("Submitting") ? "text-indigo-300 font-semibold" :
                  log.message.includes("engaged") ? "text-amber-300" : "text-slate-300"
                }>
                  {log.message}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
