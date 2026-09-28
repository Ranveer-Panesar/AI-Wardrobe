import { useState } from 'react';

const CLOSET_DATA = {
  Shirts: [
    { id: 1, name: 'White Oxford', emoji: '👔', color: 'White', colorHex: '#f8fafc', occasions: ['Business', 'Formal'] },
    { id: 2, name: 'Denim Shirt', emoji: '👕', color: 'Blue', colorHex: '#3b82f6', occasions: ['Casual', 'Smart Casual'] },
  ],
  Blazers: [
    { id: 3, name: 'Brown Blazer', emoji: '🧥', color: 'Brown', colorHex: '#8b603e', occasions: ['Business', 'Formal'] },
    { id: 4, name: 'Navy Blazer', emoji: '🧥', color: 'Navy', colorHex: '#1e293b', occasions: ['Smart Casual', 'Business'] },
    { id: 5, name: 'Grey Check Blazer', emoji: '🧥', color: 'Grey', colorHex: '#64748b', occasions: ['Smart Casual'] },
  ],
  Trousers: [
    { id: 6, name: 'Khaki Chinos', emoji: '👖', color: 'Khaki', colorHex: '#d4d4d8', occasions: ['Casual', 'Smart Casual'] },
    { id: 7, name: 'Black Slacks', emoji: '👖', color: 'Black', colorHex: '#0f172a', occasions: ['Business', 'Formal'] },
  ],
  Jeans: [
    { id: 8, name: 'Classic Blue Jeans', emoji: '👖', color: 'Blue', colorHex: '#2563eb', occasions: ['Casual'] },
  ],
  Dresses: [
    { id: 9, name: 'Little Black Dress', emoji: '👗', color: 'Black', colorHex: '#000000', occasions: ['Formal', 'Evening'] },
  ]
};

const CATEGORIES = Object.keys(CLOSET_DATA);

const DigitalCloset = () => {
  // State for category and item
  const [activeCategory, setActiveCategory] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);

  // Helper to change category and reset the selected item
  const handleCategoryClick = (category) => {
    setActiveCategory(category);
    setSelectedItem(null);
  };

  const activeItems = CLOSET_DATA[activeCategory] || [];

  return (
    <div className=" mt-16 min-h-screen bg-[#FDFBF7] flex flex-row font-sans text-[#111317]">

      {/* 1. LEFT SIDEBAR */}
      <div className="flex w-32 md:w-48 lg:w-64 border-r border-gray-200/60 p-4 md:p-6 lg:p-8 flex-col shrink-0 justify-between">

        <div>
          <h1 className="hidden md:block text-xs lg:text-sm font-bold tracking-widest uppercase mb-12">My Wardrobe</h1>
          <nav className="flex flex-col gap-6 text-lg md:text-xl lg:text-2xl font-bold text-gray-800">
            {CATEGORIES.map(category => (
              <button
                key={category}
                onClick={() => handleCategoryClick(category)}
                className={`text-left hover:text-black cursor-pointer ${activeCategory === category ? 'underline decoration-2 underline-offset-8' : 'text-gray-500'}`}
              >
                {category}
              </button>
            ))}
          </nav>
        </div>

        {/* Profile Section */}
        <div className="mt-8 flex items-center gap-3 cursor-pointer p-2 -ml-2 rounded-xl hover:bg-gray-100 transition-colors">
          <div className="w-10 h-10 rounded-full bg-gray-200 border border-gray-300 overflow-hidden shrink-0">
            <img src="https://api.dicebear.com/7.x/notionists/svg?seed=Felix" alt="User Profile" className="w-full h-full object-cover" />
          </div>
          <div className="hidden lg:block overflow-hidden">
            <p className="text-sm font-bold text-gray-900 truncate">Felix Stylist</p>
            <p className="text-xs text-gray-500 truncate">Pro Member</p>
          </div>
        </div>

      </div>

      {/* 2. MIDDLE SECTION */}
      <div className="flex-1 p-4 md:p-8 overflow-y-auto">
        <div className="mb-6 md:mb-8">
          <h2 className="text-2xl md:text-3xl font-bold mb-1">{activeCategory}</h2>
          <p className="text-xs md:text-sm text-gray-500">{activeItems.length} Items</p>
        </div>

        <div className="grid md:grid-cols-2 grid-cols-2 xl:grid-cols-3 gap-3 md:gap-4">
          {activeItems.map((item) => (
            <div
              key={item.id}
              onClick={() => setSelectedItem(item)}
              className={`bg-[#f5f4f1] rounded-2xl p-3 md:p-4 flex flex-col items-center justify-between border h-40 md:h-50 cursor-pointer shadow-sm transition-colors ${selectedItem?.id === item.id ? 'border-black' : 'border-transparent hover:border-gray-300'}`}
            >
              <div className="w-full flex-1 flex items-center justify-center">
                <span className="text-4xl md:text-6xl">{item.emoji}</span>
              </div>
              <p className="text-xs md:text-sm font-semibold mt-2 md:mt-4 text-center">{item.name}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 3. ITEM DETAILS */}
      <div className={`
        ${selectedItem ? 'fixed inset-0 z-50 bg-[#FDFBF7] p-6 lg:p-8 overflow-y-auto lg:relative lg:inset-auto lg:z-auto' : 'hidden lg:flex'}
        w-full lg:w-80 xl:w-96 lg:border-l border-gray-200/60 flex-col shrink-0
      `}>

        {selectedItem && (
          <>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl md:text-2xl font-bold">{selectedItem.name}</h2>
              <div className="flex items-center gap-4">
                <button className="text-gray-400 hover:text-black text-xl hidden lg:block cursor-pointer">•••</button>
                <button onClick={() => setSelectedItem(null)} className="lg:hidden text-2xl font-bold text-gray-800 cursor-pointer">✕</button>
              </div>
            </div>

            <div className="w-full h-48 md:h-64 bg-[#f5f4f1] rounded-2xl md:rounded-3xl mb-6 flex items-center justify-center shadow-sm">
                <span className="text-6xl md:text-8xl">{selectedItem.emoji}</span>
            </div>

            <div className="flex flex-col gap-4 md:gap-6">
              <div>
                <p className="text-xs font-bold mb-1 text-gray-800">Category</p>
                <p className="text-sm text-gray-600">{activeCategory}</p>
              </div>

              <div>
                <p className="text-xs font-bold mb-2 text-gray-800">Color</p>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 md:w-5 md:h-5 rounded-full border border-gray-200" style={{ backgroundColor: selectedItem.colorHex }}></div>
                  <p className="text-sm text-gray-600">{selectedItem.color}</p>
                </div>
              </div>

              <div>
                <p className="text-xs font-bold mb-2 text-gray-800">Occasion</p>
                <div className="flex flex-wrap gap-2">
                  {selectedItem.occasions.map((occ, idx) => (
                    <span key={idx} className="px-2 py-1 md:px-3 rounded-full border border-gray-300 text-[10px] md:text-xs text-gray-600">{occ}</span>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {!selectedItem && (
          <div className="flex-1 flex items-center justify-center h-full">
            <p className="text-gray-400 font-medium text-sm text-center">Select an item<br />to view details</p>
          </div>
        )}

      </div>

    </div>
  );
};

export default DigitalCloset;