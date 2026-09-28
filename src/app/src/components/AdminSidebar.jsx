import React from 'react'
import { Link, useLocation } from 'react-router-dom'

export default function AdminSidebar() {
  const location = useLocation()
  
  return (
    <aside className="hidden md:flex flex-col w-64 bg-surface-container-low border-r-2 border-outline-variant fixed h-full z-40">
      <div className="p-margin-desktop pt-8 pb-8 border-b border-outline-variant/30">
        <div className="font-headline-lg text-headline-lg text-secondary mb-2 select-none">SeniorVital</div>
        <div className="font-label-sm text-label-sm text-on-surface-variant font-bold">Panel de Administrador</div>
      </div>
      
      <nav className="flex-1 overflow-y-auto py-stack-md px-4 flex flex-col gap-2">
        <Link 
          to="/admin" 
          className={`flex items-center gap-4 px-4 py-3 rounded-xl font-semibold transition-all ${
            location.pathname === '/admin' 
              ? 'bg-secondary-container text-on-secondary-container' 
              : 'text-on-surface-variant hover:bg-surface-container-high'
          }`}
        >
          <span className="material-symbols-outlined">dashboard</span>
          <span className="font-label-lg text-label-lg">Panel Clínico</span>
        </Link>
        
        <Link 
          to="/" 
          className="flex items-center gap-4 px-4 py-3 rounded-xl text-on-surface-variant hover:bg-surface-container-high font-semibold transition-all"
        >
          <span className="material-symbols-outlined">phone_iphone</span>
          <span className="font-label-lg text-label-lg">Vista Móvil (Demo)</span>
        </Link>
      </nav>
      
      <div className="p-4 border-t border-outline-variant/30">
        <Link 
          to="/" 
          className="flex items-center gap-4 px-4 py-3 w-full rounded-xl text-on-surface-variant hover:bg-surface-container-high transition-all text-left font-semibold"
        >
          <span className="material-symbols-outlined">logout</span>
          <span className="font-label-lg text-label-lg">Cerrar Sesión</span>
        </Link>
      </div>
    </aside>
  )
}
