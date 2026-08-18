import React from 'react'

const HowItWorks = () => {
    return (
        <div className=' relative z-10 md:-mt-5 md:bg-neutral-950  text-black md:text-white rounded-3xl py-2 px-8 md:px-12 mx-6 md:mx-20 flex flex-col gap-2 items-center'>

            <h1 className='font-bold text-lg md:text-2xl flex items-start'>Your Closet. Endless Possiblities.</h1>

            <div className='grid grid-cols-1 md:grid-cols-4 gap-6 md:gap-4 w-full max-w-6xl mx-auto mt-6'>

                <div className='flex items-start text-left gap-3 bg-white md:bg-transparent sm:rounded-2xl md:rounded-none  px-2 py-3 md:items-center md:border-r md:border-dashed md:border-neutral-500'>
                    <div className='flex-shrink-0 w-10 h-10 md:w-12 md:h-12 rounded-2xl bg-neutral-800 flex items-center justify-center text-xl border border-gray-700'>
                        📷
                    </div>
                    <div className='flex flex-col items-start text-left'>
                        <p className='text-sm font-semibold'>1. Scan Your Closet</p>
                        <p className='text-xs text-gray-400 mt-1 leading-relaxed md:hidden lg:block'>
                            Take photos of your clothes, we'll identify each item.
                        </p>
                    </div>
                </div>

                <div className='flex items-start text-left gap-3 bg-white md:bg-transparent rounded-2xl md:rounded-none  px-2 py-3 md:items-center md:border-r md:border-dashed md:border-neutral-500'>
                    <div className='flex-shrink-0 w-10 h-10 md:w-12 md:h-12 rounded-2xl bg-neutral-800 flex items-center justify-center text-xl border border-gray-700'>
                        ✨
                    </div>
                    <div className='flex flex-col items-start text-left'>
                        <p className='text-sm font-semibold'>2. AI Creates Combos</p>
                        <p className='text-xs text-gray-400 mt-1 leading-relaxed md:hidden lg:block'>
                            Our AI generates thousands of stylish outfit combinations.
                        </p>
                    </div>
                </div>

                <div className='flex items-start text-left gap-3 bg-white md:bg-transparent rounded-2xl md:rounded-none  px-2 py-3 md:items-center md:border-r md:border-dashed md:border-neutral-500'>
                    <div className='flex-shrink-0 w-10 h-10 md:w-12 md:h-12 rounded-2xl bg-neutral-800 flex items-center justify-center text-xl border border-gray-700'>
                        📅
                    </div>
                    <div className='flex flex-col items-start text-left'>
                        <p className='text-sm font-semibold'>3. Choose the Occasion</p>
                        <p className='text-xs text-gray-400 mt-1 leading-relaxed md:hidden lg:block'>
                            Pick the event or mood you're dressing for.
                        </p>
                    </div>
                </div>

                <div className='flex items-start text-left gap-3 bg-white md:bg-transparent rounded-2xl md:rounded-none  px-2 py-3 md:items-center'>
                    <div className='flex-shrink-0 w-10 h-10 md:w-12 md:h-12 rounded-2xl bg-neutral-800 flex items-center justify-center text-xl border border-gray-700'>
                        ⭐
                    </div>
                    <div className='flex flex-col items-start text-left'>
                        <p className='text-sm font-semibold'>4. Get Your Best Outfit</p>
                        <p className='text-xs text-gray-400 mt-1 leading-relaxed md:hidden lg:block'>
                            Receive the perfect outfit recommendation for your occasion.
                        </p>
                    </div>
                </div>
            </div>

        </div>
    )
}

export default HowItWorks
