import React, { useState } from 'react'

const FindOutfit = () => {
    const [occasion, setOccasion] = useState('Casual')
    const [style, setStyle] = useState('Classic')
    const [season, setSeason] = useState('Summer')
    const [fit, setFit] = useState('Slim Fit')
    return (
        <div className='min-h-screen flex flex-row font-sans text-[#111317] pt-16 bg-[#FDFBF7]'>

            <div className='hidden md:flex flex-col gap-8 w-54 border-r border-gray-200/60 p-8 shrink-0'>

                <h1 className='text-sm font-bold tracking-widest uppercase'>AI Wardrobe</h1>

                <nav className='flex flex-col gap-1'>
                    {[
                        { icon: '🎯', label: 'Find Outfit', active: true },
                        { icon: '👕', label: 'My Closet' },
                        { icon: '✨', label: 'Outfits' },
                        { icon: '🤍', label: 'Favorites' },
                        { icon: '📖', label: 'Lookbook' },
                        { icon: '📅', label: 'Calendar' },
                        { icon: '👤', label: 'Style Profile' },
                        { icon: '⚙️', label: 'Settings' },
                    ].map((item) => (
                        <button key={item.label} className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-left w-full transition-colors cursor-pointer ${item.active ? 'bg-gray-100 text-black font-semibold' : 'text-gray-500 hover:bg-gray-50 hover:text-black'}`}>
                            <span>{item.icon}</span>
                            {item.label}
                        </button>
                    ))}
                </nav>



            </div>



            <div className='flex-1  p-6 md:p-10 overflow-y-auto'>

                <div className="mb-8">
                    <h2 className="text-2xl md:text-3xl font-bold mb-1">Find Your Perfect Outfit</h2>
                    <p className="text-sm text-gray-500">Tell us about the look you need and get AI curated outfits from your closet.</p>
                </div>
                {/* Progress Bar */}
                <div className="flex justify-center items-center gap-4 mb-10">
                    {['Occasion', 'Preferences', 'Results'].map((step, i) => (
                        <div key={step} className="flex items-center justify-center gap-2">
                            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold
        ${i === 0 ? 'bg-black text-white' : 'bg-gray-200 text-gray-400'}`}>
                                {i + 1}
                            </div>
                            <span className={`text-sm ${i === 0 ? 'font-semibold text-black' : 'text-gray-400'}`}>{step}</span>
                            {i < 2 && <div className="w-16 md:w-24 h-px bg-gray-200 ml-2"></div>}
                        </div>
                    ))}
                </div>

                    {/* first column */}
                <div className='w-full p-6 md:p-8 border border-gray-200 rounded-[24px] grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-12 bg-white shadow-sm'>
                    
                    {/* COLUMN 1: Occasion */}
                    <div className='flex flex-col'>
                        <h2 className='text-sm font-extrabold mb-5 flex items-center gap-2'>
                            <span className="w-5 h-5 rounded-full bg-black text-white flex items-center justify-center text-[10px]">1</span>
                            Select Occasion
                        </h2>
                        <div className='grid grid-cols-2 gap-3'>
                            {['Casual', 'Evening', 'Business', 'Wedding', 'Party', 'Other'].map((occ) => (
                                <button 
                                    key={occ} 
                                    onClick={() => setOccasion(occ)}
                                    className={`border p-4 rounded-2xl flex flex-col gap-2 items-center justify-center transition-all ${occasion === occ ? 'border-black bg-gray-50 shadow-sm scale-[1.02]' : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300'}`}>
                                    <span className='text-2xl'>{occ === 'Casual' ? '👕' : occ === 'Evening' ? '🍷' : occ === 'Business' ? '💼' : occ === 'Wedding' ? '💍' : occ === 'Party' ? '🎉' : '•••'}</span>
                                    <span className="text-xs font-semibold">{occ}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* COLUMN 2: Preferences */}
                    <div className="flex flex-col gap-8 lg:border-l border-gray-100 lg:pl-12">
                        
                        <div>
                            <h2 className='text-sm font-extrabold mb-4 flex items-center gap-2'>
                                <span className="w-5 h-5 rounded-full bg-black text-white flex items-center justify-center text-[10px]">2</span>
                                Core Style
                            </h2>
                            <div className="flex flex-wrap gap-2">
                                {['Classic', 'Streetwear', 'Minimalist', 'Vintage', 'Athleisure'].map(s => (
                                    <button
                                        key={s}
                                        onClick={() => setStyle(s)}
                                        className={`px-4 py-2 rounded-full text-xs font-semibold transition-all border ${style === s ? 'bg-black text-white border-black' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'}`}
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <h2 className='text-sm font-extrabold mb-4 flex items-center gap-2'>
                                <span className="w-5 h-5 rounded-full bg-black text-white flex items-center justify-center text-[10px]">3</span>
                                Season
                            </h2>
                            <div className="grid grid-cols-2 gap-2">
                                {['Spring 🌸', 'Summer ☀️', 'Autumn 🍂', 'Winter ❄️'].map(s => (
                                    <button
                                        key={s}
                                        onClick={() => setSeason(s.split(' ')[0])}
                                        className={`p-3 rounded-xl text-xs font-bold transition-all border flex items-center justify-center gap-2 ${season === s.split(' ')[0] ? 'bg-gray-100 border-gray-400 text-black' : 'bg-white border-gray-100 text-gray-500 hover:bg-gray-50'}`}
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <h2 className='text-sm font-extrabold mb-4 flex items-center gap-2'>
                                <span className="w-5 h-5 rounded-full bg-black text-white flex items-center justify-center text-[10px]">4</span>
                                Fit Preference
                            </h2>
                            <div className="flex bg-gray-100 p-1 rounded-xl">
                                {['Slim Fit', 'Regular', 'Oversized'].map(f => (
                                    <button
                                        key={f}
                                        onClick={() => setFit(f)}
                                        className={`flex-1 py-2 text-[11px] font-bold rounded-lg transition-all ${fit === f ? 'bg-white shadow-sm text-black' : 'text-gray-500 hover:text-gray-900'}`}
                                    >
                                        {f}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* ACTION SECTION */}
                    <div className="lg:col-span-2 mt-2 pt-8 border-t border-gray-100">
                        <div className="bg-[#EEF2F6] border border-[#D5E1F0] rounded-2xl p-5 mb-4 relative overflow-hidden flex items-center justify-between">
                            <div className="absolute top-0 right-0 w-24 h-24 bg-[#1877F2]/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>
                            <div>
                                <h3 className="font-extrabold text-[#111317] text-sm mb-1">AI Ready</h3>
                                <p className="text-xs text-[#111317]/60 font-medium">Scanning 42 items in your digital closet...</p>
                            </div>
                            <div className="w-10 h-10 rounded-full bg-white/50 flex items-center justify-center">
                                <span className="text-lg">✨</span>
                            </div>
                        </div>
                        
                        <button className="w-full bg-[#1877F2] hover:bg-[#1565C0] text-white font-bold py-4 rounded-2xl shadow-[0_8px_20px_rgba(24,119,242,0.25)] transition-all flex items-center justify-center gap-2 group active:scale-[0.98]">
                            <svg className="w-5 h-5 text-white/90 group-hover:animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                            </svg>
                            Generate Outfits
                        </button>
                    </div>
                </div>

                

                

            </div>


        </div>
    )
}

export default FindOutfit
