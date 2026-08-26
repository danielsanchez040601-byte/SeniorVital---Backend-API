import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import api from '../api'

export default function BottomNavBar() {
  const location = useLocation()
  const user = api.getCurrentUser()
  const role = user?.role || 'senior'

  // Items según rol
  let navItems = []

  if (role === 'caregiver' || role === 'familiar') {
    navItems = [
      { path: '/caregiver', icon: 'visibility', label: 'Supervisión' },
      { path: '/progress', icon: 'insights', label: 'Progreso' },
      { path: '/habits', icon: 'water_drop', label: 'Hábitos' },
    ]
  } else if (role === 'admin' || role === 'physio') {
    navItems = [
      { path: '/admin', icon: 'clinical_notes', label: 'Pacientes' },
      { path: '/progress', icon: 'insights', label: 'Analítica' },
      { path: '/video', icon: 'fitness_center', label: 'Ejercicios' },
    ]
  } else {
    // Senior (Default)
    navItems = [
      { path: '/', icon: 'home', label: 'Inicio' },
      { path: '/habits', icon: 'water_drop', label: 'Hábitos' },
      { path: '/video', icon: 'play_circle', label: 'Rutina' },
      { path: '/progress', icon: 'insights', label: 'Progreso' }
    ]
  }

  return (
    <nav 
      className="fixed bottom-0 w-full z-40 bg-surface/95 backdrop-blur-md border-t-2 border-outline-variant flex justify-around items-center px-3 py-2 pb-safe shadow-soft-xl"
      aria-label="Navegación principal inferior"
    >
      {navItems.map((item) => {
        const isActive = location.pathname === item.path
        return (
          <Link 
            key={item.path} 
            to={item.path} 
            className={`flex flex-col items-center justify-center py-2 px-3 rounded-2xl min-w-[70px] min-h-[60px] transition-all duration-200 active:scale-95 ${
              isActive 
                ? 'bg-secondary-container text-on-secondary-container font-extrabold shadow-soft-sm border border-secondary/20' 
                : 'text-on-surface-variant hover:bg-surface-container'
            }`}
            aria-current={isActive ? 'page' : undefined}
          >
            <span 
              className={`material-symbols-outlined text-2xl md:text-3xl mb-0.5 ${isActive ? 'fill' : ''}`}
            >
              {item.icon}
            </span>
            <span className="text-xs md:text-sm font-semibold tracking-tight leading-tight">
              {item.label}
            </span>
          </Link>
        )
      })}
    </nav>
  )
}
