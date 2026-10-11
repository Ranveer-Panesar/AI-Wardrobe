import { useState, useEffect, useRef, useCallback } from 'react';
import { getItems, uploadItem, deleteItem, resolveImageUrl, generateSyntheticCloset } from '../api/wardrobe';
import { startMannequinRender, pollRenderJob } from '../api/render';

/* ──────────────────────────────────────────────
   Tiny helpers
   ────────────────────────────────────────────── */
const CATEGORY_ICONS = {
  shirt: '👔', tshirt: '👕', top: '👚', blouse: '👘',
  jacket: '🧥', coat: '🥼', blazer: '🧥', hoodie: '🧣',
  trousers: '👖', pants: '👖', jeans: '👖', shorts: '🩳',
  dress: '👗', skirt: '🩱', suit: '🤵',
  shoes: '👟', boots: '🥾', heels: '👠', sneakers: '👟',
  bag: '👜', accessory: '💍', hat: '🎩',
};

function categoryIcon(cat = '') {
  const key = cat.toLowerCase().replace(/[\s-]+/g, '');
  for (const [k, v] of Object.entries(CATEGORY_ICONS)) {
    if (key.includes(k)) return v;
  }
  return '🧺';
}

/* ──────────────────────────────────────────────
   Sub-component: Upload Drop Zone
   ────────────────────────────────────────────── */
