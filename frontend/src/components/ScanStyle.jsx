import React from 'react'
import { useNavigate } from 'react-router-dom'

const ScanStyle = () => {
    const navigate = useNavigate();

    return (
        <div className='md:hidden bg-[#111317] rounded-[2rem] text-white py-12 px-6 mx-4 my-8 flex flex-col gap-3 items-center justify-center shadow-2xl'>
            <h2 className='text-2xl font-bold tracking-tight text-center'>
                Scan. Style. Slay.
            </h2>
            <p className='text-[15px] text-gray-300 mb-6'>It's that simple.</p>

            <button onClick={() => navigate('/closet')} className='w-full max-w-[280px] flex gap-2 items-center justify-center bg-gradient-to-r from-[#8E9CDE] to-[#E3A392] text-white font-medium px-6 py-4 rounded-full shadow-lg hover:opacity-90 transition-opacity cursor-pointer'>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0z" />
                </svg>
                <span className='text-[15px]'>Scan My Closet</span>
            </button>
        </div>
    )
}

export default ScanStyle
