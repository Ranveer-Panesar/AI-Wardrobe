import { Routes, Route, useLocation } from 'react-router-dom';

import Navbar from './components/Navbar.jsx';
import Hero from './components/Hero.jsx';
import HowItWorks from './components/HowItWorks.jsx';
import ScanStyle from './components/ScanStyle.jsx';
import SeeTheMagic from './components/SeeTheMagic.jsx';
import DigitalCloset from './components/DigitalCloset.jsx';
import FindOutfit from './components/FindOutfit.jsx';
import AuthPage from './pages/AuthPage.jsx';
import LogoutPage from './pages/LogoutPage.jsx';

function LandingPage() {
  return (
    <div className="w-full bg-[#FAF9F6] pt-16">
      <Hero />
      <HowItWorks />
      <ScanStyle />
      <SeeTheMagic />
    </div>
  );
}

function App() {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/signup' || location.pathname === '/logout';

  return (
    <>
      {!isAuthPage && <Navbar />}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<AuthPage />} />
        <Route path="/signup" element={<AuthPage />} />
        <Route path="/logout" element={<LogoutPage />} />
        <Route path="/closet" element={<DigitalCloset />} />
        <Route path="/outfit" element={<FindOutfit />} />
        <Route path="/combinations" element={<FindOutfit />} />
      </Routes>
    </>
  );
}

export default App;
