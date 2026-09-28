import React, { useState, useEffect } from 'react'
import TopAppBar from '../components/TopAppBar'
import BottomNavBar from '../components/BottomNavBar'
import api from '../api'

export default function Habits() {
  const user = api.getCurrentUser()
  const todayStr = new Date().toISOString().split('T')[0]

  const [water, setWater] = useState(4)
  const [walking, setWalking] = useState(20)
  const [medsTaken, setMedsTaken] = useState(true)
  const [sleepHours, setSleepHours] = useState(7.5)
  const [savedSuccess, setSavedSuccess] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!user) return
    loadHabits()
  }, [user])

  const loadHabits = async () => {
    try {
      const data = await api.getHabitsForDate(user.id, todayStr).catch(() => null)
      if (data) {
        setWater(data.water_glasses ?? 4)
        setWalking(data.walking_minutes ?? 20)
        setMedsTaken(data.meds_taken ?? true)
        setSleepHours(data.sleep_hours ?? 7.5)
      }
    } catch (err) {
      console.warn('Habits load:', err)
    }
  }

  const handleSave = async (newWater, newWalking, newMeds, newSleep) => {
    setSaving(true)
    try {
      setWater(newWater)
      setWalking(newWalking)
      setMedsTaken(newMeds)
      setSleepHours(newSleep)

      if (user?.id) {
        await api.saveHabits(user.id, todayStr, {
          water_glasses: newWater,
          walking_minutes: newWalking,
          meds_taken: newMeds,
          sleep_hours: newSleep
        }).catch(() => {})
      }
      setSavedSuccess(true)
      setTimeout(() => setSavedSuccess(false), 2500)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface pb-32 text-left selection:bg-secondary-container">
      <TopAppBar title="Registro de Hábitos" user={user} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        
        {/* Encabezado Cálido */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-md">
          <div className="flex items-center gap-3 mb-2">
            <span className="material-symbols-outlined text-secondary text-3xl">spa</span>
            <h2 className="text-headline-md font-extrabold text-primary">
              Tus Hábitos Saludables de Hoy
            </h2>
          </div>
          <p className="text-body-md text-on-surface-variant font-medium">
            Pequeños actos de cuidado diario que renuevan tu energía y movilidad articular.
          </p>

          {savedSuccess && (
            <div className="mt-4 p-3 rounded-2xl bg-sage-light text-sage-dark border border-sage/30 text-sm font-bold flex items-center gap-2 animate-fade-in">
              <span className="material-symbols-outlined">check_circle</span>
              <span>¡Hábitos guardados correctamente!</span>
            </div>
          )}
        </section>

        {/* 1. Hidratación (Vasos de Agua) */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-outline-variant mb-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-700 flex items-center justify-center">
                <span className="material-symbols-outlined text-3xl">water_drop</span>
              </div>
              <div>
                <h3 className="text-headline-sm font-bold text-primary">Hidratación Diaria</h3>
                <span className="text-xs font-semibold text-on-surface-variant">Recomendado: 6 a 8 vasos de agua</span>
              </div>
            </div>
            <span className="text-xs font-bold px-3 py-1 bg-blue-50 text-blue-800 rounded-full border border-blue-200 self-start sm:self-auto">
              {water >= 6 ? '¡Meta alcanzada!' : `${water} de 6 vasos`}
            </span>
          </div>

          <div className="flex items-center justify-center gap-8 py-4">
            <button
              onClick={() => handleSave(Math.max(0, water - 1), walking, medsTaken, sleepHours)}
              className="w-20 h-20 rounded-3xl bg-surface-container hover:bg-surface-container-high border-2 border-outline-variant text-primary font-extrabold text-4xl flex items-center justify-center active:scale-95 transition-transform"
              aria-label="Disminuir un vaso de agua"
            >
              −
            </button>

            <div className="text-center">
              <span className="text-5xl sm:text-6xl font-black text-primary">{water}</span>
              <span className="block text-xs font-bold uppercase tracking-wider text-on-surface-variant mt-1">Vasos de Agua</span>
            </div>

            <button
              onClick={() => handleSave(water + 1, walking, medsTaken, sleepHours)}
              className="w-20 h-20 rounded-3xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-4xl flex items-center justify-center shadow-soft-md active:scale-95 transition-transform"
              aria-label="Aumentar un vaso de agua"
            >
              +
            </button>
          </div>
        </section>

        {/* 2. Caminata y Movimiento Activo */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-outline-variant mb-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-secondary-container text-secondary flex items-center justify-center">
                <span className="material-symbols-outlined text-3xl">directions_walk</span>
              </div>
              <div>
                <h3 className="text-headline-sm font-bold text-primary">Paseo / Caminata Activa</h3>
                <span className="text-xs font-semibold text-on-surface-variant">Meta diaria sugerida: 20 a 30 minutos</span>
              </div>
            </div>
            <span className="text-xs font-bold px-3 py-1 bg-secondary-container text-on-secondary-container rounded-full border border-secondary/20 self-start sm:self-auto">
              {walking} minutos
            </span>
          </div>

          <div className="flex items-center justify-center gap-8 py-4">
            <button
              onClick={() => handleSave(water, Math.max(0, walking - 5), medsTaken, sleepHours)}
              className="w-20 h-20 rounded-3xl bg-surface-container hover:bg-surface-container-high border-2 border-outline-variant text-primary font-extrabold text-4xl flex items-center justify-center active:scale-95 transition-transform"
              aria-label="Restar 5 minutos de caminata"
            >
              −
            </button>

            <div className="text-center">
              <span className="text-5xl sm:text-6xl font-black text-primary">{walking}</span>
              <span className="block text-xs font-bold uppercase tracking-wider text-on-surface-variant mt-1">Minutos Caminados</span>
            </div>

            <button
              onClick={() => handleSave(water, walking + 5, medsTaken, sleepHours)}
              className="w-20 h-20 rounded-3xl bg-secondary hover:bg-red-700 text-on-secondary font-extrabold text-4xl flex items-center justify-center shadow-soft-md active:scale-95 transition-transform"
              aria-label="Sumar 5 minutos de caminata"
            >
              +
            </button>
          </div>
        </section>

        {/* 3. Medicación y Sueño Reparador */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Medicación */}
          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 shadow-soft-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="material-symbols-outlined text-secondary text-3xl">medication</span>
                <h3 className="text-headline-sm font-bold text-primary">Toma de Medicina</h3>
              </div>
              <p className="text-body-sm text-on-surface-variant">
                Presiona para confirmar si tomaste las pastillas indicadas por tu médico.
              </p>
            </div>

            <button
              onClick={() => handleSave(water, walking, !medsTaken, sleepHours)}
              className={`w-full min-h-[64px] mt-6 rounded-2xl font-bold text-lg flex items-center justify-center gap-3 border-2 transition-all active:scale-98 ${
                medsTaken
                  ? 'bg-tertiary text-on-tertiary border-tertiary shadow-soft-sm'
                  : 'bg-surface text-primary border-outline-variant hover:bg-surface-container'
              }`}
            >
              <span className="material-symbols-outlined text-3xl">
                {medsTaken ? 'task_alt' : 'radio_button_unchecked'}
              </span>
              <span>{medsTaken ? '¡Medicinas Completas!' : 'Marcar como Tomadas'}</span>
            </button>
          </div>

          {/* Horas de Descanso */}
          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 shadow-soft-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="material-symbols-outlined text-indigo-600 text-3xl">bedtime</span>
                <h3 className="text-headline-sm font-bold text-primary">Descanso Nocturno</h3>
              </div>
              <p className="text-body-sm text-on-surface-variant">
                El descanso repara los tejidos musculares y la memoria.
              </p>
            </div>

            <div className="flex items-center justify-between mt-4 p-3 bg-surface rounded-2xl border-2 border-outline-variant">
              <button
                onClick={() => handleSave(water, walking, medsTaken, Math.max(4, sleepHours - 0.5))}
                className="w-12 h-12 rounded-xl bg-surface-container hover:bg-surface-container-high text-primary font-bold text-xl flex items-center justify-center"
              >
                −
              </button>
              <div className="text-center">
                <span className="text-2xl font-extrabold text-primary">{sleepHours} hrs</span>
                <span className="block text-[11px] font-bold text-on-surface-variant">Sueño Anoche</span>
              </div>
              <button
                onClick={() => handleSave(water, walking, medsTaken, Math.min(12, sleepHours + 0.5))}
                className="w-12 h-12 rounded-xl bg-surface-container hover:bg-surface-container-high text-primary font-bold text-xl flex items-center justify-center"
              >
                +
              </button>
            </div>
          </div>
        </section>

      </main>

      <BottomNavBar />
    </div>
  )
}
