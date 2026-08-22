import React, { useState } from 'react';

const DigitalCloset = () => {
  const [selectedItem, setSelectedItem] = useState(null); // null means no item selected (modal closed)

  return (
    <div className="min-h-screen bg-[#FDFBF7] flex flex-row font-sans text-[#111317]">

      {/* 1. LEFT SIDEBAR (Always Visible) */}
      <div className="flex w-30 md:w-48 lg:w-64 border-r border-gray-200/60 p-4 md:p-6 lg:p-8 flex-col shrink-0">
        <h1 className="hidden md:block text-xs lg:text-sm font-bold tracking-widest uppercase mb-12">My Wardrobe</h1>
        <nav className="flex flex-col gap-6 text-lg md:text-xl lg:text-2xl font-bold text-gray-800">
          <a href="#" className="hover:text-black">Shirts</a>
          <a href="#" className="hover:text-black">Blazers</a>
          <a href="#" className="hover:text-black">Trousers</a>
          <a href="#" className="hover:text-black">Jeans</a>
          <a href="#" className="hover:text-black">Dresses</a>
        </nav>
      </div>

      {/* 3. MIDDLE SECTION (Item Grid) */}
      <div className="flex-1 p-4 md:p-8 overflow-y-auto">
        <div className="mb-6 md:mb-8">
          <h2 className="text-2xl md:text-3xl font-bold mb-1">Blazers</h2>
          <p className="text-xs md:text-sm text-gray-500">8 Items</p>
        </div>

        {/* The Grid */}
        <div className="grid md:grid-cols-3 grid-cols-2 xl:grid-cols-4 gap-3 md:gap-4">

          {/* Item Card (Clicking opens modal) */}
          <div onClick={() => setSelectedItem('Brown Blazer')} className="bg-[#f5f4f1] rounded-2xl p-3 md:p-4 flex flex-col items-center justify-between border border-black h-48 md:h-72 cursor-pointer shadow-sm">
            <div className="w-full flex-1 flex items-center justify-center">
              <span className="text-4xl md:text-6xl"></span>
            </div>
            <p className="text-xs md:text-sm font-semibold mt-2 md:mt-4">Brown Blazer</p>
          </div>

          <div onClick={() => setSelectedItem('Navy Blazer')} className="bg-[#f5f4f1] rounded-2xl p-3 md:p-4 flex flex-col items-center justify-between border border-transparent hover:border-gray-300 transition-colors h-48 md:h-72 cursor-pointer shadow-sm">
            <div className="w-full flex-1 flex items-center justify-center">
              <span className="text-4xl md:text-6xl"></span>
            </div>
            <p className="text-xs md:text-sm font-medium text-gray-600 mt-2 md:mt-4">Navy Blazer</p>
          </div>

        </div>
      </div>

      {/* 4. ITEM DETAILS (Desktop Sidebar OR Mobile Spotify-style Modal) */}
      <div className={`
        ${selectedItem ? 'fixed inset-0 z-50 bg-[#FDFBF7] p-6 lg:p-8 overflow-y-auto lg:relative lg:inset-auto lg:z-auto' : 'hidden lg:flex'}
        w-full lg:w-80 xl:w-96 lg:border-l border-gray-200/60 flex-col  shrink-0
      `}>

        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl md:text-2xl font-bold">{selectedItem || 'Brown Blazer'}</h2>

          <div className="flex items-center gap-4">
            <button className="text-gray-400 hover:text-black text-xl hidden lg:block">•••</button>
            {/* Close button only visible on mobile/tablet modal */}
            <button onClick={() => setSelectedItem(null)} className="lg:hidden text-2xl font-bold text-gray-800 cursor-pointer">✕</button>
          </div>
        </div>

        {/* Large Image Preview */}
        <div className="w-full aspect-square bg-[#f5f4f1] rounded-2xl md:rounded-3xl mb-6 md:mb-8 flex items-center justify-center shadow-sm">
          <span className="text-6xl md:text-8xl"></span>
        </div>

        {/* Details Section */}
        <div className="flex flex-col gap-4 md:gap-6">

          <div>
            <p className="text-xs font-bold mb-1 text-gray-800">Category</p>
            <p className="text-sm text-gray-600">Blazers</p>
          </div>

          <div>
            <p className="text-xs font-bold mb-2 text-gray-800">Color</p>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 md:w-5 md:h-5 rounded-full bg-[#8b603e]"></div>
              <p className="text-sm text-gray-600">Brown</p>
            </div>
          </div>

          <div>
            <p className="text-xs font-bold mb-2 text-gray-800">Occasion</p>
            <div className="flex flex-wrap gap-2">
              <span className="px-2 py-1 md:px-3 rounded-full border border-gray-300 text-[10px] md:text-xs text-gray-600">Business</span>
              <span className="px-2 py-1 md:px-3 rounded-full border border-gray-300 text-[10px] md:text-xs text-gray-600">Formal</span>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};

export default DigitalCloset;
