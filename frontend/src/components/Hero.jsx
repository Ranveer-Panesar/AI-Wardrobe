import React from 'react'


const Hero = () => {
    return (
        <div className='w-full px-20 py-5 flex flex-col md:flex-row items-center justify-between gap-16 md:bg-[url(/closet.jpg)] md:bg-cover md:bg-center md:bg-no-repeat  '>
            <div className='flex flex-col gap-6 items-start md:w-5/12'>
                <div className=' uppercase text-xs bg-white px-4 py-1.5 font-semibold rounded-full text-gray-700 border border-gray-200'>AI POWERED • SMART • PERSONAL</div>

                <h1 className='text-3xl md:text-5xl  font-bold leading-tight text-gray-900'> Turn Your Closet Into Your <span className='text-indigo-400'>Personal</span> Stylist</h1>

                <p className='text-base text-gray-500 max-w-md leading-relaxed'>Take photos of your clothes, and Al creates
                    thousands of outfit combinations from your
                    actual wardrobe. Get perfect outfit ideas
                    for every occasion.
                </p>

                <div className='flex  gap-4 mt-2 sm:flex-row'>
                    <button className='bg-black text-white py-1.5  px-3  md:px-7 md:py-3.5 rounded-full text-sm font-medium flex items-center gap-2 whitespace-nowrap'>Scan My Closet</button>

                    <button className='bg-white text-black border border-gray-300 md:px-7 md:py-3.5 rounded-full text-sm font-medium flex items-center gap-2  px-3 py-1.5 whitespace-nowrap'>Watch Demo</button>
                </div>

                <div className='flex items-center gap-3 mt-2'>
                    <div className='flex'>
                        <div className='w-8 h-8 rounded-full bg-gray-300 border-2 border-white -ml-2 first:ml-0 overflow-hidden'></div>
                        <div className='w-8 h-8 rounded-full bg-gray-300 border-2 border-white -ml-2 first:ml-0 overflow-hidden'></div>
                        <div className='w-8 h-8 rounded-full bg-gray-300 border-2 border-white -ml-2 first:ml-0 overflow-hidden'></div>
                        <div className='w-8 h-8 rounded-full bg-gray-300 border-2 border-white -ml-2 first:ml-0 overflow-hidden'></div>
                    </div>
                    <pre className='text-xs text-gray-500'>Join 10,000+ 
                        <br />users who style smarter</pre>
                    
                </div>

            </div>



            <div className='hidden md:flex md:w-7/12 relative h-full min-h-[500px]'>
                <img src="/mobile.png" 
                    alt="AI Wardrobe App"
                    className='absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] object-contain drop-shadow-2xl' />
            </div>
            
            <div className='md:hidden flex rounded-full'>
                <img src="/hero.png" alt="Ai Wardrobe"
                className='bg-contain rounded-b-2xl' />
            </div>
        </div>
    )
}

export default Hero
