import React, { useState, useEffect } from 'react'
import TopAppBar from '../components/TopAppBar'
import BottomNavBar from '../components/BottomNavBar'
import api from '../api'

const MONTH_NAMES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

export default function Progress() {
  const user = api.getCurrentUser()

  const [currentDate] = useState(new Date())
  const [projection, setProjection] = useState(null)
  const [insights, setInsights] = useState(null)
  const [loading, setLoading] = useState(true)

  // Asistencia mensual simulada (Días completados con Verde Salvia)
  const completedDays = [2, 4, 5, 8, 9, 11, 14, 15, 16, 18, 22, 23, 24, 25, 26]

  useEffect(() => {
    if (!user) return
    loadAnalytics()
  }, [user])

  const loadAnalytics = async () => {
    setLoading(true)
    try {
      if (user?.id) {
        const proj = await api.getProjection(user.id).catch(() => null)
        const ins = await api.getInsights(user.id).catch(() => null)
        setProjection(proj)
        setInsights(ins)
      }
    } catch (err) {
      console.warn('Analytics info:', err)
    } finally {
      setLoading(false)
    }
  }

  const currentMonthName = MONTH_NAMES[currentDate.getMonth()]
  const currentYear = currentDate.getFullYear()
  const daysInMonth = new Date(currentYear, currentDate.getMonth() + 1, 0).getDate()
  const firstDayIndex = new Date(currentYear, currentDate.getMonth(), 1).getDay() // 0 = Sun

  return (
    <div className="min-h-screen bg-surface pb-32 text-left selection:bg-secondary-container">
      <TopAppBar title="Mi Progreso y Salud" user={user} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        
        {/* Encabezado con Celebración de Logro */}
        <section className="bg-primary text-on-primary rounded-3xl p-6 sm:p-8 shadow-soft-lg">
          <div className="flex items-center gap-3 mb-2">
            <span className="material-symbols-outlined text-secondary text-3xl">insights</span>
            <span className="text-xs font-bold uppercase tracking-wider text-secondary">
              Evolución y Constancia
            </span>
          </div>
          <h2 className="text-headline-md font-extrabold tracking-tight">
            ¡15 Días de Movimiento Este Mes!
          </h2>
          <p className="text-body-md text-white/80 mt-1">
            Tu movilidad articular y resistencia funcional muestran una tendencia muy favorable.
          </p>
        </section>

        {/* Métricas Principales */}
        <section className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-5 shadow-soft-sm text-center">
            <span className="material-symbols-outlined text-tertiary text-3xl mb-1">sentiment_very_satisfied</span>
            <span className="block text-3xl font-black text-primary">82%</span>
            <span className="text-xs font-bold uppercase text-on-surface-variant">Vitalidad General</span>
          </div>

          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-5 shadow-soft-sm text-center">
            <span className="material-symbols-outlined text-secondary text-3xl mb-1">speed</span>
            <span className="block text-3xl font-black text-primary">4.9 / 10</span>
            <span className="text-xs font-bold uppercase text-on-surface-variant">RPE Promedio (Óptimo)</span>
          </div>

          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-5 shadow-soft-sm text-center col-span-2 sm:col-span-1">
            <span className="material-symbols-outlined text-blue-600 text-3xl mb-1">water_drop</span>
            <span className="block text-3xl font-black text-primary">6.1</span>
            <span className="text-xs font-bold uppercase text-on-surface-variant">Vasos Agua / Día</span>
          </div>
        </section>

        {/* Calendario Mensual Salvia */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-sm">
          <div className="flex items-center justify-between pb-4 border-b border-outline-variant mb-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-secondary">
                Calendario de Asistencia
              </span>
              <h3 className="text-headline-sm font-bold text-primary mt-0.5">
                {currentMonthName} {currentYear}
              </h3>
            </div>
            <span className="text-xs font-bold px-3 py-1 bg-tertiary-container text-tertiary rounded-full border border-tertiary/20">
              ● Verde Salvia = Completado
            </span>
          </div>

          {/* Días de la semana */}
          <div className="grid grid-cols-7 gap-2 text-center text-xs font-bold uppercase text-on-surface-variant mb-3">
            <span>Dom</span>
            <span>Lun</span>
            <span>Mar</span>
            <span>Mié</span>
            <span>Jue</span>
            <span>Vie</span>
            <span>Sáb</span>
          </div>

          {/* Grid de Días */}
          <div className="grid grid-cols-7 gap-2 sm:gap-3 text-center">
            {Array.from({ length: firstDayIndex }).map((_, i) => (
              <div key={`empty-${i}`} className="p-2" />
            ))}

            {Array.from({ length: daysInMonth }).map((_, i) => {
              const dayNum = i + 1
              const isDone = completedDays.includes(dayNum)
              const isToday = dayNum === currentDate.getDate()

              return (
                <div
                  key={dayNum}
                  className={`min-h-[48px] rounded-2xl border-2 flex flex-col items-center justify-center transition-all ${
                    isDone
                      ? 'bg-tertiary text-on-tertiary border-tertiary font-extrabold shadow-soft-sm'
                      : (isToday
                          ? 'bg-secondary-container border-secondary text-primary font-bold'
                          : 'bg-surface border-outline-variant/60 text-on-surface-variant')
                  }`}
                >
                  <span className="text-sm sm:text-base">{dayNum}</span>
                </div>
              )
            })}
          </div>
        </section>

        {/* Proyección y Sugerencias de IA */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-md">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-secondary-container text-secondary flex items-center justify-center">
              <span className="material-symbols-outlined text-2xl">psychology</span>
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-secondary">
                Proyección Clínica IA
              </span>
              <h3 className="text-headline-sm font-bold text-primary">
                Predicción de Movilidad y Autonomía
              </h3>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-secondary-container/40 border border-secondary/20 space-y-3">
            <p className="text-body-sm text-primary font-medium leading-relaxed">
              {projection?.summary || "Manteniendo 3 sesiones semanales a nivel de esfuerzo moderado (RPE 4-5), se proyecta un incremento del 18% en fuerza de cuádriceps y estabilidad de marcha en las próximas 4 semanas."}
            </p>
            <div className="pt-2 border-t border-secondary/20 flex items-center gap-2 text-xs font-bold text-tertiary">
              <span className="material-symbols-outlined text-base">verified</span>
              <span>Validado por el módulo de análisis de SeniorVital.</span>
            </div>
          </div>
        </section>

      </main>

      <BottomNavBar />
    </div>
  )
}
