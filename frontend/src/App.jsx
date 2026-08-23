import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'

import Navbar from './components/Navbar.jsx'
import Hero from './components/Hero.jsx'
import HowItWorks from './components/HowItWorks.jsx'
import ScanStyle from './components/ScanStyle.jsx'
import SeeTheMagic from './components/SeeTheMagic.jsx'
import DigitalCloset from './components/DigitalCloset.jsx'

function LandingPage() {
  return (
    <div className="w-full bg-[#FAF9F6]">
      <Hero />
      <HowItWorks />
      <ScanStyle />
      <SeeTheMagic />
    </div>
  )
}

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/closet" element={<DigitalCloset />} />
      </Routes>
    </>
  )
}

export default App
