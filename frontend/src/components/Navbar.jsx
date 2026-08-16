import React, { useState } from 'react'

const Navbar = () => {
    const [menuOpen, setmenuOpen] = useState(false)
    return (
        <div className='relative flex  justify-between  items-center py-4 px-8'>

            <div className='text-xl font-bold flex gap-2 items-center'>AI WARDROBE</div>

            <div className=' hidden md:flex gap-6 text-sm font-medium text-gray-600 items-center '>

                <a href="#" className="hover:text-black transition-colors">Home</a>
                <a href="#" className="hover:text-black transition-colors">How it Works</a>
                <a href="#" className="hover:text-black transition-colors">Features</a>
                <a href="#" className="hover:text-black transition-colors">Styles</a>
                <a href="#" className="hover:text-black transition-colors">Pricing</a>
                <a href="#" className="hover:text-black transition-colors">About</a>

            </div>

            <div className='flex items-center gap-4'>
                <div className='hidden md:block bg-black text-white px-5 py-2.5 rounded-full text-sm cursor-pointer hover:bg-gray-800 transition-colors'>
                    Get Started
                </div>

                {/* Mobile Hamburger Icon */}
                <button onClick={() => setmenuOpen(!menuOpen)} className='md:hidden p-2 text-gray-800 hover:bg-gray-100 rounded-md'>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                    </svg>
                </button>
            </div>
            {/* Mobile Dropdown Menu - Only renders if isMenuOpen is true */}
            {menuOpen && (
                <div className='md:hidden absolute top-full left-0 w-full bg-white shadow-md border-t border-gray-100 flex flex-col px-8 py-6 gap-5'>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">Home</a>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">How it Works</a>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">Features</a>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">Styles</a>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">Pricing</a>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">About</a>

                    <div className='bg-black text-white px-5 py-3 rounded-full text-sm text-center font-medium cursor-pointer mt-2 hover:bg-gray-800 transition-colors'>
                        Get Started
                    </div>
                </div>
            )}
        </div>


    )
}

export default Navbar
