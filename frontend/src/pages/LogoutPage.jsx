import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const LogoutPage = () => {
  const navigate = useNavigate();
  const { logout } = useAuth(); // Grab logout from our global context

  useEffect(() => {
    // Clear global auth state and localStorage
    logout();
  }, [logout]);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..700&family=Inter:wght@400;500;600&display=swap');
        
        .font-fraunces { font-family: 'Fraunces', serif; }
        .font-inter { font-family: 'Inter', sans-serif; }
        
        .bg-grain {
          background-image: radial-gradient(rgba(0,0,0,0.05) 1px, transparent 1px);
          background-size: 4px 4px;
        }
      `}</style>
      
      <div className="min-h-screen bg-[#faf6ef] text-[#1c1815] flex flex-col items-center justify-center p-6 font-inter selection:bg-[#7b2d3b] selection:text-[#faf6ef]">
        
        {/* Brand Top (Optional, makes it feel grounded) */}
        <div className="absolute top-8 left-8 flex items-center gap-3 cursor-pointer group" onClick={() => navigate('/')}>
            <div className="w-8 h-8 rounded-full bg-[#7b2d3b] flex items-center justify-center shadow-sm transition-colors">
              <span className="font-fraunces italic text-[#faf6ef] text-lg leading-none mt-1 pr-0.5">W</span>
            </div>
            <span className="font-fraunces font-medium text-[19px] tracking-tight text-[#1c1815]">AI Wardrobe</span>
        </div>

        {/* Center Card */}
        <div className="relative max-w-md w-full bg-[#f3ece0] border border-[#1c1815]/10 p-10 md:p-14 rounded-[28px] overflow-hidden text-center shadow-2xl shadow-[#1c1815]/5">
            
            {/* Grain & Tints */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(123,45,59,0.06),transparent_60%)] pointer-events-none"></div>
            <div className="absolute inset-0 bg-grain mix-blend-multiply opacity-50 pointer-events-none"></div>
            
            {/* Content */}
            <div className="relative z-10 flex flex-col items-center">
                <span className="uppercase text-[10px] tracking-widest text-[#1c1815]/50 font-semibold mb-4 block">
                    Session ended
                </span>
                
                <h1 className="font-fraunces text-4xl md:text-5xl text-[#1c1815] leading-[0.9] mb-4">
                    Signed <span className="italic text-[#7b2d3b]">out.</span>
                </h1>
                
                <p className="text-[14px] text-[#1c1815]/70 mb-10 max-w-[28ch] mx-auto leading-relaxed">
                    You have been securely signed out of your digital closet. We'll be here when you're ready to style again.
                </p>
                
                <button 
                  onClick={() => navigate('/login')}
                  className="w-full bg-[#7b2d3b] hover:bg-[#5e1f2b] text-[#faf6ef] text-[14px] font-medium py-3 rounded-full shadow-[0_4px_14px_rgba(123,45,59,0.15)] transition-all transform hover:-translate-y-0.5 mb-4"
                >
                  Sign in again
                </button>
                
                <button 
                  onClick={() => navigate('/')}
                  className="text-[13px] text-[#1c1815]/60 hover:text-[#7b2d3b] font-medium transition-colors"
                >
                  Return to homepage
                </button>
            </div>
        </div>
      </div>
    </>
  );
};

export default LogoutPage;