function UploadZone({ onUpload, uploading }) {
  const inputRef = useRef();
  const [dragging, setDragging] = useState(false);

  const handleFiles = (files) => {
    const img = Array.from(files).find(f => f.type.startsWith('image/'));
    if (img) onUpload(img);
  };

  return (
    <div
      onDragOver={e => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
      onClick={() => inputRef.current?.click()}
      className={`
        group relative flex flex-col items-center justify-center gap-3
        rounded-2xl border-2 border-dashed cursor-pointer
        transition-all duration-200 h-40
        ${dragging
          ? 'border-[#7b2d3b] bg-[#7b2d3b]/5 scale-[1.01]'
          : 'border-gray-200 hover:border-[#7b2d3b]/50 hover:bg-gray-50'
        }
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="sr-only"
        onChange={e => handleFiles(e.target.files)}
      />

      {uploading ? (
        <>
          <svg className="animate-spin w-8 h-8 text-[#7b2d3b]" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm text-gray-500 font-medium">Uploading & tagging…</p>
        </>
      ) : (
        <>
          <div className="w-12 h-12 rounded-full bg-gray-100 group-hover:bg-[#7b2d3b]/10 flex items-center justify-center transition-colors">
            <svg className="w-6 h-6 text-gray-400 group-hover:text-[#7b2d3b] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
          </div>
          <div className="text-center">
            <p className="text-sm font-semibold text-gray-700 group-hover:text-[#7b2d3b] transition-colors">
              Drop a photo or click to upload
            </p>
            <p className="text-xs text-gray-400 mt-0.5">JPG, PNG, WEBP — AI will auto-tag it</p>
          </div>
        </>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────────
   Sub-component: VTON Panel
   ────────────────────────────────────────────── */
function VtonPanel({ item, onClose }) {
  const [state, setState] = useState('idle'); // idle | rendering | done | error
  const [renderUrl, setRenderUrl] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [progress, setProgress] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const getProgressMsg = (elapsedSeconds) => {
    if (elapsedSeconds < 5)  return 'Queued — starting GPU…';
    if (elapsedSeconds < 180) return 'Downloading model weights (first run only)…';
    return 'Running CatVTON inference on RTX 5060 Ti…';
  };

  const startRender = async () => {
    setState('rendering');
    setElapsed(0);
    setProgress('Queued — starting GPU…');
    try {
      const { job_id } = await startMannequinRender(item.id);
      const url = await pollRenderJob(job_id, (job) => {
        setElapsed(job.elapsedSeconds || 0);
        setProgress(getProgressMsg(job.elapsedSeconds || 0));
      });
      setRenderUrl(url);
      setState('done');
    } catch (err) {
      setErrorMsg(err.message);
      setState('error');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-sm overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <div>
            <p className="text-xs uppercase tracking-widest text-gray-400 font-semibold">Virtual Try-On</p>
            <h3 className="font-bold text-gray-900 mt-0.5">{item.category || item.filename}</h3>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-400 hover:text-gray-700 transition-colors cursor-pointer">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-5">
          {state === 'idle' && (
            <div className="text-center space-y-4">
              <div className="w-20 h-20 mx-auto rounded-2xl overflow-hidden bg-gray-100 border border-gray-200">
                {item.image_url
                  ? <img src={resolveImageUrl(item.image_url)} alt={item.category} className="w-full h-full object-cover" />
                  : <span className="text-4xl flex items-center justify-center h-full">{categoryIcon(item.category)}</span>
                }
              </div>
              <p className="text-sm text-gray-500">
                Renders this garment on the model using <strong>CatVTON</strong> on your <strong>RTX 5060 Ti</strong>.
                Takes ~35s. <span className="text-amber-600 font-medium">First run takes 2-3 min</span> to download model weights.
              </p>
              <button
                onClick={startRender}
                className="w-full bg-[#7b2d3b] hover:bg-[#5e1f2b] text-white font-semibold py-3 rounded-xl shadow-lg shadow-[#7b2d3b]/20 transition-all hover:-translate-y-0.5 cursor-pointer"
              >
                ✨ Generate Try-On
              </button>
            </div>
          )}

          {state === 'rendering' && (
            <div className="text-center py-4 space-y-4">
              {/* Spinner */}
              <div className="relative w-20 h-20 mx-auto">
                <svg className="animate-spin w-20 h-20 text-[#7b2d3b]/20" fill="none" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                </svg>
                <svg className="animate-spin absolute inset-0 w-20 h-20 text-[#7b2d3b]" fill="none" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-700">Rendering on GPU…</p>
                <p className="text-xs text-gray-500 mt-1">{progress}</p>
                <p className="text-xs text-gray-400 mt-0.5 tabular-nums">{elapsed}s elapsed</p>
              </div>
              {elapsed > 20 && (
                <p className="text-[10px] text-amber-600 bg-amber-50 rounded-lg px-3 py-2">
                  {elapsed < 180
                    ? '⬇ Downloading model weights for the first time — this only happens once.'
                    : '🎨 AI is compositing your garment — almost there!'}
                </p>
              )}
            </div>
          )}

          {state === 'done' && renderUrl && (
            <div className="space-y-3">
              <img
                src={renderUrl}
                alt="Try-on result"
                className="w-full rounded-2xl object-cover border border-gray-100 shadow-sm"
              />
              <div className="flex gap-2">
                <a
                  href={renderUrl}
                  download
                  className="flex-1 text-center bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2.5 rounded-xl text-sm transition-colors cursor-pointer"
                >
                  ⬇ Download
                </a>
                <button
                  onClick={() => { setState('idle'); setRenderUrl(null); }}
                  className="flex-1 bg-[#7b2d3b] hover:bg-[#5e1f2b] text-white font-semibold py-2.5 rounded-xl text-sm transition-colors cursor-pointer"
                >
                  🔄 Re-render
                </button>
              </div>
            </div>
          )}

          {state === 'error' && (
            <div className="text-center space-y-3 py-2">
              <div className="text-4xl">⚠️</div>
              <p className="text-sm font-semibold text-red-600">Render failed</p>
              <p className="text-xs text-gray-400 break-all">{typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg)}</p>
              <button
                onClick={() => { setState('idle'); setErrorMsg(''); }}
                className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2.5 rounded-xl text-sm transition-colors cursor-pointer"
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
   Main Component
   ────────────────────────────────────────────── */
const DigitalCloset = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [selectedItem, setSelectedItem] = useState(null);
  const [vtonItem, setVtonItem] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const [seeding, setSeeding] = useState(false);
  const [seedSuccess, setSeedSuccess] = useState('');

  const handleGenerateSynthetic = async (replace = false) => {
    setSeeding(true);
    setUploadError('');
    setSeedSuccess('');
    try {
      const res = await generateSyntheticCloset(replace, 16);
      setSeedSuccess(`Generated ${res.total || res.items?.length || 16} synthetic items through the AI classification pipeline!`);
      await loadItems();
      setTimeout(() => setSeedSuccess(''), 5000);
    } catch (e) {
      setUploadError(e.message || 'Failed to generate synthetic closet');
    } finally {
      setSeeding(false);
    }
  };

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getItems();
      setItems(data.items || []);
    } catch (e) {
      setError('Could not connect to backend. Is the server running on port 8000?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadItems(); }, [loadItems]);

  // Derive categories from actual items
  const categories = ['All', ...new Set(
    items.map(i => i.category || 'Other').filter(Boolean)
  )];

  const filtered = activeCategory === 'All'
    ? items
    : items.filter(i => i.category === activeCategory);

  const handleUpload = async (file) => {
    setUploading(true);
    setUploadError('');
    try {
      await uploadItem(file);
      await loadItems();
    } catch (e) {
      setUploadError(e.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteItem(id);
      setSelectedItem(null);
      setDeleteConfirm(null);
      await loadItems();
    } catch (e) {
      console.error('Delete failed', e);
    }
  };

  return (
    <div className="mt-16 min-h-screen bg-[#FDFBF7] flex flex-col font-sans text-[#111317]">
      <div className="flex flex-1 h-[calc(100vh-4rem)] overflow-hidden">

        {/* ── LEFT SIDEBAR ── */}
        <aside className="hidden md:flex w-56 lg:w-64 border-r border-gray-100 flex-col shrink-0 overflow-y-auto">
          <div className="p-6 flex-1">
            <p className="text-[10px] font-bold tracking-widest uppercase text-gray-400 mb-5">My Wardrobe</p>

            {/* Upload zone */}
            <div className="mb-6">
              <UploadZone onUpload={handleUpload} uploading={uploading} />
              {uploadError && (
                <p className="text-xs text-red-500 mt-2 px-1">{uploadError}</p>
              )}
            </div>

            {/* Category nav */}
            <nav className="flex flex-col gap-1">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`text-left px-3 py-2 rounded-xl text-sm font-medium transition-colors cursor-pointer ${
                    activeCategory === cat
                      ? 'bg-[#7b2d3b]/8 text-[#7b2d3b] font-semibold'
                      : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <span className="mr-2">{cat === 'All' ? '🗂' : categoryIcon(cat)}</span>
                  <span className="capitalize">{cat}</span>
                </button>
              ))}
            </nav>
          </div>

          <div className="p-4 border-t border-gray-100">
            <p className="text-xs text-gray-400 text-center">{items.length} item{items.length !== 1 ? 's' : ''} in closet</p>
          </div>
        </aside>

        {/* ── MAIN GRID ── */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          {/* Mobile upload bar */}
          <div className="md:hidden mb-4">
            <UploadZone onUpload={handleUpload} uploading={uploading} />
            {uploadError && <p className="text-xs text-red-500 mt-1">{uploadError}</p>}
          </div>

          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-2xl font-bold">{activeCategory}</h2>
              <p className="text-sm text-gray-400 mt-0.5">{filtered.length} item{filtered.length !== 1 ? 's' : ''}</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleGenerateSynthetic(false)}
                disabled={seeding}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white border border-[#7b2d3b]/30 text-[#7b2d3b] hover:bg-[#7b2d3b]/5 text-xs font-bold transition-all shadow-sm cursor-pointer disabled:opacity-50"
                title="Populate test items from fashion dataset running through the AI classifier"
              >
                {seeding ? (
                  <>
                    <svg className="animate-spin w-3.5 h-3.5 text-[#7b2d3b]" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span>Classifying Dataset Items…</span>
                  </>
                ) : (
                  <>
                    <span>⚡</span>
                    <span>Generate Synthetic Closet</span>
                  </>
                )}
              </button>
              <div className="md:hidden">
                <select
                  value={activeCategory}
                  onChange={e => setActiveCategory(e.target.value)}
                  className="border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-700 bg-white focus:outline-none focus:border-[#7b2d3b] cursor-pointer"
                >
                  {categories.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Success Banner */}
          {seedSuccess && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs px-4 py-2.5 rounded-xl mb-4 flex items-center gap-2">
              <span>🎉</span>
              <span className="font-medium">{seedSuccess}</span>
            </div>
          )}

          {/* State: Loading */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-24 text-gray-400 gap-3">
              <svg className="animate-spin w-8 h-8" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p className="text-sm">Loading your wardrobe…</p>
            </div>
          )}

          {/* State: Error */}
          {!loading && error && (
            <div className="flex flex-col items-center justify-center py-24 gap-3">
              <span className="text-4xl">⚠️</span>
              <p className="text-sm text-red-500 text-center max-w-xs">{error}</p>
              <button onClick={loadItems} className="text-sm text-[#7b2d3b] underline cursor-pointer">Retry</button>
            </div>
          )}

          {/* State: Empty */}
          {!loading && !error && filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 gap-4 text-gray-400">
              <span className="text-5xl">🧺</span>
              <p className="text-base font-semibold text-gray-600">Your closet is empty</p>
              <p className="text-sm text-center max-w-xs text-gray-500">
                Upload a photo of any garment above, or generate a synthetic closet from the clothing dataset to test the AI stylist algorithm immediately.
              </p>
              <button
                onClick={() => handleGenerateSynthetic(false)}
                disabled={seeding}
                className="mt-2 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#7b2d3b] text-white hover:bg-[#5e1f2b] text-xs font-bold transition-all shadow-sm cursor-pointer disabled:opacity-50"
              >
                {seeding ? 'Classifying Dataset Items…' : '✨ Generate Synthetic Closet (Dataset)'}
              </button>
            </div>
          )}

          {/* Grid */}
          {!loading && !error && filtered.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 md:gap-4">
              {filtered.map(item => (
                <div
                  key={item.id}
                  onClick={() => setSelectedItem(item)}
                  className={`group relative bg-white rounded-2xl border overflow-hidden cursor-pointer shadow-sm hover:shadow-md transition-all duration-200 ${
                    selectedItem?.id === item.id ? 'border-[#7b2d3b] ring-2 ring-[#7b2d3b]/20' : 'border-gray-100 hover:border-gray-200'
                  }`}
                >
                  {/* Image */}
                  <div className="aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
                    {item.image_url ? (
                      <img
                        src={resolveImageUrl(item.image_url)}
                        alt={item.category || item.filename}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <span className="text-4xl">{categoryIcon(item.category)}</span>
                    )}
                  </div>

                  {/* Info */}
                  <div className="p-2.5">
                    <p className="text-xs font-semibold text-gray-800 truncate capitalize">{item.category || 'Garment'}</p>
                    {item.dominant_colors?.[0] && (
                      <p className="text-[10px] text-gray-400 mt-0.5 capitalize">{item.dominant_colors[0]}</p>
                    )}
                  </div>

                  {/* VTON quick button */}
                  <button
                    onClick={e => { e.stopPropagation(); setVtonItem(item); }}
                    className="absolute top-2 right-2 w-7 h-7 rounded-full bg-white/80 backdrop-blur-sm border border-gray-200 flex items-center justify-center text-sm opacity-0 group-hover:opacity-100 transition-opacity hover:bg-[#7b2d3b] hover:border-[#7b2d3b] hover:text-white cursor-pointer"
                    title="Virtual Try-On"
                  >
                    ✨
                  </button>
                </div>
              ))}
            </div>
          )}
        </main>

        {/* ── ITEM DETAIL PANEL ── */}
        {selectedItem && (
          <aside className="hidden lg:flex w-72 xl:w-80 border-l border-gray-100 flex-col shrink-0 overflow-y-auto">
            <div className="p-6 flex-1 flex flex-col gap-5">
              <div className="flex items-start justify-between">
                <h3 className="font-bold text-lg capitalize">{selectedItem.label || 'Garment'}</h3>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="w-7 h-7 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-400 hover:text-gray-700 transition-colors cursor-pointer"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Image */}
              <div className="w-full aspect-square bg-gray-50 rounded-2xl overflow-hidden border border-gray-100">
                {selectedItem.image_url ? (
                  <img
                    src={resolveImageUrl(selectedItem.image_url)}
                    alt={selectedItem.category}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-6xl">
                    {categoryIcon(selectedItem.category)}
                  </div>
                )}
              </div>

              {/* Metadata */}
              <div className="space-y-3">
                {selectedItem.dominant_colors?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Color</p>
                    <div className="flex gap-1.5 flex-wrap">
                      {selectedItem.dominant_colors.map((c, i) => (
                        <span key={i} className="px-2.5 py-1 bg-gray-100 rounded-full text-xs text-gray-600 capitalize">{c}</span>
                      ))}
                    </div>
                  </div>
                )}
                {selectedItem.pattern && (
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Pattern</p>
                    <p className="text-sm text-gray-700 capitalize">{selectedItem.pattern}</p>
                  </div>
                )}
                {selectedItem.formality && (
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Formality</p>
                    <p className="text-sm text-gray-700 capitalize">{selectedItem.formality}</p>
                  </div>
                )}
                {selectedItem.category_confidence !== undefined && (
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">AI Confidence</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[#7b2d3b] rounded-full"
                          style={{ width: `${(selectedItem.category_confidence || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold text-gray-600">{Math.round((selectedItem.category_confidence || 0) * 100)}%</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex flex-col gap-2 mt-auto pt-2">
                <button
                  onClick={() => setVtonItem(selectedItem)}
                  className="w-full bg-[#7b2d3b] hover:bg-[#5e1f2b] text-white font-semibold py-3 rounded-xl shadow-sm shadow-[#7b2d3b]/20 transition-all hover:-translate-y-0.5 cursor-pointer text-sm"
                >
                  ✨ Virtual Try-On
                </button>
                {deleteConfirm === selectedItem.id ? (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDelete(selectedItem.id)}
                      className="flex-1 bg-red-500 hover:bg-red-600 text-white font-semibold py-2.5 rounded-xl text-sm transition-colors cursor-pointer"
                    >
                      Confirm Delete
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(null)}
                      className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2.5 rounded-xl text-sm transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setDeleteConfirm(selectedItem.id)}
                    className="w-full bg-gray-100 hover:bg-red-50 text-gray-500 hover:text-red-500 font-semibold py-2.5 rounded-xl text-sm transition-colors cursor-pointer"
                  >
                    🗑 Remove from Closet
                  </button>
                )}
              </div>
            </div>
          </aside>
        )}
      </div>

      {/* ── VTON MODAL ── */}
      {vtonItem && (
        <VtonPanel item={vtonItem} onClose={() => setVtonItem(null)} />
      )}
    </div>
  );
};

export default DigitalCloset;