import React from 'react';

const SeeTheMagic = () => {
    return (
        <div className="w-full px-6 py-16 md:py-24 max-w-6xl mx-auto">

            {/* Main Wrapper: Stack on mobile, side-by-side on desktop */}
            <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-16">

                {/* 1. HEADER BLOCK (Left side on desktop) */}
                <div className="w-full lg:w-1/3 flex flex-col text-center lg:text-left">
                    <h2 className="text-4xl md:text-5xl font-bold leading-tight mb-4 text-[#111317]">
                        See the Magic <br className="hidden lg:block" /> of Your Closet
                    </h2>
                    <p className="text-gray-500 text-base md:text-lg">
                        What looks like a few clothes can create thousands of stylish combinations.
                    </p>
                </div>

                {/* 2. VISUAL FLOW BLOCK (Right side on desktop) */}
                <div className=" hidden md:flex w-full lg:w-2/3 flex items-center justify-center">

                    <img
                        src="/MagicDesktop.png"
                        alt="AI Outfit Generation Flow"
                        className="w-full max-w-2xl object-contain drop-shadow-xl"
                    />

                </div>
                <div className="  md:hidden lg:hidden w-full lg:w-2/3 flex rounded-2xl items-center justify-center">

                    <img
                        src="/MagicMobile.png"
                        alt="AI Outfit Generation Flow"
                        className="w-full max-w-2xl rounded-2xl object-contain drop-shadow-xl"
                    />

                </div>

            </div>
        </div>
    );
};

export default SeeTheMagic;
