import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, RefreshCw, AlertTriangle } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';

import Header from './components/Header';
import Controls from './components/Controls';
import DealCard from './components/DealCard';
import SniperShell from './components/SniperShell';
import CompsModal from './components/CompsModal';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';
const POLL_MS = 15000;

function mapDeal(d) {
  return {
    id: d.deal_id,
    rawId: d.listing.listing_id,
    player: d.listing.card.player_name,
    year: d.listing.card.year,
    brand: d.listing.card.brand,
    type: d.listing.card.card_type,
    graded: d.listing.card.graded,
    grader: d.listing.card.grader || '',
    grade: d.listing.card.grade || '',
    title: d.listing.title,
    currentPrice: d.listing.current_price,
    shippingCost: d.listing.shipping_cost || 0,
    fmv: d.fair_market_value,
    discount: d.discount,
    maxBid: d.max_bid,
    confidence: d.comps?.confidence || 'none',
    nComps: d.comps?.n || 0,
    cv: d.comps?.cv ?? 0,
    endTime: d.listing.end_time ? new Date(d.listing.end_time) : null,
    imageUrl: d.listing.image_url,
    url: d.listing.url,
    explainer: d.explainer,
    status: d.status,
    comps: (d.comps?.samples || []).map((c) => ({
      price: c.sale_price,
      date: new Date(c.sale_date).toLocaleDateString(),
      source: c.source,
      url: c.url,
    })),
  };
}

function secondsLeft(endTime) {
  if (!endTime) return null;
  return Math.max(0, Math.floor((endTime.getTime() - Date.now()) / 1000));
}

