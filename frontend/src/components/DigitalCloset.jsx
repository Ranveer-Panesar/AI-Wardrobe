import React, { useState, useEffect, useRef } from 'react';
import { getItems, uploadItem, deleteItem, resolveImageUrl } from '../api/wardrobe';

// Map backend categories to sidebar nav groupings
const CATEGORY_GROUPS = {
  Shirts: ['shirt', 'formal shirt', 't-shirt', 'top', 'blouse', 'polo'],
  Blazers: ['blazer', 'suit jacket', 'sport coat'],
  Trousers: ['trousers', 'pants', 'chinos', 'shorts'],
  Jeans: ['jeans', 'denim'],
  Dresses: ['dress', 'skirt', 'jumpsuit'],
};

function categoryGroup(category = '') {
  const lower = category.toLowerCase();
  for (const [group, keywords] of Object.entries(CATEGORY_GROUPS)) {
    if (keywords.some((k) => lower.includes(k))) return group;
  }
  return 'All';
}

const DigitalCloset = () => {
  const [selectedItem, setSelectedItem] = useState(null);
  const [garments, setGarments] = useState([]);
  const [activeGroup, setActiveGroup] = useState('All');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  // Fetch garments on mount
  useEffect(() => {
    getItems()
      .then((data) => setGarments(data.items || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const newGarment = await uploadItem(file);
      setGarments((prev) => [newGarment, ...prev]);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteItem(id);
      setGarments((prev) => prev.filter((g) => g.id !== id));
      if (selectedItem?.id === id) setSelectedItem(null);
    } catch (err) {
      setError(err.message);
    }
  };

  // Filter displayed garments by active sidebar group
  const displayed = activeGroup === 'All'
    ? garments
    : garments.filter((g) => categoryGroup(g.category) === activeGroup);

  return (
    <div className="min-h-screen bg-[#FDFBF7] flex flex-row font-sans text-[#111317]">

      {/* 1. LEFT SIDEBAR (Always Visible) */}
      <div className="flex w-30 md:w-48 lg:w-64 border-r border-gray-200/60 p-4 md:p-6 lg:p-8 flex-col shrink-0">
        <h1 className="hidden md:block text-xs lg:text-sm font-bold tracking-widest uppercase mb-12">My Wardrobe</h1>
        <nav className="flex flex-col gap-6 text-lg md:text-xl lg:text-2xl font-bold text-gray-800">
          {['All', ...Object.keys(CATEGORY_GROUPS)].map((group) => (
            <a
              key={group}
              href="#"
              onClick={(e) => { e.preventDefault(); setActiveGroup(group); setSelectedItem(null); }}
              className={`hover:text-black transition-colors ${activeGroup === group ? 'text-black' : 'text-gray-400'}`}
            >
              {group}
            </a>
          ))}
        </nav>
      </div>

      {/* 3. MIDDLE SECTION (Item Grid) */}
      <div className="flex-1 p-4 md:p-8 overflow-y-auto">
        <div className="mb-6 md:mb-8 flex items-start justify-between">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold mb-1">{activeGroup}</h2>
            <p className="text-xs md:text-sm text-gray-500">{displayed.length} Items</p>
          </div>

          {/* Upload button */}
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleUpload}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="bg-black text-white text-xs md:text-sm font-medium px-4 py-2 rounded-full hover:bg-gray-800 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {uploading ? 'Classifying…' : '+ Add Item'}
            </button>
          </div>
        </div>

        {error && (
          <p className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2 mb-4">{error}</p>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Loading your wardrobe…</div>
        ) : displayed.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 gap-3 text-gray-400">
            <span className="text-4xl">👗</span>
            <p className="text-sm">No items yet — click <strong>+ Add Item</strong> to upload your first garment</p>
          </div>
        ) : (
          /* The Grid — identical classes to what the dev wrote */
          <div className="grid md:grid-cols-3 grid-cols-2 xl:grid-cols-4 gap-3 md:gap-4">
            {displayed.map((garment) => (
              <div
                key={garment.id}
                onClick={() => setSelectedItem(garment)}
                className={`bg-[#f5f4f1] rounded-2xl p-3 md:p-4 flex flex-col items-center justify-between border h-48 md:h-72 cursor-pointer shadow-sm transition-colors ${
                  selectedItem?.id === garment.id ? 'border-black' : 'border-transparent hover:border-gray-300'
                }`}
              >
                <div className="w-full flex-1 flex items-center justify-center overflow-hidden rounded-xl">
                  {garment.image_url ? (
                    <img
                      src={resolveImageUrl(garment.image_url)}
                      alt={garment.category}
                      className="w-full h-full object-cover rounded-xl"
                    />
                  ) : (
                    <span className="text-4xl md:text-6xl">👔</span>
                  )}
                </div>
                <p className="text-xs md:text-sm font-semibold mt-2 md:mt-4 capitalize">{garment.category}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4. ITEM DETAILS (Desktop Sidebar OR Mobile Modal) — identical structure to dev's code */}
      <div className={`
        ${selectedItem ? 'fixed inset-0 z-50 bg-[#FDFBF7] p-6 lg:p-8 overflow-y-auto lg:relative lg:inset-auto lg:z-auto' : 'hidden lg:flex'}
        w-full lg:w-80 xl:w-96 lg:border-l border-gray-200/60 flex-col  shrink-0
      `}>

        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl md:text-2xl font-bold capitalize">
            {selectedItem?.category || 'Select an item'}
          </h2>

          <div className="flex items-center gap-4">
            {selectedItem && (
              <button
                onClick={() => handleDelete(selectedItem.id)}
                className="text-red-400 hover:text-red-600 text-xs font-semibold transition-colors"
                title="Remove garment"
              >
                Delete
              </button>
            )}
            <button className="text-gray-400 hover:text-black text-xl hidden lg:block">•••</button>
            {/* Close button only visible on mobile/tablet modal */}
            <button onClick={() => setSelectedItem(null)} className="lg:hidden text-2xl font-bold text-gray-800 cursor-pointer">✕</button>
          </div>
        </div>

        {/* Large Image Preview */}
        <div className="w-full aspect-square bg-[#f5f4f1] rounded-2xl md:rounded-3xl mb-6 md:mb-8 flex items-center justify-center shadow-sm overflow-hidden">
          {selectedItem?.image_url ? (
            <img
              src={resolveImageUrl(selectedItem.image_url)}
              alt={selectedItem.category}
              className="w-full h-full object-cover"
            />
          ) : (
            <span className="text-6xl md:text-8xl">👗</span>
          )}
        </div>

        {/* Details Section */}
        <div className="flex flex-col gap-4 md:gap-6">

          <div>
            <p className="text-xs font-bold mb-1 text-gray-800">Category</p>
            <p className="text-sm text-gray-600 capitalize">{selectedItem?.category || '—'}</p>
          </div>

          <div>
            <p className="text-xs font-bold mb-2 text-gray-800">Color</p>
            <div className="flex items-center gap-2 flex-wrap">
              {selectedItem?.dominant_colors?.length ? (
                selectedItem.dominant_colors.map((hex) => (
                  <div key={hex} className="flex items-center gap-1.5">
                    <div className="w-4 h-4 md:w-5 md:h-5 rounded-full border border-gray-200" style={{ backgroundColor: hex }} />
                    <p className="text-sm text-gray-600">{hex}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-600">—</p>
              )}
            </div>
          </div>

          <div>
            <p className="text-xs font-bold mb-2 text-gray-800">Pattern</p>
            <span className="px-2 py-1 md:px-3 rounded-full border border-gray-300 text-[10px] md:text-xs text-gray-600 capitalize">
              {selectedItem?.pattern || '—'}
            </span>
          </div>

          <div>
            <p className="text-xs font-bold mb-2 text-gray-800">Occasion</p>
            <div className="flex flex-wrap gap-2">
              {selectedItem?.formality ? (
                <span className="px-2 py-1 md:px-3 rounded-full border border-gray-300 text-[10px] md:text-xs text-gray-600 capitalize">
                  {selectedItem.formality}
                </span>
              ) : (
                <p className="text-sm text-gray-600">—</p>
              )}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};

export default DigitalCloset;
