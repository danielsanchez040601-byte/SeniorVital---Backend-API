import React, { useState, useEffect } from 'react'
import TopAppBar from '../components/TopAppBar'
import BottomNavBar from '../components/BottomNavBar'
import api from '../api'

const DEFAULT_SESSIONS = [
  {
    id: "1",
    title: "Movilidad Matutina en Silla",
    description: "Activación de 10 minutos para hombros, columna y caderas sin impacto.",
    duration: "10 min",
    level: "Nivel 1 (Sentado)",
    icon: "chair"
  },
  {
    id: "2",
    title: "Equilibrio y Apoyo en Pared",
    description: "Fortalecimiento de tobillos y estabilidad de marcha asistida.",
    duration: "12 min",
    level: "Nivel 2 (Asistido)",
    icon: "assist_walker"
  },
  {
    id: "3",
    title: "Respiración y Relajación Guiada",
    description: "Técnicas de calma diafragmática para reducir tensión y mejorar descanso.",
    duration: "8 min",
    level: "Todos los Niveles",
    icon: "spa"
  },
  {
    id: "4",
    title: "Fortalecimiento Suave de Piernas",
    description: "Sentadilla guiada con silla y elevación de puntas de pies.",
    duration: "15 min",
    level: "Nivel 2-3",
    icon: "fitness_center"
  }
]

export default function Video() {
  const user = api.getCurrentUser()
  const [sessions, setSessions] = useState(DEFAULT_SESSIONS)
  const [activeSession, setActiveSession] = useState(DEFAULT_SESSIONS[0])
  const [isPlaying, setIsPlaying] = useState(false)
  const [completed, setCompleted] = useState(false)

  const handlePlayToggle = () => {
    setIsPlaying(!isPlaying)
  }

  const handleFinish = () => {
    setIsPlaying(false)
    setCompleted(true)
    setTimeout(() => setCompleted(false), 3000)
  }

  return (
    <div className="min-h-screen bg-surface pb-32 text-left selection:bg-secondary-container">
      <TopAppBar title="Sesión Guiada" user={user} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        
        {/* Reproductor de Video Accesible */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-lg">
          <div className="relative aspect-video w-full rounded-2xl bg-primary-container overflow-hidden flex flex-col items-center justify-center text-white border-2 border-outline-variant/40 shadow-inner">
            <div className="text-center p-6 z-10">
              <div className="w-16 h-16 rounded-full bg-surface/20 backdrop-blur-md flex items-center justify-center mx-auto mb-3 text-secondary">
                <span className="material-symbols-outlined text-4xl">
                  {isPlaying ? 'pause' : 'play_arrow'}
                </span>
              </div>
              <h2 className="text-headline-sm sm:text-headline-md font-extrabold text-white">
                {activeSession.title}
              </h2>
              <p className="text-body-sm text-white/80 mt-1 max-w-md mx-auto">
                {activeSession.description}
              </p>
            </div>

            {isPlaying && (
              <div className="absolute inset-0 bg-primary/40 backdrop-blur-xs flex items-end p-4">
                <div className="w-full bg-white/20 h-3 rounded-full overflow-hidden">
                  <div className="bg-secondary h-full w-2/3 animate-pulse rounded-full" />
                </div>
              </div>
            )}
          </div>

          {/* Controles de Reproducción Masivos */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6 pt-4 border-t border-outline-variant">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-secondary-container text-on-secondary-container rounded-full text-xs font-bold uppercase border border-secondary/20">
                {activeSession.level}
              </span>
              <span className="text-xs text-on-surface-variant font-bold">
                ⏱ {activeSession.duration}
              </span>
            </div>

            <div className="flex gap-3 w-full sm:w-auto">
              <button
                onClick={handlePlayToggle}
                className="flex-1 sm:flex-none min-h-[56px] px-8 rounded-2xl bg-secondary hover:bg-red-700 text-on-secondary font-bold text-lg flex items-center justify-center gap-2 shadow-soft-sm active:scale-95 transition-all"
              >
                <span className="material-symbols-outlined text-2xl">
                  {isPlaying ? 'pause' : 'play_arrow'}
                </span>
                <span>{isPlaying ? 'Pausar' : 'Comenzar Video'}</span>
              </button>

              <button
                onClick={handleFinish}
                className="min-h-[56px] px-6 rounded-2xl bg-tertiary hover:bg-sage-dark text-on-tertiary font-bold text-base flex items-center justify-center gap-2 shadow-soft-sm active:scale-95 transition-all"
              >
                <span className="material-symbols-outlined text-2xl">check_circle</span>
                <span className="hidden sm:inline">Completar</span>
              </button>
            </div>
          </div>

          {completed && (
            <div className="mt-4 p-4 rounded-2xl bg-sage-light text-sage-dark border border-sage/30 text-sm font-bold flex items-center gap-2 animate-fade-in">
              <span className="material-symbols-outlined text-2xl">celebration</span>
              <span>¡Excelente trabajo! Has sumado una sesión a tu progreso de hoy.</span>
            </div>
          )}
        </section>

        {/* Lista de Sesiones Disponibles */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-sm">
          <h3 className="text-headline-sm font-bold text-primary mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary">video_library</span>
            <span>Otras Rutinas Guiadas</span>
          </h3>

          <div className="space-y-3">
            {sessions.map(s => {
              const isActive = activeSession.id === s.id
              return (
                <button
                  key={s.id}
                  onClick={() => { setActiveSession(s); setIsPlaying(false); }}
                  className={`w-full p-4 rounded-2xl border-2 text-left flex items-center justify-between gap-4 transition-all ${
                    isActive
                      ? 'border-secondary bg-secondary-container shadow-soft-sm'
                      : 'border-outline-variant bg-surface hover:bg-surface-container'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-surface flex items-center justify-center text-secondary shrink-0 shadow-soft-sm">
                      <span className="material-symbols-outlined text-2xl">{s.icon}</span>
                    </div>
                    <div>
                      <h4 className="text-body-md font-bold text-primary">{s.title}</h4>
                      <p className="text-xs text-on-surface-variant font-medium mt-0.5">{s.duration} • {s.level}</p>
                    </div>
                  </div>

                  <span className="material-symbols-outlined text-2xl text-secondary">
                    {isActive ? 'play_circle' : 'chevron_right'}
                  </span>
                </button>
              )
            })}
          </div>
        </section>

      </main>

      <BottomNavBar />
    </div>
  )
}
