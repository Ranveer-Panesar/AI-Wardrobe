import { useState } from 'react'

import Navbar from './components/Navbar.jsx'
import Hero from './components/Hero.jsx'
import HowItWorks from './components/HowItWorks.jsx'
import ScanStyle from './components/ScanStyle.jsx'
function App() {


  return (
    <>
      <Navbar />
      <div className="w-full bg-[#FAF9F6]">
        <Hero />
        <HowItWorks />
        <ScanStyle />
      </div>

    </>
  )
}

export default App
