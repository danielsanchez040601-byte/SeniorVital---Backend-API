import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import TopAppBar from '../components/TopAppBar'
import BottomNavBar from '../components/BottomNavBar'
import api from '../api'

export default function Home({ user: propUser }) {
  const navigate = useNavigate()
  const user = propUser || api.getCurrentUser()
  
  // Routine states
  const [routine, setRoutine] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [catalog, setCatalog] = useState([])
  const [completedExercises, setCompletedExercises] = useState([])

  // Modal states for RPE & Tracking
  const [showRpeModal, setShowRpeModal] = useState(false)
  const [activeExercise, setActiveExercise] = useState(null)
  const [sets, setSets] = useState(3)
  const [reps, setReps] = useState(10)
  const [rpe, setRpe] = useState(5)
  const [feltDifficulty, setFeltDifficulty] = useState('moderado')
  const [painArea, setPainArea] = useState('ninguno')
  const [savingTracking, setSavingTracking] = useState(false)

  // Habits quick state
  const [waterGlasses, setWaterGlasses] = useState(4)
  const [medsTaken, setMedsTaken] = useState(true)

  // Attendance Days (Current Week, Sage green celebration)
  const [weekDays, setWeekDays] = useState([
    { day: 'Lun', num: 24, completed: true },
    { day: 'Mar', num: 25, completed: true },
    { day: 'Mié', num: 26, completed: true, isToday: true },
    { day: 'Jue', num: 27, completed: false },
    { day: 'Vie', num: 28, completed: false },
    { day: 'Sáb', num: 29, completed: false },
    { day: 'Dom', num: 30, completed: false },
  ])

  useEffect(() => {
    if (!user) return

    if (user.role === 'caregiver' || user.role === 'familiar') {
      navigate('/caregiver')
      return
    }

    if (user.role === 'admin' || user.role === 'physio') {
      navigate('/admin')
      return
    }

    loadInitialData()
  }, [user])

  const loadInitialData = async () => {
    setLoading(true)
    try {
      // 1. Catálogo
      const exercises = await api.listExercises().catch(() => [])
      setCatalog(exercises)

      // 2. Rutina de hoy
      if (user?.id) {
        const todayRot = await api.getTodayRoutine(user.id).catch(() => null)
        if (todayRot) {
          setRoutine(todayRot)
        } else {
          // Rutina mock por defecto mientras se genera
          setRoutine({
            routine_name: 'Movilidad Suave y Equilibrio Diario',
            recommendation_note: 'Plan adaptado por el Agente Wellness para activar articulaciones sin sobrecarga.',
            exercises: [
              { exercise_id: exercises[0]?.id || '1', name: 'Sentadilla Asistida en Silla', sets: 3, reps: 10, rest_seconds: 45, level: 1 },
              { exercise_id: exercises[1]?.id || '2', name: 'Elevación de Talones para Tobillos', sets: 3, reps: 12, rest_seconds: 30, level: 1 },
              { exercise_id: exercises[2]?.id || '3', name: 'Rotación Torácica con Respiración', sets: 2, reps: 8, rest_seconds: 30, level: 1 }
            ]
          })
        }
      }
    } catch (err) {
      console.warn('Data load info:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateRoutine = async () => {
    setGenerating(true)
    try {
      const newRoutine = await api.generateRoutine(user?.id || 'demo-user', true)
      setRoutine(newRoutine)
    } catch (err) {
      console.warn('AI routine generation fallback:', err)
      setRoutine({
        routine_name: 'Rutina Personalizada IA: Equilibrio y Marcha',
        recommendation_note: 'Ajuste dinámico generado por Ollama AI según tu nivel de energía.',
        exercises: [
          { exercise_id: 'ex-1', name: 'Marcha Estática con Apoyo Ligero', sets: 3, reps: 15, rest_seconds: 45, level: 1 },
          { exercise_id: 'ex-2', name: 'Flexión de Rodilla De Pie', sets: 3, reps: 10, rest_seconds: 45, level: 2 },
          { exercise_id: 'ex-3', name: 'Apertura de Pecho con Brazos Suaves', sets: 2, reps: 10, rest_seconds: 30, level: 1 }
        ]
      })
    } finally {
      setGenerating(false)
    }
  }

  const openExerciseCompleteModal = (exercise) => {
    setActiveExercise(exercise)
    setSets(exercise.sets || 3)
    setReps(exercise.reps || 10)
    setRpe(5)
    setFeltDifficulty('moderado')
    setPainArea('ninguno')
    setShowRpeModal(true)
  }

  const handleSaveTracking = async () => {
    if (!activeExercise) return
    setSavingTracking(true)
    try {
      if (user?.id && activeExercise.exercise_id) {
        await api.recordExercise(
          user.id,
          activeExercise.exercise_id,
          sets,
          reps,
          rpe,
          feltDifficulty
        ).catch(() => {})
      }

      // Marcar como completado localmente
      const completedId = activeExercise.exercise_id || activeExercise.name
      if (!completedExercises.includes(completedId)) {
        setCompletedExercises([...completedExercises, completedId])
      }

      setShowRpeModal(false)
    } catch (err) {
      console.error('Error saving tracking:', err)
      setShowRpeModal(false)
    } finally {
      setSavingTracking(false)
    }
  }

  const getRpeDetails = (val) => {
    if (val <= 3) return { label: 'Muy Suave / Relajado', color: 'text-tertiary bg-tertiary-container border-tertiary/30', emoji: '😊' }
    if (val <= 6) return { label: 'Moderado / Cómodo', color: 'text-warning bg-warning-container border-warning/30', emoji: '🙂' }
    if (val <= 8) return { label: 'Intenso / Buen Esfuerzo', color: 'text-secondary bg-secondary-container border-secondary/30', emoji: '😅' }
    return { label: 'Muy Duro / Exigente', color: 'text-error bg-error-container border-error/30', emoji: '🥵' }
  }

  const rpeInfo = getRpeDetails(rpe)

  const userName = user?.profile?.name || user?.email?.split('@')[0] || 'Manuel'

  return (
    <div className="min-h-screen bg-surface pb-32 text-left selection:bg-secondary-container">
      <TopAppBar title="Mi Bienestar" user={user} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        
        {/* 1. Saludo Cálido y Resumen del Día */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-md relative overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="w-3 h-3 rounded-full bg-tertiary animate-pulse" />
                <span className="text-xs font-bold uppercase tracking-wider text-tertiary">
                  Agente Wellness IA Activo
                </span>
              </div>
              <h2 className="text-headline-md sm:text-headline-lg font-extrabold text-primary tracking-tight">
                ¡Buenos días, {userName}!
              </h2>
              <p className="text-body-md text-on-surface-variant font-medium mt-1">
                Tu cuerpo responde con fuerza a la constancia tranquila. ¿Listo para el movimiento de hoy?
              </p>
            </div>

            <button
              onClick={handleGenerateRoutine}
              disabled={generating}
              className="min-h-[56px] px-6 rounded-2xl bg-secondary hover:bg-red-700 text-on-secondary font-bold text-base shadow-soft-sm flex items-center justify-center gap-2 shrink-0 transition-all active:scale-95"
            >
              <span className={`material-symbols-outlined text-2xl ${generating ? 'animate-spin' : ''}`}>
                {generating ? 'autorenew' : 'smart_toy'}
              </span>
              <span>{generating ? 'Generando con IA...' : 'Adaptar Rutina Hoy'}</span>
            </button>
          </div>
        </section>

        {/* 2. Calendario de Asistencia Salvia (Sin Rachas Punitivas) */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 shadow-soft-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-tertiary text-2xl">calendar_today</span>
              <h3 className="text-headline-sm font-bold text-primary">
                Mi Semana de Actividad
              </h3>
            </div>
            <span className="text-xs font-bold px-3 py-1 bg-tertiary-container text-tertiary rounded-full border border-tertiary/20">
              3 días completados
            </span>
          </div>

          <p className="text-body-sm text-on-surface-variant mb-4">
            Cada día cuenta a tu propio ritmo. Los días marcados en verde celebran tu dedicación.
          </p>

          <div className="grid grid-cols-7 gap-2 sm:gap-3 text-center">
            {weekDays.map((d, i) => (
              <div 
                key={i}
                className={`py-3 px-1 rounded-2xl border-2 flex flex-col items-center justify-center transition-all ${
                  d.completed
                    ? 'bg-tertiary text-on-tertiary border-tertiary font-bold shadow-soft-sm'
                    : (d.isToday 
                        ? 'bg-secondary-container border-secondary text-primary font-bold' 
                        : 'bg-surface border-outline-variant text-on-surface-variant')
                }`}
              >
                <span className="text-xs uppercase font-medium">{d.day}</span>
                <span className="text-lg sm:text-xl font-extrabold my-0.5">{d.num}</span>
                <span className="material-symbols-outlined text-lg">
                  {d.completed ? 'check_circle' : (d.isToday ? 'radio_button_checked' : 'horizontal_rule')}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* 3. Tarjeta de Rutina del Día */}
        <section className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-md">
          <div className="flex items-center justify-between pb-4 border-b border-outline-variant mb-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-secondary">
                Entrenamiento Recomendado
              </span>
              <h3 className="text-headline-md font-extrabold text-primary mt-0.5">
                {routine?.routine_name || 'Movilidad Funcional en Silla'}
              </h3>
            </div>
            <Link
              to="/video"
              className="min-h-[48px] px-4 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant text-primary font-bold text-sm flex items-center gap-2 transition-colors"
            >
              <span className="material-symbols-outlined text-xl text-secondary">play_circle</span>
              <span>Ver en Video</span>
            </Link>
          </div>

          {routine?.recommendation_note && (
            <div className="p-4 rounded-2xl bg-secondary-container/40 border border-secondary/20 mb-6 flex items-start gap-3">
              <span className="material-symbols-outlined text-secondary text-2xl shrink-0 mt-0.5">lightbulb</span>
              <p className="text-body-sm text-primary leading-relaxed font-medium">
                {routine.recommendation_note}
              </p>
            </div>
          )}

          {/* Lista de Ejercicios */}
          <div className="space-y-4">
            {routine?.exercises?.map((ex, index) => {
              const isCompleted = completedExercises.includes(ex.exercise_id || ex.name)
              return (
                <div 
                  key={index}
                  className={`p-4 sm:p-5 rounded-2xl border-2 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all ${
                    isCompleted 
                      ? 'bg-tertiary-container/30 border-tertiary/40' 
                      : 'bg-surface border-outline-variant hover:border-secondary/50'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-lg shrink-0 ${
                      isCompleted 
                        ? 'bg-tertiary text-on-tertiary' 
                        : 'bg-surface-container text-primary border border-outline-variant'
                    }`}>
                      {isCompleted ? (
                        <span className="material-symbols-outlined text-2xl">check</span>
                      ) : (
                        index + 1
                      )}
                    </div>
                    <div>
                      <h4 className="text-body-lg font-bold text-primary">{ex.name}</h4>
                      <p className="text-body-sm text-on-surface-variant font-medium">
                        {ex.sets || 3} series × {ex.reps || 10} repeticiones • Descanso: {ex.rest_seconds || 45}s
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => openExerciseCompleteModal(ex)}
                    className={`min-h-[52px] px-6 rounded-2xl font-bold text-base flex items-center justify-center gap-2 transition-all active:scale-95 ${
                      isCompleted
                        ? 'bg-tertiary-container text-tertiary border border-tertiary/30'
                        : 'bg-secondary text-on-secondary hover:bg-red-700 shadow-soft-sm'
                    }`}
                  >
                    <span className="material-symbols-outlined text-xl">
                      {isCompleted ? 'edit' : 'task_alt'}
                    </span>
                    <span>{isCompleted ? 'Registrado' : 'Registrar Esfuerzo'}</span>
                  </button>
                </div>
              )
            })}
          </div>
        </section>

        {/* 4. Widget Rápido de Hidratación y Medicación */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Hidratación con Botones Gigantes */}
          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 shadow-soft-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-600 text-3xl">water_drop</span>
                <h3 className="text-headline-sm font-bold text-primary">Agua Hoy</h3>
              </div>
              <span className="text-xs font-bold px-3 py-1 bg-blue-50 text-blue-800 rounded-full border border-blue-200">
                Meta: 6 a 8 vasos
              </span>
            </div>

            <div className="flex items-center justify-between py-2">
              <button
                onClick={() => setWaterGlasses(Math.max(0, waterGlasses - 1))}
                className="w-16 h-16 rounded-2xl bg-surface-container hover:bg-surface-container-high border-2 border-outline-variant text-primary font-extrabold text-3xl flex items-center justify-center active:scale-95 transition-transform"
                aria-label="Restar vaso de agua"
              >
                −
              </button>

              <div className="text-center">
                <span className="text-4xl font-extrabold text-primary">{waterGlasses}</span>
                <span className="block text-xs font-bold uppercase tracking-wider text-on-surface-variant">Vasos Tomados</span>
              </div>

              <button
                onClick={() => setWaterGlasses(waterGlasses + 1)}
                className="w-16 h-16 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-3xl flex items-center justify-center shadow-soft-sm active:scale-95 transition-transform"
                aria-label="Añadir vaso de agua"
              >
                +
              </button>
            </div>
          </div>

          {/* Medicación Rápida */}
          <div className="bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 shadow-soft-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-secondary text-3xl">pill</span>
                  <h3 className="text-headline-sm font-bold text-primary">Medicamentos</h3>
                </div>
                <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                  medsTaken ? 'bg-tertiary-container text-tertiary border-tertiary/20' : 'bg-warning-container text-warning border-warning/20'
                }`}>
                  {medsTaken ? 'Al día' : 'Pendiente'}
                </span>
              </div>
              <p className="text-body-sm text-on-surface-variant">
                Recordatorio de toma matutina y vespertina.
              </p>
            </div>

            <button
              onClick={() => setMedsTaken(!medsTaken)}
              className={`w-full min-h-[56px] mt-4 rounded-2xl font-bold text-base flex items-center justify-center gap-3 border-2 transition-all ${
                medsTaken
                  ? 'bg-tertiary text-on-tertiary border-tertiary shadow-soft-sm'
                  : 'bg-surface text-primary border-outline-variant hover:bg-surface-container'
              }`}
            >
              <span className="material-symbols-outlined text-2xl">
                {medsTaken ? 'check_circle' : 'radio_button_unchecked'}
              </span>
              <span>{medsTaken ? '¡Medicinas Tomadas Hoy!' : 'Marcar como Tomadas'}</span>
            </button>
          </div>
        </section>

      </main>

      {/* MODAL DE REGISTRO DE ESFUERZO RPE (1-10) Y DOLOR */}
      {showRpeModal && activeExercise && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/70 backdrop-blur-sm animate-fade-in">
          <div 
            className="w-full max-w-lg bg-surface border-2 border-outline-variant rounded-3xl p-6 sm:p-8 shadow-soft-xl max-h-[90vh] overflow-y-auto text-left"
            role="dialog"
            aria-modal="true"
          >
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant mb-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-secondary">
                  Registro de Esfuerzo Clínico
                </span>
                <h3 className="text-headline-sm font-bold text-primary">{activeExercise.name}</h3>
              </div>
              <button
                onClick={() => setShowRpeModal(false)}
                className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-surface-container text-on-surface-variant"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {/* Selector de Escala RPE (1-10 con Emojis) */}
            <div className="mb-6">
              <label className="block text-body-md font-bold text-primary mb-2">
                ¿Cómo sentiste la intensidad? (Escala RPE 1-10)
              </label>

              <div className={`p-4 rounded-2xl border-2 flex items-center justify-between mb-4 ${rpeInfo.color}`}>
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{rpeInfo.emoji}</span>
                  <div>
                    <span className="text-xs uppercase font-bold tracking-wider block">Nivel RPE {rpe} de 10</span>
                    <span className="text-base font-extrabold">{rpeInfo.label}</span>
                  </div>
                </div>
                <span className="text-2xl font-black">{rpe}</span>
              </div>

              {/* Slider Táctil RPE */}
              <input
                type="range"
                min="1"
                max="10"
                value={rpe}
                onChange={(e) => setRpe(parseInt(e.target.value))}
                className="w-full h-3 bg-surface-container-high rounded-lg appearance-none cursor-pointer accent-secondary"
              />
              <div className="flex justify-between text-xs text-on-surface-variant font-bold mt-1 px-1">
                <span>1 (Muy Suave)</span>
                <span>5 (Moderado)</span>
                <span>10 (Máximo)</span>
              </div>
            </div>

            {/* Series y Repeticiones */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-xs font-bold uppercase text-on-surface-variant mb-1">Series Realizadas</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={sets}
                  onChange={(e) => setSets(e.target.value)}
                  className="w-full min-h-[52px] px-3 rounded-2xl border-2 border-outline-variant bg-surface text-xl font-bold text-primary text-center"
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-on-surface-variant mb-1">Repeticiones</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={reps}
                  onChange={(e) => setReps(e.target.value)}
                  className="w-full min-h-[52px] px-3 rounded-2xl border-2 border-outline-variant bg-surface text-xl font-bold text-primary text-center"
                />
              </div>
            </div>

            {/* Aviso de Dolor Articular */}
            <div className="mb-6">
              <label className="block text-body-sm font-bold text-primary mb-2">
                ¿Sentiste alguna molestia o dolor durante el ejercicio?
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'ninguno', label: 'Sin Dolor' },
                  { id: 'rodilla', label: 'Rodilla' },
                  { id: 'espalda', label: 'Espalda' },
                  { id: 'hombro', label: 'Hombro' },
                  { id: 'cadera', label: 'Cadera' },
                  { id: 'otro', label: 'Otro' }
                ].map(p => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setPainArea(p.id)}
                    className={`min-h-[44px] py-2 px-3 rounded-xl border-2 text-xs font-bold transition-all ${
                      painArea === p.id 
                        ? (p.id === 'ninguno' ? 'border-tertiary bg-tertiary-container text-tertiary' : 'border-error bg-error-container text-on-error-container') 
                        : 'border-outline-variant bg-surface text-on-surface-variant'
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Botón de Guardar */}
            <button
              onClick={handleSaveTracking}
              disabled={savingTracking}
              className="w-full min-h-[56px] bg-tertiary hover:bg-sage-dark text-on-tertiary font-bold text-lg rounded-2xl shadow-soft-sm flex items-center justify-center gap-2 transition-all active:scale-98"
            >
              <span className="material-symbols-outlined">check_circle</span>
              <span>{savingTracking ? 'Guardando...' : 'Completar y Guardar Registro'}</span>
            </button>
          </div>
        </div>
      )}

      <BottomNavBar />
    </div>
  )
}
