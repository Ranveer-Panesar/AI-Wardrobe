import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getItems, resolveImageUrl } from '../api/wardrobe';
import { getOutfitRecommendations, startOutfitRender, pollRenderJob } from '../api/render';

/* ──────────────────────────────────────────────
   Constants
   ────────────────────────────────────────────── */
const OCCASIONS = [
  { id: 'casual',   label: 'Casual',   icon: '☀️' },
  { id: 'business', label: 'Business', icon: '💼' },
  { id: 'formal',   label: 'Formal',   icon: '🎩' },
  { id: 'evening',  label: 'Evening',  icon: '🍷' },
  { id: 'wedding',  label: 'Wedding',  icon: '💍' },
  { id: 'sport',    label: 'Sport',    icon: '🏃' },
];

const STYLES = ['Classic', 'Minimalist', 'Streetwear', 'Vintage', 'Bohemian', 'Athleisure'];
const SEASONS = ['Spring 🌸', 'Summer ☀️', 'Autumn 🍂', 'Winter ❄️'];
const FITS   = ['Slim Fit', 'Regular', 'Oversized', 'Relaxed'];

/* ──────────────────────────────────────────────
   Score bar
   ────────────────────────────────────────────── */
function ScoreBar({ score }) {
  const normalized = score <= 1.0 ? score * 10 : score;
  const pct = Math.min(100, Math.max(0, normalized * 10));
  const color = normalized >= 7.5 ? '#22c55e' : normalized >= 5.0 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-bold tabular-nums" style={{ color }}>{normalized.toFixed(1)}/10</span>
    </div>
  );
}

/* ──────────────────────────────────────────────
   Outfit Try-On Modal
   ────────────────────────────────────────────── */
