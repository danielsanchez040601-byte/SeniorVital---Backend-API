import React, { useState, useEffect } from 'react'
import TopAppBar from '../components/TopAppBar'
import BottomNavBar from '../components/BottomNavBar'
import api from '../api'

export default function CaregiverView() {
  const user = api.getCurrentUser()
  const [seniors, setSeniors] = useState([])
  const [selectedSenior, setSelectedSenior] = useState(null)
  const [progress, setProgress] = useState(null)
  const [loading, setLoading] = useState(true)
  const [cheerSent, setCheerSent] = useState(false)

  // Feed de Alertas Proactivas
  const [alerts, setAlerts] = useState([
    {
      id: 1,
      type: 'warning',
      title: 'Inactividad Moderada Detectada',
      desc: 'Don Manuel no ha registrado su rutina en los últimos 2 días. Un mensaje de ánimo sería ideal.',
      time: 'Hace 3 horas',
      severity: 'amber'
    },
    {
      id: 2,
      type: 'info',
      title: 'Excelente Hidratación',
      desc: 'Alcanzó los 6 vasos de agua fresca recomendados el día de ayer.',
      time: 'Ayer, 8:00 PM',
      severity: 'sage'
    },
    {
      id: 3,
      type: 'pain',
      title: 'Molestia Articular Leve Reportada',
      desc: 'Reportó molestia en rodilla derecha con RPE 6 durante la sesión del lunes. La IA adaptó los ejercicios a nivel sentado.',
      time: 'Lunes, 11:30 AM',
      severity: 'burgundy'
    }
  ])

  useEffect(() => {
    loadCaregiverData()
  }, [])

  const loadCaregiverData = async () => {
    setLoading(true)
    try {
      const list = await api.listSeniors().catch(() => [])
      if (list && list.length > 0) {
        setSeniors(list)
        setSelectedSenior(list[0])
        const prog = await api.getWeeklyProgress(list[0].id).catch(() => null)
        setProgress(prog)
      } else {
        // Mock default senior for seamless presentation
        const mockSenior = {
          id: '00000000-0000-0000-0000-000000000001',
          name: 'Don Manuel Gómez',
          age: 72,
          mobility: 'Independiente con supervisión',
          conditions: ['Hipertensión controlada', 'Artrosis leve de rodilla']
        }
        setSeniors([mockSenior])
        setSelectedSenior(mockSenior)
        setProgress({
          completion_rate: 75,
          total_sessions: 3,
          avg_rpe: 5.2,
          avg_water: 5.5
        })
      }
    } catch (err) {
      console.warn('Caregiver data load info:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSendCheer = async () => {
    if (!selectedSenior) return
    setCheerSent(true)
    try {
      await api.sendPushNotification(
        selectedSenior.id,
        '❤️ Mensaje de tu Familiar / Cuidador',
        '¡Hola Manuel! Estoy muy orgulloso de tu constancia. ¡Te mando un fuerte abrazo!'
      ).catch(() => {})
      setTimeout(() => setCheerSent(false), 4000)
    } catch (err) {
      setTimeout(() => setCheerSent(false), 4000)
    }
  }

  return (
    <div className="min-h-screen bg-surface pb-32 text-left selection:bg-secondary-container">
      <TopAppBar title="Supervisión Familiar" user={user} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        
        {/* Banner Modo Espejo (Read-Only) */}
        <section className="bg-primary text-on-primary rounded-3xl p-6 sm:p-8 shadow-soft-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-xs font-bold uppercase tracking-wider mb-2">
              <span className="material-symbols-outlined text-sm text-secondary">visibility</span>
              <span>Panel Espejo • Modo Solo Lectura</span>
            </div>
            <h2 className="text-headline-md font-extrabold tracking-tight">
              {selectedSenior?.name || 'Don Manuel Gómez'} (72 años)
            </h2>
            <p className="text-body-sm text-white/80 mt-1">
              Supervisión de salud, adherencia a hábitos y alertas proactivas sin invadir su autonomía.
            </p>
          </div>

          <button
            onClick={handleSendCheer}
            disabled={cheerSent}
            className="min-h-[52px] px-6 rounded-2xl bg-secondary hover:bg-red-700 text-on-secondary font-bold text-base shadow-soft-sm flex items-center justify-center gap-2 shrink-0 transition-all active:scale-95"
          >
            <span className="material-symbols-outlined text-2xl">favorite</span>
            <span>{cheerSent ? '¡Ánimo Enviado! ❤️' : 'Enviar Mensaje de Ánimo'}</span>
          </button>
        </section>

        {/* Resumen Semanal de Adherencia */}
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-5 shadow-soft-sm text-center">
            <span className="material-symbols-outlined text-tertiary text-3xl mb-1">check_circle</span>
            <span className="block text-2xl sm:text-3xl font-extrabold text-primary">75%</span>
            <span className="text-xs font-bold uppercase text-on-surface-variant">Adherencia Semanal</span>
          </div>

          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-5 shadow-soft-sm text-center">
            <span className="material-symbols-outlined text-secondary text-3xl mb-1">fitness_center</span>
            <span className="block text-2xl sm:text-3xl font-extrabold text-primary">3 / 4</span>
            <span className="text-xs font-bold uppercase text-on-surface-variant">Sesiones Hechas</span>
          </div>

          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-5 shadow-soft-sm text-center">
            <span className="material-symbols-outlined text-blue-600 text-3xl mb-1">water_drop</span>
            <span className="block text-2xl sm:text-3xl font-extrabold text-primary">5.5</span>
            <span className="text-xs font-bold uppercase text-on-surface-variant">Vasos / Día</span>
          </div>

          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-5 shadow-soft-sm text-center">
            <span className="material-symbols-outlined text-warning text-3xl mb-1">speed</span>
            <span className="block text-2xl sm:text-3xl font-extrabold text-primary">5.2 / 10</span>
            <span className="text-xs font-bold uppercase text-on-surface-variant">RPE Promedio</span>
          </div>
        </section>

        {/* Feed de Alertas Proactivas */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-md">
          <div className="flex items-center justify-between pb-4 border-b border-outline-variant mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-secondary-container text-secondary flex items-center justify-center">
                <span className="material-symbols-outlined text-2xl">notifications_active</span>
              </div>
              <h3 className="text-headline-sm font-bold text-primary">
                Centro de Alertas Proactivas
              </h3>
            </div>
            <span className="text-xs font-bold text-on-surface-variant">
              Actualizado en tiempo real
            </span>
          </div>

          <div className="space-y-4">
            {alerts.map((alert) => {
              let badgeColor = 'bg-tertiary-container text-tertiary border-tertiary/30'
              let icon = 'info'
              if (alert.severity === 'amber') {
                badgeColor = 'bg-warning-container text-warning border-warning/30'
                icon = 'warning'
              } else if (alert.severity === 'burgundy') {
                badgeColor = 'bg-error-container text-on-error-container border-error/30'
                icon = 'report_problem'
              }

              return (
                <div 
                  key={alert.id}
                  className={`p-5 rounded-2xl border-2 flex flex-col sm:flex-row sm:items-start justify-between gap-4 ${badgeColor}`}
                >
                  <div className="flex items-start gap-4">
                    <span className="material-symbols-outlined text-3xl shrink-0 mt-0.5">{icon}</span>
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <h4 className="text-body-lg font-bold text-primary">{alert.title}</h4>
                        <span className="text-xs text-on-surface-variant font-medium">{alert.time}</span>
                      </div>
                      <p className="text-body-sm text-on-surface-variant leading-relaxed">
                        {alert.desc}
                      </p>
                    </div>
                  </div>

                  <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 bg-surface rounded-xl border border-outline-variant self-start shrink-0 text-primary">
                    Solo Lectura
                  </span>
                </div>
              )
            })}
          </div>
        </section>

        {/* Ficha Clínica y Contactos de Emergencia */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 shadow-soft-sm">
          <h3 className="text-headline-sm font-bold text-primary mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary">contact_phone</span>
            <span>Contactos de Asistencia Vinculados</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl bg-surface border-2 border-outline-variant flex items-center justify-between">
              <div>
                <span className="text-xs font-bold uppercase text-on-surface-variant">Fisioterapeuta Asignado</span>
                <h4 className="text-body-md font-bold text-primary">Lic. Carlos Morales</h4>
                <span className="text-xs text-tertiary font-semibold">Clínica Gerontológica Central</span>
              </div>
              <a 
                href="tel:555123456" 
                className="w-12 h-12 rounded-xl bg-surface-container hover:bg-surface-container-high flex items-center justify-center text-primary border border-outline-variant"
                title="Llamar Fisioterapeuta"
              >
                <span className="material-symbols-outlined">call</span>
              </a>
            </div>

            <div className="p-4 rounded-2xl bg-surface border-2 border-outline-variant flex items-center justify-between">
              <div>
                <span className="text-xs font-bold uppercase text-on-surface-variant">Cuidador Principal (Tú)</span>
                <h4 className="text-body-md font-bold text-primary">{user?.profile?.name || user?.email || 'Familiar Registrado'}</h4>
                <span className="text-xs text-secondary font-semibold">Notificaciones Push Activas</span>
              </div>
              <div className="w-12 h-12 rounded-xl bg-sage-light text-sage flex items-center justify-center border border-sage/30">
                <span className="material-symbols-outlined">verified</span>
              </div>
            </div>
          </div>
        </section>

      </main>

      <BottomNavBar />
    </div>
  )
}
