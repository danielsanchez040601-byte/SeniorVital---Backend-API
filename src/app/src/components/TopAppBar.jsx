import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import NotificationModal from './NotificationModal'

export default function TopAppBar({ title, showBack = false, user = null }) {
  const navigate = useNavigate()
  const [showNotifications, setShowNotifications] = useState(false)

  return (
    <>
      <header className="sticky top-0 w-full z-40 bg-surface/95 backdrop-blur-md border-b-2 border-outline-variant flex justify-between items-center px-4 md:px-8 h-20 shrink-0 shadow-soft-sm">
        <div className="flex items-center gap-3 md:gap-4">
          {showBack ? (
            <button
              onClick={() => navigate(-1)}
              className="w-12 h-12 flex items-center justify-center rounded-2xl bg-surface-container hover:bg-surface-container-high border border-outline-variant text-primary transition-colors focus:ring-2 focus:ring-secondary"
              aria-label="Volver a la pantalla anterior"
            >
              <span className="material-symbols-outlined text-2xl md:text-3xl">arrow_back</span>
            </button>
          ) : (
            <div className="w-12 h-12 flex items-center justify-center rounded-2xl bg-secondary-container text-secondary border border-secondary/20 shadow-soft-sm">
              <span className="material-symbols-outlined text-2xl md:text-3xl font-bold">elderly</span>
            </div>
          )}

          <div>
            <span className="text-[11px] uppercase tracking-wider font-extrabold text-secondary block -mb-1">
              SeniorVital
            </span>
            <h1 className="font-extrabold text-headline-sm md:text-headline-md text-primary tracking-tight truncate max-w-[200px] sm:max-w-md">
              {title || 'Bienestar Activo'}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2 md:gap-3">
          {/* Botón de Notificaciones */}
          <button
            onClick={() => setShowNotifications(true)}
            className="relative w-12 h-12 flex items-center justify-center rounded-2xl bg-surface-container hover:bg-surface-container-high border border-outline-variant text-primary transition-all active:scale-95"
            aria-label="Abrir notificaciones"
            title="Buzón de Bienestar"
          >
            <span className="material-symbols-outlined text-2xl">notifications</span>
            <span className="absolute top-2 right-2 w-3 h-3 bg-secondary rounded-full border-2 border-surface animate-pulse" />
          </button>

          {/* Avatar del usuario */}
          {user && (
            <div 
              className="hidden sm:flex items-center gap-2 bg-surface-container px-3 py-1.5 rounded-2xl border border-outline-variant text-left"
              title={`Conectado como: ${user.email} (${user.role})`}
            >
              <div className="w-8 h-8 rounded-xl bg-primary text-on-primary flex items-center justify-center font-bold text-sm">
                {(user.profile?.name?.[0] || user.email?.[0] || 'U').toUpperCase()}
              </div>
              <div className="text-xs">
                <p className="font-bold text-primary truncate max-w-[100px]">
                  {user?.profile?.name || user?.email?.split('@')?.[0] || 'Usuario'}
                </p>
                <span className="text-[10px] text-tertiary font-bold uppercase tracking-wider">
                  {user?.role || 'senior'}
                </span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Modal de Notificaciones */}
      <NotificationModal 
        isOpen={showNotifications} 
        onClose={() => setShowNotifications(false)} 
      />
    </>
  )
}
