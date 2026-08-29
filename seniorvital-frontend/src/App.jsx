import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Home from './pages/Home.jsx'
import Habits from './pages/Habits.jsx'
import Video from './pages/Video.jsx'
import Progress from './pages/Progress.jsx'
import CaregiverView from './pages/CaregiverView.jsx'
import AdminDashboard from './pages/AdminDashboard.jsx'
import AuthOnboarding from './components/AuthOnboarding.jsx'
import SOSFloatingButton from './components/SOSFloatingButton.jsx'
import api from './api'

export default function App() {
  const [user, setUser] = useState(api.getCurrentUser())

  const handleAuthSuccess = (loggedUser) => {
    setUser(loggedUser)
  }

  const handleLogout = () => {
    api.logout()
    setUser(null)
    window.location.href = '/'
  }

  return (
    <div className="min-h-screen bg-surface font-sans antialiased text-primary selection:bg-secondary-container">
      {!user && <AuthOnboarding onAuthSuccess={handleAuthSuccess} />}

      {user && (
        <Router>
          {/* Floating Control Bar for User Profile and Logout */}
          <header aria-label="Barra de Estado del Usuario" className="fixed top-3 right-3 z-50 bg-surface/90 backdrop-blur-md px-3.5 py-1.5 border-2 border-outline-variant rounded-2xl flex items-center gap-3 shadow-soft-md select-none">
            <div className="w-7 h-7 rounded-lg bg-secondary-container text-secondary flex items-center justify-center font-bold text-xs">
              {(user.profile?.name?.[0] || user.email?.[0] || 'U').toUpperCase()}
            </div>
            <div className="flex flex-col text-left">
              <span className="text-xs font-extrabold text-primary truncate max-w-[110px]">
                {user?.profile?.name || user?.email?.split('@')?.[0] || 'Usuario'}
              </span>
              <span className="text-[10px] text-secondary font-bold uppercase tracking-wider">
                {user?.role || 'senior'}
              </span>
            </div>
            <button 
              onClick={handleLogout}
              className="p-1.5 hover:bg-error-container hover:text-on-error-container text-on-surface-variant rounded-xl transition-colors flex items-center justify-center"
              title="Cerrar Sesión"
              aria-label="Cerrar Sesión"
            >
              <span className="material-symbols-outlined text-lg">logout</span>
            </button>
          </header>

          <Routes>
            <Route path="/" element={<Home user={user} />} />
            <Route path="/habits" element={<Habits user={user} />} />
            <Route path="/video" element={<Video user={user} />} />
            <Route path="/progress" element={<Progress user={user} />} />
            <Route path="/caregiver" element={<CaregiverView user={user} />} />
            <Route path="/caregiver-dashboard" element={<CaregiverView user={user} />} />
            <Route path="/admin" element={<AdminDashboard user={user} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>

          {/* Botón SOS Permanente (Visible prioritariamente para rol Senior y general) */}
          {(user.role === 'senior' || !user.role) && (
            <SOSFloatingButton user={user} />
          )}
        </Router>
      )}
    </div>
  )
}
