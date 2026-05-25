import React from 'react';
import { Info } from 'lucide-react';
import { motion } from 'framer-motion';

export default function CompsModal({ selectedDealComps, targetMargin, onClose }) {
  if (!selectedDealComps) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <motion.div 
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        className="glass-panel w-full max-w-xl rounded-3xl p-6 overflow-hidden relative"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-xl font-bold mb-1 text-white">Comps Valuation Analysis</h3>
        <p className="text-xs text-indigo-400 font-semibold mb-6">
          {selectedDealComps.year} {selectedDealComps.brand} {selectedDealComps.player} {selectedDealComps.type} ({selectedDealComps.grader} {selectedDealComps.grade})
        </p>

        <div className="flex flex-col gap-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Recent Market Comparables</span>
          <div className="flex flex-col gap-2 max-h-[220px] overflow-y-auto pr-1">
            {selectedDealComps.comps.map((comp, idx) => (
              <div 
                key={idx} 
                className="bg-white/5 border border-white/5 rounded-2xl p-4 flex justify-between items-center"
              >
                <div className="flex flex-col">
                  <span className="text-xs font-bold text-white">${comp.price.toLocaleString([], { minimumFractionDigits: 2 })}</span>
                  <span className="text-[10px] text-slate-400 mt-0.5">{comp.source} • {comp.date}</span>
                </div>
                <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  COMP VERIFIED
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Educational Comps explanation for Cooper */}
        <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-2xl p-4 mt-6 flex gap-3">
          <Info className="h-5 w-5 text-indigo-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed text-slate-300">
            <span className="font-bold text-indigo-300">Cooper's Valuation Corner:</span> We calculate the true <span className="underline decoration-indigo-400/50">Fair Market Value</span> by averaging these verified comps. Averages remove short-term price spikes and drops, showing what the card is truly worth. Buying at {(targetMargin*100).toFixed(0)}% below this average ensures you build in profit from day one!
          </div>
        </div>

        <button 
          type="button"
          onClick={onClose}
          className="mt-6 w-full bg-slate-800 hover:bg-slate-750 text-white rounded-2xl py-3 text-sm font-semibold transition-all"
        >
          Close Comps
        </button>
      </motion.div>
    </div>
  );
}
