import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const Navbar = () => {
    const [menuOpen, setmenuOpen] = useState(false)
    const navigate = useNavigate()
    const { user } = useAuth(); // Read the global user state

    return (
        <div className='fixed top-0 left-0 right-0 flex justify-between items-center py-4 px-8 bg-white z-50 shadow-sm'>

            <div onClick={() => navigate('/')} className='text-xl font-bold flex gap-2 items-center cursor-pointer'>
                AI WARDROBE
            </div>

            <div className='hidden md:flex gap-6 text-sm font-medium text-gray-600 items-center '>
                <a href="#" className="hover:text-black transition-colors">Home</a>
                <a href="#" className="hover:text-black transition-colors">How it Works</a>
                <a href="#" className="hover:text-black transition-colors">Features</a>
                <a href="#" className="hover:text-black transition-colors">Styles</a>
                <a href="#" className="hover:text-black transition-colors">Pricing</a>
                <a href="#" className="hover:text-black transition-colors">About</a>
            </div>

            <div className='flex items-center gap-4'>
                {user ? (
                    <>
                        <div onClick={() => navigate('/closet')} className="hidden md:block text-sm font-semibold text-gray-600 hover:text-black cursor-pointer transition-colors">
                            My Closet
                        </div>
                        <div className="w-9 h-9 rounded-full bg-gray-200 border border-gray-300 overflow-hidden shrink-0 cursor-pointer hover:opacity-80 transition-opacity">
                            <img src={user.avatar} alt="Profile" className="w-full h-full object-cover" />
                        </div>
                        <div onClick={() => navigate('/logout')} className='hidden md:block bg-[#7b2d3b] text-[#faf6ef] px-5 py-2.5 rounded-full text-sm font-medium cursor-pointer hover:bg-[#5e1f2b] transition-colors'>
                            Log out
                        </div>
                    </>
                ) : (
                    <>
                        <div onClick={() => navigate('/login')} className="hidden md:block text-sm font-semibold text-gray-600 hover:text-black cursor-pointer transition-colors">
                            Log in
                        </div>
                        <div onClick={() => navigate('/login')} className='bg-black text-white px-5 py-2.5 rounded-full text-sm font-medium cursor-pointer hover:bg-gray-800 transition-colors'>
                            Get Started
                        </div>
                    </>
                )}

                {/* Mobile Hamburger Icon */}
                <button onClick={() => setmenuOpen(!menuOpen)} className='md:hidden p-2 text-gray-800 hover:bg-gray-100 rounded-md cursor-pointer'>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                    </svg>
                </button>
            </div>

            {/* Mobile Dropdown Menu */}
            {menuOpen && (
                <div className='md:hidden absolute top-full left-0 w-full bg-white shadow-md border-t border-gray-100 flex flex-col px-8 py-6 gap-5 z-50'>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">Home</a>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">How it Works</a>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">Features</a>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">Styles</a>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">Pricing</a>
                    <a href="#" className="text-gray-600 hover:text-black font-medium transition-colors">About</a>

                    <div className="flex flex-col gap-3 mt-2">
                        {user ? (
                            <>
                                <div className="flex items-center gap-3 px-2 py-2 mb-2 border-b border-gray-100">
                                    <div className="w-10 h-10 rounded-full bg-gray-200 border border-gray-300 overflow-hidden shrink-0">
                                        <img src={user.avatar} alt="Profile" className="w-full h-full object-cover" />
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-sm font-bold text-gray-900">{user.name || 'User'}</span>
                                        <span className="text-xs text-gray-500">{user.email || 'Member'}</span>
                                    </div>
                                </div>
                                <div onClick={() => { setmenuOpen(false); navigate('/closet'); }} className='w-full text-center text-sm font-semibold text-gray-700 hover:text-black cursor-pointer py-2.5 border border-gray-200 rounded-full transition-colors'>
                                    My Closet
                                </div>
                                <div onClick={() => { setmenuOpen(false); navigate('/logout'); }} className='w-full bg-[#7b2d3b] text-[#faf6ef] px-5 py-3 rounded-full text-sm text-center font-medium cursor-pointer hover:bg-[#5e1f2b] transition-colors'>
                                    Log out
                                </div>
                            </>
                        ) : (
                            <>
                                <div onClick={() => { setmenuOpen(false); navigate('/login'); }} className='w-full text-center text-sm font-semibold text-gray-700 hover:text-black cursor-pointer py-2.5 border border-gray-200 rounded-full transition-colors'>
                                    Log in
                                </div>
                                <div onClick={() => { setmenuOpen(false); navigate('/login'); }} className='w-full bg-black text-white px-5 py-3 rounded-full text-sm text-center font-medium cursor-pointer hover:bg-gray-800 transition-colors'>
                                    Get Started
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}

export default Navbar
