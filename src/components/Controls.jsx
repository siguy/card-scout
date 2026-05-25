import React from 'react';
import { Sliders, Cpu, Search, UserPlus, UserMinus } from 'lucide-react';

export default function Controls({ 
  targetMargin, 
  setTargetMargin, 
  monitoredRoster, 
  newPlayerInput, 
  setNewPlayerInput, 
  addPlayerToRoster, 
  removePlayerFromRoster 
}) {
  return (
    <div className="flex flex-col gap-8">
      {/* CONTROL BOX: Margins & Filters */}
      <div className="glass-panel rounded-3xl p-6 relative overflow-hidden">
        {/* Background luxury gradient glow */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl" />
        
        <h2 className="text-lg font-bold mb-6 flex items-center gap-2 text-white">
          <Sliders className="h-5 w-5 text-indigo-400" />
          Deal Margin Controls
        </h2>
        
        {/* Margin Slider */}
        <div className="mb-6">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-slate-400">Target Profit Margin</span>
            <span className="text-indigo-300 font-semibold">{(targetMargin * 100).toFixed(0)}%</span>
          </div>
          <input 
            type="range" 
            min="0.10" 
            max="0.40" 
            step="0.05" 
            value={targetMargin} 
            onChange={(e) => setTargetMargin(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
          <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
            Higher margins filter for absolute bargains (lower risk), while lower margins approve more opportunities.
          </p>
        </div>
        
        <div className="border-t border-white/5 pt-6">
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Default Graders Monitored</span>
            <span className="px-2 py-0.5 rounded-md bg-white/5 text-slate-300">PSA, BGS, SGC</span>
          </div>
        </div>
      </div>

      {/* ROSTER PANEL */}
      <div className="glass-panel rounded-3xl p-6 relative overflow-hidden">
        <h2 className="text-lg font-bold mb-6 flex items-center gap-2 text-white">
          <Cpu className="h-5 w-5 text-indigo-400" />
          Scout Target Roster
        </h2>
        
        {/* Add Target Input */}
        <form onSubmit={addPlayerToRoster} className="flex gap-2 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input 
              type="text" 
              placeholder="Add player (e.g. Kobe Bryant)..." 
              value={newPlayerInput}
              onChange={(e) => setNewPlayerInput(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-2xl py-2 pl-9 pr-4 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
            />
          </div>
          <button 
            type="submit" 
            className="bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-2xl px-4 py-2 hover:bg-indigo-500/40 hover:text-indigo-200 text-sm font-semibold transition-all"
          >
            <UserPlus className="h-4 w-4" />
          </button>
        </form>

        {/* List of active players */}
        <div className="flex flex-wrap gap-2 max-h-[220px] overflow-y-auto pr-1">
          {monitoredRoster.map(player => (
            <div 
              key={player} 
              className="flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl px-3 py-1.5 text-xs text-slate-300 transition-all group"
            >
              <span>{player}</span>
              <button 
                type="button"
                onClick={() => removePlayerFromRoster(player)}
                className="text-slate-500 hover:text-rose-400 transition-all opacity-0 group-hover:opacity-100 ml-1"
              >
                <UserMinus className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