export default function App() {
  const [deals, setDeals] = useState([]);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [targetMargin, setTargetMargin] = useState(0.30);
  const [maxBidLimit, setMaxBidLimit] = useState(5000);
  const [dailyBudget, setDailyBudget] = useState(5000);
  const [budgetPreset, setBudgetPreset] = useState('whale');
  const [selectedDealComps, setSelectedDealComps] = useState(null);
  const [monitoredRoster, setMonitoredRoster] = useState([]);
  const [newPlayerInput, setNewPlayerInput] = useState('');
  const [sniperLogs, setSniperLogs] = useState([]);
  const [, setTick] = useState(0);

  const addLog = useCallback((message) => {
    const time = new Date().toLocaleTimeString([], {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
    setSniperLogs((prev) => [{ time, message }, ...prev].slice(0, 50));
  }, []);

  const fetchDeals = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/deals`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setDeals(data.map(mapDeal));
      setError(null);
    } catch (err) {
      setError(`Could not reach backend at ${API_BASE}. Is the server running?`);
    }
  }, []);

  useEffect(() => {
    fetchDeals();
    const id = setInterval(fetchDeals, POLL_MS);
    return () => clearInterval(id);
  }, [fetchDeals]);

  // tick once per second so countdowns update
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  // pull roster from watchlist (best-effort; if API isn't ready, leave blank)
  useEffect(() => {
    fetch(`${API_BASE}/config`).catch(() => {});
    const players = new Set(deals.map((d) => d.player));
    setMonitoredRoster(Array.from(players));
  }, [deals]);

  useEffect(() => {
    deals.forEach((d) => {
      if (!d.endTime) return;
      const s = secondsLeft(d.endTime);
      if (s === 60 && d.status === 'approved') {
        addLog(`⏰ ${d.player} ${d.year} ${d.brand} closes in 60s — open eBay and place max bid $${d.maxBid.toFixed(2)}.`);
      }
    });
  }, [deals, addLog]);

  const applyBudgetPreset = (preset) => {
    setBudgetPreset(preset);
    if (preset === 'cooper') {
      setMaxBidLimit(300); setDailyBudget(300);
      addLog('👦 Cooper mode: $300 cap per card.');
    } else if (preset === 'whale') {
      setMaxBidLimit(5000); setDailyBudget(5000);
      addLog('🐋 Whale mode: $5,000 cap per card.');
    }
  };

  const refresh = async () => {
    setRefreshing(true);
    addLog('🔄 Manual refresh: scanning eBay…');
    try {
      const r = await fetch(`${API_BASE}/refresh`, { method: 'POST' });
      const json = await r.json();
      addLog(`✅ Scan complete: ${json.scanned} listings, ${json.approved} approved.`);
      await fetchDeals();
    } catch {
      addLog('❌ Refresh failed; check backend logs.');
    } finally {
      setRefreshing(false);
    }
  };

  const setDealStatus = async (deal, status) => {
    try {
      await fetch(`${API_BASE}/deals/${deal.id}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      addLog(`📝 ${deal.player} ${deal.year} → ${status}`);
      fetchDeals();
    } catch {
      addLog('❌ Status change failed.');
    }
  };

  const queueSnipe = async (deal) => {
    try {
      const r = await fetch(`${API_BASE}/deals/${deal.id}/snipe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_bid: deal.maxBid }),
      });
      const json = await r.json();
      addLog(`🎯 Snipe queued for ${deal.player}. ${json.instructions || ''}`);
      fetchDeals();
    } catch {
      addLog('❌ Snipe queue failed.');
    }
  };

  const addPlayerToRoster = (e) => {
    e.preventDefault();
    const v = newPlayerInput.trim();
    if (v && !monitoredRoster.includes(v)) {
      setMonitoredRoster([...monitoredRoster, v]);
      addLog(`📈 ${v} added locally. (Persist to backend by editing watchlist.yaml.)`);
      setNewPlayerInput('');
    }
  };
  const removePlayerFromRoster = (player) => {
    setMonitoredRoster(monitoredRoster.filter((p) => p !== player));
    addLog(`📉 ${player} removed locally. (Edit watchlist.yaml to persist.)`);
  };

  const dealsForCard = deals.map((d) => ({ ...d, endTimeSeconds: secondsLeft(d.endTime) ?? 0 }));
  const approvedCount = dealsForCard.filter((d) => d.status === 'approved' || d.status === 'snipe_queued').length;

  return (
    <div className="min-h-screen px-4 py-8 md:px-12 max-w-7xl mx-auto">
      <Header rosterCount={monitoredRoster.length} activeDealsCount={approvedCount} />

      {error && (
        <div className="mb-6 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Controls
          targetMargin={targetMargin}
          setTargetMargin={setTargetMargin}
          maxBidLimit={maxBidLimit}
          setMaxBidLimit={setMaxBidLimit}
          dailyBudget={dailyBudget}
          setDailyBudget={setDailyBudget}
          budgetPreset={budgetPreset}
          applyBudgetPreset={applyBudgetPreset}
          monitoredRoster={monitoredRoster}
          newPlayerInput={newPlayerInput}
          setNewPlayerInput={setNewPlayerInput}
          addPlayerToRoster={addPlayerToRoster}
          removePlayerFromRoster={removePlayerFromRoster}
        />

        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-indigo-400" />
              Live Arbitrage Opportunities
            </h2>
            <div className="flex items-center gap-3">
              <div className="text-xs text-slate-400">{dealsForCard.length} listings tracked</div>
              <button
                type="button"
                onClick={refresh}
                disabled={refreshing}
                className="text-xs px-3 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 hover:bg-indigo-500/20 flex items-center gap-1.5 disabled:opacity-50"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                Scan now
              </button>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            {dealsForCard.length === 0 && !error && (
              <div className="p-6 rounded-2xl bg-white/5 border border-white/10 text-sm text-slate-400">
                No deals yet. Hit <strong>Scan now</strong> to pull live auctions from eBay.
                If you haven't set <code>EBAY_CLIENT_ID</code> / <code>EBAY_CLIENT_SECRET</code> in <code>.env</code>, do that first.
              </div>
            )}
            <AnimatePresence>
              {dealsForCard.map((deal) => (
                <DealCard
                  key={deal.id}
                  deal={deal}
                  targetMargin={targetMargin}
                  maxBidLimit={maxBidLimit}
                  dailyBudget={dailyBudget}
                  onSelectComps={setSelectedDealComps}
                  onApprove={() => setDealStatus(deal, 'approved')}
                  onReject={() => setDealStatus(deal, 'rejected')}
                  onSnipe={() => queueSnipe(deal)}
                />
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <SniperShell sniperState="waiting" sniperLogs={sniperLogs} />

      <AnimatePresence>
        {selectedDealComps && (
          <CompsModal
            selectedDealComps={selectedDealComps}
            targetMargin={targetMargin}
            onClose={() => setSelectedDealComps(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