function OutfitVtonModal({ outfit, wardrobeItems, onClose }) {
  const [state, setState] = useState('idle'); // idle | rendering | done | error
  const [renderUrl, setRenderUrl] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [progress, setProgress] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const getProgressMsg = (elapsedSeconds) => {
    if (elapsedSeconds < 5)   return 'Queued — starting GPU…';
    if (elapsedSeconds < 180) return 'Running CatVTON inference on RTX 5060 Ti…';
    return 'Finalizing render result…';
  };

  const startRender = async () => {
    setState('rendering');
    setElapsed(0);
    setProgress('Queued — starting GPU…');
    try {
      const { job_id } = await startOutfitRender(outfit.id);
      const url = await pollRenderJob(job_id, (job) => {
        setElapsed(job.elapsedSeconds || 0);
        setProgress(getProgressMsg(job.elapsedSeconds || 0));
      });
      setRenderUrl(url);
      setState('done');
    } catch (err) {
      setErrorMsg(err.message || 'Render failed');
      setState('error');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-sm overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <div>
            <p className="text-xs uppercase tracking-widest text-gray-400 font-semibold">Outfit Try-On</p>
            <h3 className="font-bold text-gray-900 mt-0.5">{outfit.name || 'AI Selected Look'}</h3>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-400 hover:text-gray-700 transition-colors cursor-pointer">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-5">
          {state === 'idle' && (
            <div className="text-center space-y-4">
              <div className="flex justify-center gap-2">
                {(outfit.garment_ids || []).slice(0, 3).map((id, i) => {
                  const item = wardrobeItems.find(w => w.id === id);
                  return (
                    <div key={i} className="w-16 h-16 rounded-xl bg-gray-100 border border-gray-200 overflow-hidden flex items-center justify-center">
                      {item?.image_url ? (
                        <img src={resolveImageUrl(item.image_url)} alt={item.label || item.category} className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-2xl">👕</span>
                      )}
                    </div>
                  );
                })}
              </div>
              <p className="text-sm text-gray-500">
                Virtually drape this outfit onto the base model using <strong>CatVTON</strong> on your local <strong>RTX 5060 Ti</strong>.
              </p>
              <button
                onClick={startRender}
                className="w-full bg-[#7b2d3b] hover:bg-[#5e1f2b] text-white font-semibold py-3 rounded-xl shadow-lg shadow-[#7b2d3b]/20 transition-all hover:-translate-y-0.5 cursor-pointer text-sm"
              >
                ✨ Render on Model
              </button>
            </div>
          )}

          {state === 'rendering' && (
            <div className="text-center py-6 space-y-4">
              <div className="relative w-16 h-16 mx-auto">
                <div className="w-16 h-16 rounded-full border-4 border-gray-100 border-t-[#7b2d3b] animate-spin" />
                <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-gray-400">
                  {elapsed}s
                </span>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-800">Rendering on GPU…</p>
                <p className="text-xs text-gray-400 mt-1">{progress}</p>
              </div>
            </div>
          )}

          {state === 'done' && (
            <div className="text-center space-y-4">
              <div className="rounded-2xl overflow-hidden border border-gray-100 shadow-inner bg-gray-50 aspect-[3/4] max-h-80 mx-auto">
                <img src={renderUrl} alt="Try-on result" className="w-full h-full object-cover" />
              </div>
              <a
                href={renderUrl}
                download="ai-wardrobe-outfit.jpg"
                target="_blank"
                rel="noreferrer"
                className="block w-full text-center py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                ⬇ Download High-Res
              </a>
            </div>
          )}

          {state === 'error' && (
            <div className="text-center space-y-3 py-4">
              <span className="text-3xl">⚠️</span>
              <p className="text-sm font-semibold text-gray-800">Render Failed</p>
              <p className="text-xs text-red-500 max-w-xs mx-auto">{errorMsg}</p>
              <button
                onClick={startRender}
                className="text-xs text-[#7b2d3b] underline cursor-pointer"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────
   Outfit Card
   ────────────────────────────────────────────── */
function OutfitCard({ outfit, wardrobeItems, rank, onTryOn }) {
  const [expanded, setExpanded] = useState(false);

  // Map item IDs → wardrobe items for images
  const resolveItem = (id) => wardrobeItems.find(w => w.id === id);

  const pieces = outfit.garment_ids || outfit.items || [];
  const rawScore = outfit.score || 0;
  const displayScore = rawScore <= 1.0 ? rawScore * 10 : rawScore;

  // Format style tags safely whether it's an object or array
  const displayTags = Array.isArray(outfit.style_tags)
    ? outfit.style_tags
    : outfit.style_tags && typeof outfit.style_tags === 'object'
      ? Object.entries(outfit.style_tags)
          .filter(([_, val]) => typeof val === 'number' ? val >= 0.25 : true)
          .sort((a, b) => b[1] - a[1])
          .map(([key, val]) => `${key.charAt(0).toUpperCase() + key.slice(1)} ${typeof val === 'number' ? Math.round(val * 100) + '%' : ''}`)
      : [];

  const reasoning = outfit.reasoning || (
    displayScore >= 7.5
      ? 'Exceptional color harmony, complementary silhouettes, and clean coordination across items.'
      : displayScore >= 5.0
        ? 'Well-rounded outfit with cohesive tones and versatile day-to-night styling.'
        : 'Casual pairing with easy everyday wearability.'
  );

  return (
    <div className="bg-white rounded-3xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col justify-between">
      {/* Top accent strip */}
      <div
        className="h-1"
        style={{
          background: `linear-gradient(90deg, #7b2d3b, ${displayScore >= 7.5 ? '#22c55e' : displayScore >= 5.0 ? '#f59e0b' : '#ef4444'})`
        }}
      />

      <div className="p-5 flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#7b2d3b]/10 flex items-center justify-center shrink-0">
              <span className="text-xs font-bold text-[#7b2d3b]">#{rank}</span>
            </div>
            <div>
              <h3 className="font-bold text-gray-900 text-sm">{outfit.name || `Look #${rank}`}</h3>
              <p className="text-xs text-gray-400 mt-0.5">{outfit.occasion || 'Coordinated Look'}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-gray-400 uppercase tracking-wider">Score</p>
            <p className="text-lg font-bold text-gray-900 tabular-nums">{displayScore.toFixed(1)}</p>
          </div>
        </div>

        {/* Score bar */}
        <ScoreBar score={displayScore} />

        {/* Garment previews */}
        <div className="flex gap-2 mt-4 mb-3">
          {pieces.slice(0, 4).map((id, i) => {
            const item = resolveItem(id);
            return (
              <div
                key={i}
                className="w-14 h-14 rounded-xl bg-gray-50 border border-gray-100 overflow-hidden flex items-center justify-center shrink-0"
                title={item?.label || item?.category || 'Garment'}
              >
                {item?.image_url ? (
                  <img src={resolveImageUrl(item.image_url)} alt={item.label || item.category} className="w-full h-full object-cover" />
                ) : (
                  <span className="text-xl">{item ? '👕' : '?'}</span>
                )}
              </div>
            );
          })}
          {pieces.length > 4 && (
            <div className="w-14 h-14 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-center text-xs text-gray-400 font-medium">
              +{pieces.length - 4}
            </div>
          )}
        </div>

        {/* Reasoning (collapsible) */}
        <div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-[11px] text-[#7b2d3b] font-semibold flex items-center gap-1 cursor-pointer hover:underline"
          >
            {expanded ? '▴' : '▾'} Why this works
          </button>
          {expanded && (
            <p className="text-xs text-gray-500 mt-1.5 leading-relaxed border-l-2 border-[#7b2d3b]/20 pl-2">
              {reasoning}
            </p>
          )}
        </div>

        {/* Tags */}
        {displayTags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {displayTags.map((tag, i) => (
              <span key={i} className="px-2 py-0.5 bg-gray-50 border border-gray-100 rounded-full text-[10px] text-gray-500 capitalize">
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Actions: Try-On */}
        <div className="mt-auto pt-4 border-t border-gray-100 flex items-center justify-between">
          <span className="text-[11px] text-gray-400 font-medium">{pieces.length} items</span>
          <button
            onClick={() => onTryOn?.(outfit)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#7b2d3b] text-white hover:bg-[#5e1f2b] transition-all text-xs font-semibold cursor-pointer shadow-sm hover:-translate-y-0.5"
          >
            <span>✨</span>
            <span>Try On Look</span>
          </button>
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────
   Main Component
   ────────────────────────────────────────────── */
const FindOutfit = () => {
  const navigate = useNavigate();

  // Preferences state
  const [occasion, setOccasion]   = useState('casual');
  const [style, setStyle]         = useState('Classic');
  const [season, setSeason]       = useState('Summer');
  const [fit, setFit]             = useState('Regular');

  // Closet + results state
  const [wardrobeItems, setWardrobeItems]     = useState([]);
  const [wardrobeLoading, setWardrobeLoading] = useState(true);
  const [outfits, setOutfits]                 = useState([]);
  const [generating, setGenerating]           = useState(false);
  const [genError, setGenError]               = useState('');
  const [generated, setGenerated]             = useState(false);
  const [vtonOutfit, setVtonOutfit]           = useState(null);

  useEffect(() => {
    getItems()
      .then(d => setWardrobeItems(d.items || []))
      .catch(() => {})
      .finally(() => setWardrobeLoading(false));
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setGenError('');
    setGenerated(false);
    setOutfits([]);

    try {
      const data = await getOutfitRecommendations({ count: 6 });
      setOutfits(data.outfits || data.combinations || []);
      setGenerated(true);
    } catch (e) {
      setGenError(e.message || 'Recommendation failed — is the backend running?');
    } finally {
      setGenerating(false);
    }
  };

  const seasonLabel = season.split(' ')[0];


  return (
    <div className="min-h-screen bg-[#FDFBF7] font-sans text-[#111317] pt-16">
      <div className="max-w-5xl mx-auto px-4 py-8 md:py-12">

        {/* Page header */}
        <div className="mb-8">
          <p className="text-xs font-bold uppercase tracking-widest text-[#7b2d3b] mb-2">AI Stylist</p>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Find Your Perfect Outfit</h1>
          <p className="text-sm text-gray-500 mt-2">
            {wardrobeLoading
              ? 'Loading your wardrobe…'
              : `Scanning ${wardrobeItems.length} item${wardrobeItems.length !== 1 ? 's' : ''} in your digital closet.`
            }
          </p>
        </div>

        {/* Empty wardrobe prompt */}
        {!wardrobeLoading && wardrobeItems.length === 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 mb-8 flex items-start gap-3">
            <span className="text-2xl">👗</span>
            <div>
              <p className="font-semibold text-amber-800 text-sm">Your closet is empty</p>
              <p className="text-xs text-amber-600 mt-0.5">
                <button onClick={() => navigate('/closet')} className="underline cursor-pointer">Upload garments to your closet</button>{' '}
                first so the AI has something to work with.
              </p>
            </div>
          </div>
        )}

        {/* ── PREFERENCES FORM ── */}
        <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-6 md:p-8 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

            {/* OCCASION */}
            <div>
              <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4">
                <span className="inline-flex w-5 h-5 rounded-full bg-[#7b2d3b] text-white items-center justify-center text-[10px] mr-2">1</span>
                Occasion
              </h2>
              <div className="grid grid-cols-3 gap-2">
                {OCCASIONS.map(occ => (
                  <button
                    key={occ.id}
                    onClick={() => setOccasion(occ.id)}
                    className={`p-3 rounded-2xl border flex flex-col items-center gap-1 transition-all cursor-pointer ${
                      occasion === occ.id
                        ? 'border-[#7b2d3b] bg-[#7b2d3b]/5 shadow-sm scale-[1.03]'
                        : 'border-gray-100 hover:border-gray-300 bg-white text-gray-500'
                    }`}
                  >
                    <span className="text-xl">{occ.icon}</span>
                    <span className="text-[10px] font-bold">{occ.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* STYLE + SEASON + FIT */}
            <div className="flex flex-col gap-5 md:border-l md:border-gray-100 md:pl-8">

              {/* Style */}
              <div>
                <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">
                  <span className="inline-flex w-5 h-5 rounded-full bg-[#7b2d3b] text-white items-center justify-center text-[10px] mr-2">2</span>
                  Core Style
                </h2>
                <div className="flex flex-wrap gap-1.5">
                  {STYLES.map(s => (
                    <button
                      key={s}
                      onClick={() => setStyle(s)}
                      className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all cursor-pointer ${
                        style === s
                          ? 'bg-[#7b2d3b] text-white border-[#7b2d3b]'
                          : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* Season */}
              <div>
                <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">
                  <span className="inline-flex w-5 h-5 rounded-full bg-[#7b2d3b] text-white items-center justify-center text-[10px] mr-2">3</span>
                  Season
                </h2>
                <div className="grid grid-cols-2 gap-2">
                  {SEASONS.map(s => (
                    <button
                      key={s}
                      onClick={() => setSeason(s)}
                      className={`py-2 px-3 rounded-xl text-xs font-bold border flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                        season === s
                          ? 'bg-gray-100 border-gray-400 text-gray-900'
                          : 'bg-white border-gray-100 text-gray-500 hover:bg-gray-50'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* Fit */}
              <div>
                <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">
                  <span className="inline-flex w-5 h-5 rounded-full bg-[#7b2d3b] text-white items-center justify-center text-[10px] mr-2">4</span>
                  Fit Preference
                </h2>
                <div className="flex bg-gray-100 p-1 rounded-xl">
                  {FITS.map(f => (
                    <button
                      key={f}
                      onClick={() => setFit(f)}
                      className={`flex-1 py-2 text-[11px] font-bold rounded-lg transition-all cursor-pointer ${
                        fit === f ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-800'
                      }`}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Generate button */}
          <div className="mt-8 pt-6 border-t border-gray-100">
            <div className="flex items-center gap-4 bg-[#f3f4f6] rounded-2xl px-5 py-3.5 mb-4">
              <div className="w-8 h-8 rounded-full bg-[#7b2d3b]/10 flex items-center justify-center text-sm">✨</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-gray-800">
                  AI Ready — {wardrobeItems.length} items in your closet
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {occasion.charAt(0).toUpperCase() + occasion.slice(1)} · {style} · {seasonLabel} · {fit}
                </p>
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={generating || wardrobeItems.length === 0}
              className="w-full bg-[#7b2d3b] hover:bg-[#5e1f2b] disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold py-4 rounded-2xl shadow-[0_8px_20px_rgba(123,45,59,0.2)] transition-all hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-2 cursor-pointer text-base"
            >
              {generating ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Generating outfit combinations…
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                  </svg>
                  Generate AI Outfit Recommendations
                </>
              )}
            </button>
          </div>
        </div>

        {/* ── ERROR ── */}
        {genError && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-4 mb-6 flex items-start gap-3">
            <span className="text-xl">⚠️</span>
            <div>
              <p className="font-semibold text-red-700 text-sm">Generation failed</p>
              <p className="text-xs text-red-500 mt-0.5">{genError}</p>
            </div>
          </div>
        )}

        {/* ── RESULTS ── */}
        {generated && outfits.length === 0 && (
          <div className="text-center py-10 text-gray-400">
            <span className="text-4xl block mb-3">🤔</span>
            <p className="text-sm">No outfit combinations found for those preferences. Try adjusting your criteria.</p>
          </div>
        )}

        {outfits.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-xl font-bold">Your Outfit Recommendations</h2>
                <p className="text-sm text-gray-400 mt-0.5">
                  {outfits.length} combination{outfits.length !== 1 ? 's' : ''} curated for you
                </p>
              </div>
              <button
                onClick={() => { setOutfits([]); setGenerated(false); }}
                className="text-xs text-gray-400 hover:text-gray-700 border border-gray-200 rounded-xl px-3 py-1.5 transition-colors cursor-pointer"
              >
                Clear
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {outfits.map((outfit, i) => (
                <OutfitCard
                  key={outfit.id || i}
                  outfit={outfit}
                  wardrobeItems={wardrobeItems}
                  rank={i + 1}
                  onTryOn={setVtonOutfit}
                />
              ))}
            </div>
          </div>
        )}

      </div>

      {/* ── OUTFIT VTON MODAL ── */}
      {vtonOutfit && (
        <OutfitVtonModal
          outfit={vtonOutfit}
          wardrobeItems={wardrobeItems}
          onClose={() => setVtonOutfit(null)}
        />
      )}
    </div>
  );
};

export default FindOutfit;

