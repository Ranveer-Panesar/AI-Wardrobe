import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { login as apiLogin, signup as apiSignup } from '../api/auth';

const AuthPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  // --- Form & UI States ---
  const [email, setEmail]               = useState('');
  const [phone, setPhone]               = useState('');
  const [password, setPassword]         = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [keepSignedIn, setKeepSignedIn] = useState(true);

  // Sync mode with URL: /signup -> true, /login -> false
  const [isSignUp, setIsSignUp]         = useState(() => location.pathname === '/signup');
  const [isLoading, setIsLoading]       = useState(false);
  const [formError, setFormError]       = useState('');

  useEffect(() => {
    setIsSignUp(location.pathname === '/signup');
  }, [location.pathname]);

  // Format phone to E.164 (+CountryCodeNumber)
  const formatPhone = (raw) => {
    const digits = raw.replace(/\D/g, '');
    if (!digits) return raw;
    // If user didn't type +, prepend country code +91 for India (default)
    return raw.startsWith('+') ? raw : `+${digits}`;
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) return;
    setIsLoading(true);
    setFormError('');
    try {
      if (isSignUp) {
        const formattedPhone = formatPhone(phone);
        await apiSignup(email, formattedPhone, password);
        // Auto-login after successful signup
        const { access_token } = await apiLogin(email, password);
        login({ email, name: email.split('@')[0] }, access_token);
      } else {
        const { access_token } = await apiLogin(email, password);
        login({ email, name: email.split('@')[0] }, access_token);
      }
      navigate('/closet');
    } catch (err) {
      setFormError(err.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleAuth = () => {
    setFormError('Google sign-in is not yet connected to the backend.');
  };

  const toggleAuthMode = (e) => {
    if (e) e.preventDefault();
    const nextMode = !isSignUp;
    setIsSignUp(nextMode);
    navigate(nextMode ? '/signup' : '/login', { replace: true });
    setEmail('');
    setPhone('');
    setPassword('');
    setFormError('');
  };


  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..700&family=Inter:wght@400;500;600&display=swap');
        
        .font-fraunces { font-family: 'Fraunces', serif; }
        .font-inter { font-family: 'Inter', sans-serif; }
        
        .link-underline {
          background-image: linear-gradient(to right, #7b2d3b, #7b2d3b);
          background-size: 0% 1px;
          background-repeat: no-repeat;
          background-position: left bottom;
          transition: background-size 0.3s ease;
          padding-bottom: 2px;
        }
        .link-underline:hover { background-size: 100% 1px; }
        
        .bg-grain {
          background-image: radial-gradient(rgba(0,0,0,0.05) 1px, transparent 1px);
          background-size: 4px 4px;
        }
      `}</style>

      <div className="min-h-screen bg-[#faf6ef] text-[#1c1815] font-inter selection:bg-[#7b2d3b] selection:text-[#faf6ef]">
        
        {/* Sticky Nav */}
        <nav className="sticky top-0 z-50 h-[68px] bg-[#faf6ef]/85 backdrop-blur-md border-b border-[#1c1815]/10 flex items-center justify-center px-6 sm:px-8">
          <div className="max-w-[1240px] w-full flex justify-between items-center">
            
            {/* Brand Lockup */}
            <div onClick={() => navigate('/')} className="flex items-center gap-3 cursor-pointer group">
              
              <span className="font-fraunces font-medium text-[19px] tracking-tight text-[#1c1815]">AI Wardrobe</span>
            </div>

            {/* Center Links (Hidden on small screens) */}
            <div className="hidden md:flex items-center gap-8 text-[14px] text-[#1c1815]/70 font-medium">
              <button onClick={() => navigate('/closet')} className="link-underline hover:text-[#1c1815] transition-colors cursor-pointer">My Closet</button>
              <button onClick={() => navigate('/outfit')} className="link-underline hover:text-[#1c1815] transition-colors cursor-pointer">Lookbook</button>
              <button className="link-underline hover:text-[#1c1815] transition-colors cursor-pointer">Pricing</button>
              <button className="link-underline hover:text-[#1c1815] transition-colors cursor-pointer">Style Guide</button>
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-4">
              <span className="hidden sm:block text-[14px] text-[#1c1815]/60 font-medium">
                {isSignUp ? 'Already a member?' : 'New here?'}
              </span>
              <button 
                onClick={toggleAuthMode}
                className="px-4 py-1.5 rounded-full border border-[#7b2d3b]/30 text-[#7b2d3b] text-[14px] font-medium hover:border-[#7b2d3b] hover:bg-[#7b2d3b]/5 transition-all cursor-pointer"
              >
                {isSignUp ? 'Sign in' : 'Create account'}
              </button>
            </div>
          </div>
        </nav>

        {/* Main Split Layout */}
        <main className="min-h-[calc(100vh-68px)] w-full flex items-center justify-center px-6 sm:px-8 py-8 md:py-12">
          
          <div className="max-w-[1240px] w-full grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] border border-[#1c1815]/10 rounded-[24px] lg:rounded-l-[28px] lg:rounded-r-[28px] overflow-hidden shadow-2xl shadow-[#1c1815]/5">
            
            {/* LEFT COLUMN: Editorial Panel */}
            <div className="order-2 lg:order-1 relative bg-[#f3ece0] p-8 sm:p-12 xl:p-16 flex flex-col justify-between border-t lg:border-t-0 lg:border-r border-[#1c1815]/10 min-h-[500px]">
              
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(123,45,59,0.06),transparent_50%),radial-gradient(circle_at_bottom_right,rgba(123,45,59,0.04),transparent_50%)] pointer-events-none"></div>
              <div className="absolute inset-0 bg-grain mix-blend-multiply opacity-50 pointer-events-none"></div>

              <div className="relative z-10 flex flex-col h-full justify-between gap-12 lg:gap-0">
                
                <div className="flex items-center gap-4 mt-2">
                  <div className="w-8 h-[1px] bg-[#7b2d3b]"></div>
                  <span className="uppercase text-[11px] font-semibold tracking-[0.22em] text-[#7b2d3b]">
                    The Digital Closet
                  </span>
                </div>

                <div className="max-w-[30ch] transition-opacity duration-300">
                  <span className="block uppercase text-[10px] font-semibold tracking-widest text-[#1c1815]/50 mb-4">
                    Autumn Collection · 2026
                  </span>
                  <h1 className="font-fraunces text-[clamp(2.6rem,6.2vw,4.6rem)] leading-[0.96] tracking-[-0.02em] font-light text-[#1c1815] mb-6">
                    Welcome <br />
                    {isSignUp ? (
                      <span className="italic text-[#7b2d3b] pr-2">aboard.</span>
                    ) : (
                      <span className="italic text-[#7b2d3b] pr-2">back.</span>
                    )}
                  </h1>
                  <p className="font-fraunces text-[clamp(1.15rem,2vw,1.45rem)] text-[#1c1815]/70 leading-relaxed max-w-[24ch]">
                    {isSignUp 
                      ? 'Create an account to build your digital wardrobe and discover your personal style.' 
                      : 'Sign in to access your digital wardrobe and continue curating your personal style.'}
                  </p>
                </div>

                <figure className="relative pt-8">
                  <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-[#1c1815]/15 to-transparent"></div>
                  
                  <span 
                    className="absolute -top-4 -left-3 text-7xl font-fraunces text-[#7b2d3b] opacity-90 select-none"
                    style={{ fontFeatureSettings: "'ss01' 1" }}
                  >
                    “
                  </span>
                  
                  <blockquote className="relative z-10 font-fraunces text-[clamp(1.05rem,1.5vw,1.15rem)] leading-[1.6] text-[#1c1815]/80 pl-6 mb-6">
                    Fashion fades, only style remains the same. Our AI ensures your personal style is always effortless and elevated.
                  </blockquote>
                  
                  <figcaption className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-[#7b2d3b]/15 flex items-center justify-center border border-[#7b2d3b]/20">
                      <span className="font-fraunces italic text-[#7b2d3b] text-lg pr-0.5 mt-0.5">E</span>
                    </div>
                    <div>
                      <span className="block text-[13px] font-semibold text-[#1c1815]">Elena Rostova</span>
                      <span className="block text-[12px] text-[#1c1815]/60">Lead Stylist, AI Wardrobe</span>
                    </div>
                  </figcaption>
                </figure>
                
              </div>
            </div>

            {/* RIGHT COLUMN: Auth Form */}
            <div className="order-1 lg:order-2 bg-[#faf6ef] p-8 sm:p-12 xl:p-16 flex items-center justify-center">
              <div className="w-full max-w-[400px]">
                
                {/* Form Header */}
                <div className="flex justify-between items-start mb-8">
                  <div>
                    <span className="uppercase text-[10px] tracking-[0.15em] text-[#1c1815]/50 font-semibold block mb-2">
                      {isSignUp ? 'New account' : 'Member sign in'}
                    </span>
                    <h2 className="font-fraunces text-[2rem] leading-none text-[#1c1815] transition-all">
                      {isSignUp ? 'Sign up' : 'Sign in'}
                    </h2>
                  </div>
                  <span className="font-fraunces text-[2.4rem] leading-none text-[#7b2d3b]/25 tabular-nums select-none transition-all">
                    {isSignUp ? '02' : '01'}
                  </span>
                </div>

                {/* Google SSO Button */}
                <button 
                  type="button" 
                  onClick={handleGoogleAuth}
                  disabled={isLoading}
                  className="w-full flex items-center justify-center gap-3 bg-white/60 hover:bg-white border border-[#1c1815]/15 rounded-[12px] py-3 transition-colors mb-6 shadow-sm disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                  </svg>
                  <span className="text-[14px] font-medium text-[#1c1815]">Continue with Google</span>
                </button>

                <div className="flex items-center gap-4 mb-6">
                  <div className="flex-1 h-[1px] bg-[#1c1815]/10"></div>
                  <span className="uppercase text-[10px] tracking-widest text-[#1c1815]/40 font-semibold">
                    Or with email
                  </span>
                  <div className="flex-1 h-[1px] bg-[#1c1815]/10"></div>
                </div>

                {/* Main Form */}
                <form className="space-y-5" onSubmit={handleAuthSubmit}>
                  
                  {/* Email Field */}
                  <div className="space-y-1.5">
                    <label className="block text-[13px] font-medium text-[#1c1815]">Email address</label>
                    <input 
                      type="email" 
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      required
                      className="w-full bg-white/60 border border-[#1c1815]/15 rounded-[12px] px-4 py-3 text-[14px] text-[#1c1815] placeholder:text-[#1c1815]/30 focus:outline-none focus:bg-[#fffdf9] focus:border-[#7b2d3b] focus:ring-4 focus:ring-[#7b2d3b]/10 transition-all"
                    />
                  </div>

                  {/* Phone Field — signup only */}
                  {isSignUp && (
                    <div className="space-y-1.5">
                      <label className="block text-[13px] font-medium text-[#1c1815]">Phone number</label>
                      <input 
                        type="tel"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="+919876543210"
                        required
                        className="w-full bg-white/60 border border-[#1c1815]/15 rounded-[12px] px-4 py-3 text-[14px] text-[#1c1815] placeholder:text-[#1c1815]/30 focus:outline-none focus:bg-[#fffdf9] focus:border-[#7b2d3b] focus:ring-4 focus:ring-[#7b2d3b]/10 transition-all"
                      />
                      <p className="text-[11px] text-[#1c1815]/40">Include country code, e.g. +91 for India</p>
                    </div>
                  )}

                  {/* Password Field */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between items-center">
                      <label className="block text-[13px] font-medium text-[#1c1815]">Password</label>
                      {!isSignUp && (
                        <a href="#" className="text-[12px] text-[#7b2d3b] hover:text-[#5e1f2b] font-medium link-underline pb-0.5">Forgot?</a>
                      )}
                    </div>
                    <div className="relative">
                      <input 
                        type={showPassword ? "text" : "password"} 
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        className="w-full bg-white/60 border border-[#1c1815]/15 rounded-[12px] pl-4 pr-11 py-3 text-[14px] text-[#1c1815] placeholder:text-[#1c1815]/30 focus:outline-none focus:bg-[#fffdf9] focus:border-[#7b2d3b] focus:ring-4 focus:ring-[#7b2d3b]/10 transition-all"
                      />
                      <button 
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-[#1c1815]/40 hover:text-[#1c1815]/70 transition-colors p-1 cursor-pointer"
                        tabIndex="-1"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                          {showPassword ? (
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                          ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          )}
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Password hint for signup */}
                  {isSignUp && (
                    <p className="text-[11px] text-[#1c1815]/40 -mt-2 px-1">
                      Must be 8+ chars with at least one uppercase letter, digit, and special character (!@#$%^&*…)
                    </p>
                  )}

                  {/* Keep Signed In Checkbox */}

                  <label className="flex items-center gap-3 cursor-pointer group mt-2 w-max">
                    <div className={`relative flex items-center justify-center w-[18px] h-[18px] rounded-[5px] transition-colors ${keepSignedIn ? 'bg-[#7b2d3b] border border-[#7b2d3b]' : 'bg-white/60 border border-[#1c1815]/20 group-hover:border-[#7b2d3b]/50'}`}>
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={keepSignedIn}
                        onChange={() => setKeepSignedIn(!keepSignedIn)}
                      />
                      <svg 
                        className={`w-3.5 h-3.5 text-[#faf6ef] transition-opacity duration-200 ${keepSignedIn ? 'opacity-100' : 'opacity-0'}`} 
                        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className="text-[14px] text-[#1c1815]/80 select-none">Keep me signed in for 30 days</span>
                  </label>

                  {/* Error Banner */}
                  {formError && (
                    <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-[10px] px-3 py-2.5">
                      <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3m0 3h.01M12 3a9 9 0 100 18A9 9 0 0012 3z" />
                      </svg>
                      <p className="text-[12px] text-red-600 font-medium">{formError}</p>
                    </div>
                  )}

                  {/* Primary Submit Button */}
                  <button 
                    type="submit" 
                    disabled={isLoading}
                    className="w-full bg-[#7b2d3b] hover:bg-[#5e1f2b] disabled:opacity-75 disabled:hover:bg-[#7b2d3b] text-[#faf6ef] text-[15px] font-medium py-3.5 rounded-[12px] shadow-[0_4px_14px_rgba(123,45,59,0.2)] hover:shadow-[0_6px_20px_rgba(94,31,43,0.3)] transition-all transform hover:-translate-y-0.5 disabled:transform-none mt-2 flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {isLoading ? (
                      <>
                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </>
                    ) : (
                      isSignUp ? 'Create your closet' : 'Sign in to your closet'
                    )}
                  </button>

                </form>

                {/* Footer Copy */}
                <div className="mt-8 text-center space-y-4">
                  <p className="text-[14px] text-[#1c1815]/70">
                    {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
                    <a href="#" onClick={toggleAuthMode} className="text-[#7b2d3b] font-medium link-underline pb-0.5 cursor-pointer">
                      {isSignUp ? 'Sign in here' : 'Start styling free'}
                    </a>
                  </p>
                  <p className="text-[11.5px] text-[#1c1815]/40 leading-relaxed">
                    By proceeding, you agree to our <a href="#" className="hover:text-[#1c1815]/70 underline decoration-[#1c1815]/20 underline-offset-2">Terms of Service</a> and <a href="#" className="hover:text-[#1c1815]/70 underline decoration-[#1c1815]/20 underline-offset-2">Privacy Policy</a>.
                  </p>
                </div>

              </div>
            </div>

          </div>
        </main>
        
      </div>
    </>
  );
};

export default AuthPage;
