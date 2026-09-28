import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'

import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar.jsx'
import Hero from './components/Hero.jsx'
import HowItWorks from './components/HowItWorks.jsx'
import ScanStyle from './components/ScanStyle.jsx'
import SeeTheMagic from './components/SeeTheMagic.jsx'
import DigitalCloset from './components/DigitalCloset.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'

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
    <AuthProvider>
      <Navbar />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/closet"
          element={
            <ProtectedRoute>
              <DigitalCloset />
            </ProtectedRoute>
          }
        />
      </Routes>
    </AuthProvider>
  )
}

export default App
