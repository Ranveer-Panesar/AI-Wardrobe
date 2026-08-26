import React, { useState } from 'react'

const FindOutfit = () => {
    const [occasion, setOccasion] = useState('Casual')
    const [style, setStyle] = useState('Classic')
    const [season, setSeason] = useState('Summer')
    const [fit, setFit] = useState('Slim Fit')
    const [tags, setTags] = useState(['No Hoodie', 'No Cap', 'No Sneakers', 'Light Colors'])
    return (
        <div className='min-h-screen flex flex-row font-sans text-[#111317] pt-16 bg-[#FDFBF7]'>

            <div className='hidden md:flex gap-3 w-54 border-r border-gray-200/60 p-8 justify-between shrink-0 flex-col'>

                <h1 className='text-sm font-bold tracking-widest uppercase mb-10'>AI Wardrobe</h1>

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

                {/* Upgrade Card */}
                <div className="bg-[#F5F4F1] rounded-2xl p-5">
                    <p className="text-xs font-bold mb-1">👑 Upgrade to Pro</p>
                    <p className="text-xs text-gray-500 mb-4">Unlock unlimited outfits, advanced filters and AI style insights.</p>
                    <button className="w-full bg-black text-white text-xs font-semibold py-3 rounded-full cursor-pointer">
                        Upgrade Now
                    </button>
                </div>

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

                <div className='w-full p-6 border border-gray-200 rounded-2xl grid grid-cols-3'>
                    {/* COLUMN 1: Occasion */}
                    <div className='flex flex-col'>
                        <h2 className='text-sm font-bold mb-4'>1. Select Occasion</h2>
                        <div className='grid grid-cols-3 gap-3'>
                            {['Casual', 'Evening', 'Business', 'Wedding', 'Party', 'Other'].map((occ) => (
                                <button 
                                    key={occ} 
                                    onClick={() => setOccasion(occ)}
                                    className={`border p-4 rounded-2xl flex flex-col gap-3 items-center justify-center transition-all ${occasion === occ ? 'border-black bg-white shadow-md scale-105' : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-gray-400'}`}>
                                    <span className='mb-2 text-xl'>{occ === 'Casual' ? '👕' : occ === 'Evening' ? '🍷' : occ === 'Business' ? '💼' : occ === 'Wedding' ? '💍' : occ === 'Party' ? '🎉' : '•••'}</span>
                                    {occ}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

            </div>


        </div>
    )
}

export default FindOutfit
