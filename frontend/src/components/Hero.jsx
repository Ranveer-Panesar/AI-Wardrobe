import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const Hero = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    
    return (
        <div className='w-full px-6 md:px-20 py-2 flex flex-col md:flex-row items-center justify-between gap-16 md:bg-[url(/closet.jpg)] md:bg-cover md:bg-center md:bg-no-repeat  '>
            <div className='flex flex-col gap-3 items-start md:w-5/12'>
                <div className='font uppercase text-xs bg-white px-4 py-1.5 font-semibold rounded-full text-gray-700 border border-gray-200'>AI POWERED • SMART • PERSONAL</div>

                <h1 className='font-roboto text-3xl md:text-5xl  font-bold leading-tight text-gray-900'> Turn Your Closet Into Your <span className='text-indigo-400'>Personal</span> Stylist</h1>

                <p className='text-base text-gray-500 max-w-md leading-normal'>Take photos of your clothes, and Al creates
                    thousands of outfit combinations from your
                    actual wardrobe. Get perfect outfit ideas
                    for every occasion.
                </p>

                <div className='flex items-center justify-start gap-4 mt-2 sm:flex-row'>
                    <button onClick={() => navigate(user ? '/closet' : '/login')} className='bg-black text-white py-1.5 px-4 md:px-7 md:py-3.5 rounded-full text-sm font-medium flex items-center gap-2 whitespace-nowrap cursor-pointer hover:bg-gray-800 transition-colors'>
                        {user ? 'Open My Closet' : 'Create your Closet'}
                    </button>

                    <button onClick={() => navigate('/outfit')} className='bg-white text-black border border-gray-300 md:px-7 md:py-3.5 rounded-full text-sm font-medium flex items-center gap-2 px-4 py-1.5 whitespace-nowrap cursor-pointer hover:bg-gray-50 transition-colors'>
                        ✨ Find Outfits
                    </button>
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
                <img src="/hero.png" 
                alt="Ai Wardrobe"
                className='bg-contain rounded-b-2xl' />
            </div>
            
        </div>
    )
}

export default Hero
