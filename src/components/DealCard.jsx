import React from 'react';
import { Clock, Info, ArrowUpRight } from 'lucide-react';
import { motion } from 'framer-motion';

export default function DealCard({ deal, targetMargin, onSelectComps }) {
  const maxBidCeiling = deal.fmv * (1 - targetMargin) - deal.shippingCost;
  const isDealApproved = deal.currentPrice <= maxBidCeiling;
  const discountPercentage = ((deal.fmv - deal.currentPrice) / deal.fmv) * 100;
  const projectedMargin = deal.fmv - deal.currentPrice - deal.shippingCost;

  const formatTime = (seconds) => {
    if (seconds <= 0) return "Auction Ended";
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins < 60) return `${mins}m ${secs}s`;
    const hrs = Math.floor(mins / 60);
    const remMins = mins % 60;
    return `${hrs}h ${remMins}m`;
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3 }}
      className={`glass-panel-interactive rounded-3xl p-6 flex flex-col md:flex-row gap-6 relative overflow-hidden ${
        isDealApproved ? 'border-emerald-500/20' : 'border-white/5'
      }`}
    >
      {/* Deal Ribbon / Status indicator */}
      <div className="absolute top-4 right-4 flex gap-2">
        <span className={`text-[10px] uppercase font-bold tracking-widest px-2.5 py-1 rounded-full ${
          isDealApproved 
            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
            : 'bg-slate-800/50 text-slate-400 border border-white/5'
        }`}>
          {isDealApproved ? "APPROVED SNIPE" : "WATCH LIST"}
        </span>
        {deal.status === "secured" && (
          <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            SECURED
          </span>
        )}
      </div>

      {/* Card Preview Image Box */}
      <div className="relative w-full md:w-36 h-48 bg-slate-900/60 rounded-2xl overflow-hidden flex-shrink-0 border border-white/5 flex items-center justify-center">
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent z-10" />
        <div className="absolute top-3 left-3 bg-indigo-600 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded z-20 shadow-md">
          {deal.grader} {deal.grade}
        </div>
        <img 
          src={deal.imageUrl} 
          alt={deal.player}
          className="w-full h-full object-cover opacity-60" 
        />
        <div className="absolute bottom-3 left-3 right-3 z-20">
          <p className="text-[10px] text-indigo-300 uppercase tracking-widest font-semibold">{deal.brand}</p>
          <p className="text-xs font-bold text-white leading-tight mt-0.5">{deal.player}</p>
        </div>
      </div>

      {/* Deal Metadata Details */}
      <div className="flex-1 flex flex-col justify-between">
        <div>
          <span className="text-xs text-indigo-400 font-semibold">
            {deal.year} {deal.type}
          </span>
          <h3 className="text-base font-bold text-white mt-1 pr-24 leading-snug line-clamp-2">
            {deal.title}
          </h3>
          
          {/* Financial Analysis Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="flex flex-col">
              <span className="text-[10px] uppercase tracking-wider text-slate-400">Current Price</span>
              <span className="text-lg font-bold text-white mt-0.5">
                ${deal.currentPrice.toLocaleString([], { minimumFractionDigits: 2 })}
              </span>
            </div>
            
            <div className="flex flex-col">
              <span className="text-[10px] uppercase tracking-wider text-slate-400">Calculated FMV</span>
              <span className="text-lg font-bold text-indigo-300 mt-0.5">
                ${deal.fmv.toLocaleString([], { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div className="flex flex-col">
              <span className="text-[10px] uppercase tracking-wider text-slate-400">Max Bid Limit</span>
              <span className="text-lg font-bold text-slate-200 mt-0.5">
                ${maxBidCeiling.toLocaleString([], { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div className="flex flex-col">
              <span className="text-[10px] uppercase tracking-wider text-slate-400">Est. Profit</span>
              <span className={`text-lg font-bold mt-0.5 ${isDealApproved ? 'text-emerald-400' : 'text-slate-400'}`}>
                ${projectedMargin.toLocaleString([], { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </div>

        {/* Interactive Buttons footer */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 mt-6 pt-4 border-t border-white/5">
          <div className="flex items-center gap-3">
            <Clock className="h-4 w-4 text-slate-400" />
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              Auction Ends in: 
              <span className={`font-semibold ${deal.endTimeSeconds < 60 ? 'text-rose-400 animate-pulse font-extrabold' : 'text-slate-300'}`}>
                {formatTime(deal.endTimeSeconds)}
              </span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button 
              type="button"
              onClick={() => onSelectComps(deal)}
              className="bg-white/5 text-slate-300 border border-white/10 hover:bg-white/10 hover:text-white rounded-2xl px-4 py-2 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <Info className="h-3.5 w-3.5" />
              View Comps
            </button>
            
            <a 
              href={deal.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 hover:bg-indigo-500/20 hover:text-indigo-200 rounded-2xl px-4 py-2 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              eBay Link
              <ArrowUpRight className="h-3.5 w-3.5" />
            </a>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
