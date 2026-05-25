import React from 'react';

export default function Header({ rosterCount, activeDealsCount }) {
  return (
    <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
      <div>
        <div className="flex items-center gap-3 mb-1">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
          </span>
          <span className="text-xs uppercase tracking-widest text-indigo-400 font-semibold">Active Scout Engine</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent">
          CARD SCOUT
        </h1>
      </div>

      {/* Stats Row */}
      <div className="flex gap-4">
        <div className="glass-panel rounded-3xl p-4 flex flex-col min-w-[120px]">
          <span className="text-[10px] uppercase tracking-widest text-slate-400">Total Monitored</span>
          <span className="text-xl font-bold mt-1 text-white">{rosterCount} Players</span>
        </div>
        <div className="glass-panel rounded-3xl p-4 flex flex-col min-w-[120px]">
          <span className="text-[10px] uppercase tracking-widest text-slate-400">Deals Located</span>
          <span className="text-xl font-bold mt-1 text-emerald-400">{activeDealsCount} Cards</span>
        </div>
        <div className="glass-panel rounded-3xl p-4 flex flex-col min-w-[120px]">
          <span className="text-[10px] uppercase tracking-widest text-slate-400">Secured Comp</span>
          <span className="text-xl font-bold mt-1 text-indigo-300">$2,025.00</span>
        </div>
      </div>
    </header>
  );
}
