import React, { useState } from 'react'
import api from '../api'

export default function AuthOnboarding({ onAuthSuccess }) {
  const [mode, setMode] = useState('welcome') // 'welcome' | 'login' | 'wizard'
  const [step, setStep] = useState(1) // 1 to 5
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Form Data
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState('senior') // 'senior' | 'caregiver' | 'admin'

  // Clinical Profile Data
  const [ageRange, setAgeRange] = useState('65-75')
  const [mobilityLevel, setMobilityLevel] = useState('independiente')
  const [restrictions, setRestrictions] = useState([])
  const [goals, setGoals] = useState([])

  const mobilityOptions = [
    {
      id: 'independiente',
      title: 'Independiente y Activo',
      description: 'Puedo caminar y moverme con total autonomía en el hogar.',
      icon: 'directions_walk'
    },
    {
      id: 'asistido',
      title: 'Movilidad Asistida',
      description: 'Uso bastón, andador o apoyo ocasional para caminar seguro.',
      icon: 'assist_walker'
    },
    {
      id: 'sentado',
      title: 'Mayormente Sentado',
      description: 'Prefiero rutinas y ejercicios sentados en una silla firme.',
      icon: 'chair'
    }
  ]

  const restrictionOptions = [
    { id: 'artritis', label: 'Artritis / Artrosis', icon: 'back_hand' },
    { id: 'osteoporosis', label: 'Osteoporosis', icon: 'bone' },
    { id: 'hipertension', label: 'Hipertensión', icon: 'cardiology' },
    { id: 'lumbar', label: 'Dolor Lumbar / Espalda', icon: 'accessibility_new' },
    { id: 'ninguna', label: 'Ninguna Restricción', icon: 'verified' }
  ]

  const goalOptions = [
    { id: 'equilibrio', title: 'Mejorar Equilibrio y Estabilidad', icon: 'balance', desc: 'Prevenir tropiezos y ganar confianza al caminar.' },
    { id: 'fuerza', title: 'Mantener Fuerza y Tono Muscular', icon: 'fitness_center', desc: 'Subir escaleras y cargar objetos con ligereza.' },
    { id: 'alivio', title: 'Alivio del Dolor Articular', icon: 'spa', desc: 'Movilidad suave para despertar las articulaciones sin impacto.' },
    { id: 'vitalidad', title: 'Energía y Vitalidad Diaria', icon: 'sentiment_very_satisfied', desc: 'Sentirme activo, ágil y de buen ánimo cada día.' }
  ]

  const toggleRestriction = (id) => {
    if (id === 'ninguna') {
      setRestrictions(['ninguna'])
      return
    }
    const filtered = restrictions.filter(r => r !== 'ninguna')
    if (filtered.includes(id)) {
      setRestrictions(filtered.filter(r => r !== id))
    } else {
      setRestrictions([...filtered, id])
    }
  }

  const toggleGoal = (id) => {
    if (goals.includes(id)) {
      setGoals(goals.filter(g => g !== id))
    } else {
      setGoals([...goals, id])
    }
  }

  const handleDemoLogin = async (selectedRole) => {
    setLoading(true)
    setError('')
    
    let targetEmail = 'senior@vital.com'
    let defaultName = 'Don Manuel Gómez'
    if (selectedRole === 'caregiver') {
      targetEmail = 'caregiver@vital.com'
      defaultName = 'Dra. Elena Ramos'
    } else if (selectedRole === 'admin') {
      targetEmail = 'admin@vital.com'
      defaultName = 'Lic. Carlos Morales'
    }

    const mockUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: targetEmail,
      role: selectedRole,
      profile: {
        name: defaultName,
        age: 72,
        fitness_level: 'moderado',
        goals: ['Mejorar equilibrio', 'Aliviar dolor articular'],
        restrictions: ['Artritis leve', 'Hipertensión']
      }
    }

    try {
      // Intentar login con timeout de 2.5s para no bloquear al usuario por cold-start de Render
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 2500)

      const user = await Promise.race([
        api.login(targetEmail, 'VitalPass123'),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout de servidor')), 2500))
      ])
      clearTimeout(timeoutId)
      
      if (user) {
        onAuthSuccess(user)
        return
      }
    } catch (err) {
      console.log('Ingresando con sesión de demostración instantánea:', err)
    }

    // Fallback instantáneo garantizado
    localStorage.setItem('sv_user', JSON.stringify(mockUser))
    localStorage.setItem('sv_token', 'demo-token-seniorvital-2026')
    onAuthSuccess(mockUser)
    setLoading(false)
  }

  const handleManualLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const user = await api.login(email, password)
      onAuthSuccess(user)
    } catch (err) {
      setError(err.message || 'Credenciales incorrectas o servidor no disponible.')
    } finally {
      setLoading(false)
    }
  }

  const handleFinishWizard = async () => {
    setLoading(true)
    setError('')

    const finalEmail = email.trim() || `usuario_${Math.floor(Math.random() * 9000 + 1000)}@seniorvital.com`
    const finalPassword = password.trim() || 'VitalPass123'
    const finalName = name.trim() || 'Nuevo Miembro SeniorVital'

    const clinicalProfile = {
      name: finalName,
      age_range: ageRange,
      mobility: mobilityLevel,
      restrictions: restrictions.length > 0 ? restrictions : ['ninguna'],
      goals: goals.length > 0 ? goals : ['equilibrio'],
      fitness_level: mobilityLevel === 'sentado' ? 'principiante' : (mobilityLevel === 'asistido' ? 'moderado' : 'activo')
    }

    const fallbackUser = {
      id: 'usr-' + Date.now(),
      email: finalEmail,
      role: role || 'senior',
      profile: clinicalProfile
    }

    try {
      // Intentar registrar en backend con timeout de 3s
      await Promise.race([
        api.register(finalEmail, finalPassword, role, clinicalProfile),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout backend')), 3000))
      ])

      const user = await Promise.race([
        api.login(finalEmail, finalPassword),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout login')), 3000))
      ])

      if (user) {
        onAuthSuccess(user)
        return
      }
    } catch (err) {
      console.log('Registro completado localmente de forma inmediata:', err)
    }

    // Guardar sesión y activar usuario inmediatamente
    localStorage.setItem('sv_user', JSON.stringify(fallbackUser))
    localStorage.setItem('sv_token', 'token-reg-' + Date.now())
    onAuthSuccess(fallbackUser)
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-center items-center px-4 py-8 md:p-12 selection:bg-secondary-container">
      {/* Container Boutique */}
      <div className="w-full max-w-2xl bg-surface-container-lowest border-2 border-outline-variant rounded-3xl p-6 sm:p-10 shadow-soft-xl relative text-left">
        
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-secondary-container text-secondary mb-3 shadow-soft-sm border border-secondary/20">
            <span className="material-symbols-outlined text-4xl">health_and_safety</span>
          </div>
          <h1 className="text-headline-lg md:text-headline-xl font-extrabold text-primary tracking-tight">
            SeniorVital
          </h1>
          <p className="text-body-md text-on-surface-variant font-medium mt-1">
            Plataforma Inteligente de Bienestar Gerontológico
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-error-container text-on-error-container border border-error/30 text-body-sm font-semibold flex items-center gap-3">
            <span className="material-symbols-outlined text-2xl text-error">error</span>
            <span>{error}</span>
          </div>
        )}

        {/* VISTA 1: Bienvenida y Selección Rápida */}
        {mode === 'welcome' && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-headline-sm font-bold text-primary">
                Elige cómo deseas ingresar
              </h2>
              <p className="text-body-sm text-on-surface-variant mt-1">
                Accede rápidamente con una cuenta demostrativa o personaliza tu perfil.
              </p>
            </div>

            {/* Accesos Rápidos de Demostración */}
            <div className="space-y-3">
              <button
                onClick={() => handleDemoLogin('senior')}
                disabled={loading}
                className="w-full min-h-[64px] bg-secondary hover:bg-red-700 text-on-secondary font-bold text-lg rounded-2xl shadow-soft-md flex items-center justify-between px-6 transition-all active:scale-98"
              >
                <div className="flex items-center gap-4">
                  <span className="material-symbols-outlined text-3xl">elderly</span>
                  <div className="text-left">
                    <span className="block text-lg font-bold leading-tight">Ingresar como Adulto Mayor</span>
                    <span className="text-xs text-white/90 font-normal">Don Manuel Gómez (72 años)</span>
                  </div>
                </div>
                <span className="material-symbols-outlined text-2xl">arrow_forward</span>
              </button>

              <button
                onClick={() => handleDemoLogin('caregiver')}
                disabled={loading}
                className="w-full min-h-[64px] bg-surface-container hover:bg-surface-container-high text-primary border-2 border-outline-variant font-bold text-lg rounded-2xl flex items-center justify-between px-6 transition-all active:scale-98"
              >
                <div className="flex items-center gap-4">
                  <span className="material-symbols-outlined text-3xl text-secondary">family_restroom</span>
                  <div className="text-left">
                    <span className="block text-lg font-bold leading-tight">Modo Cuidador / Familiar</span>
                    <span className="text-xs text-on-surface-variant font-normal">Supervisión Remota Espejo</span>
                  </div>
                </div>
                <span className="material-symbols-outlined text-2xl text-on-surface-variant">arrow_forward</span>
              </button>

              <button
                onClick={() => handleDemoLogin('admin')}
                disabled={loading}
                className="w-full min-h-[64px] bg-surface-container hover:bg-surface-container-high text-primary border-2 border-outline-variant font-bold text-lg rounded-2xl flex items-center justify-between px-6 transition-all active:scale-98"
              >
                <div className="flex items-center gap-4">
                  <span className="material-symbols-outlined text-3xl text-tertiary">clinical_notes</span>
                  <div className="text-left">
                    <span className="block text-lg font-bold leading-tight">Panel Fisioterapeuta / Admin</span>
                    <span className="text-xs text-on-surface-variant font-normal">Semáforo Clínico y Overrides</span>
                  </div>
                </div>
                <span className="material-symbols-outlined text-2xl text-on-surface-variant">arrow_forward</span>
              </button>
            </div>

            <div className="pt-6 border-t border-outline-variant flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => { setMode('wizard'); setStep(1); }}
                className="flex-1 min-h-[52px] bg-tertiary text-on-tertiary font-bold text-base rounded-2xl hover:bg-sage-dark transition-colors flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined">person_add</span>
                <span>Nuevo Onboarding Clínico</span>
              </button>

              <button
                onClick={() => setMode('login')}
                className="flex-1 min-h-[52px] bg-surface-container text-primary border border-outline-variant font-bold text-base rounded-2xl hover:bg-surface-container-high transition-colors"
              >
                Iniciar Sesión con Correo
              </button>
            </div>
          </div>
        )}

        {/* VISTA 2: Login Convencional */}
        {mode === 'login' && (
          <form onSubmit={handleManualLogin} className="space-y-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-headline-sm font-bold text-primary">Inicia Sesión</h2>
              <button
                type="button"
                onClick={() => setMode('welcome')}
                className="text-sm font-bold text-secondary hover:underline"
              >
                Volver
              </button>
            </div>

            <div>
              <label className="block text-sm font-bold text-primary mb-2">Correo Electrónico</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ejemplo@seniorvital.com"
                className="w-full min-h-[56px] px-4 rounded-2xl border-2 border-outline-variant bg-surface text-lg text-primary focus:border-secondary focus:ring-2 focus:ring-secondary/20 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-primary mb-2">Contraseña</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full min-h-[56px] px-4 rounded-2xl border-2 border-outline-variant bg-surface text-lg text-primary focus:border-secondary focus:ring-2 focus:ring-secondary/20 outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full min-h-[56px] bg-secondary text-on-secondary font-bold text-lg rounded-2xl shadow-soft-md hover:bg-red-700 transition-all flex items-center justify-center gap-2"
            >
              {loading ? 'Ingresando...' : 'Acceder a SeniorVital'}
            </button>
          </form>
        )}

        {/* VISTA 3: Wizard de Onboarding Clínico (5 Pasos Guiados) */}
        {mode === 'wizard' && (
          <div>
            {/* Barra de Progreso del Wizard */}
            <div className="mb-6">
              <div className="flex justify-between items-center text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">
                <span>Paso {step} de 5</span>
                <span className="text-secondary">
                  {step === 1 && 'Identificación'}
                  {step === 2 && 'Rango de Edad'}
                  {step === 3 && 'Nivel de Movilidad'}
                  {step === 4 && 'Restricciones de Salud'}
                  {step === 5 && 'Objetivos de Bienestar'}
                </span>
              </div>
              <div className="w-full bg-surface-container h-2.5 rounded-full overflow-hidden">
                <div 
                  className="bg-secondary h-full transition-all duration-300 rounded-full"
                  style={{ width: `${(step / 5) * 100}%` }}
                />
              </div>
            </div>

            {/* PASO 1: Identificación y Rol */}
            {step === 1 && (
              <div className="space-y-4 animate-fade-in">
                <h2 className="text-headline-sm font-bold text-primary">¿Cómo te llamas y cuál es tu rol?</h2>
                <div>
                  <label className="block text-sm font-bold text-primary mb-1">Nombre Completo</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ej. Manuel Gómez"
                    className="w-full min-h-[56px] px-4 rounded-2xl border-2 border-outline-variant bg-surface text-lg text-primary focus:border-secondary outline-none mb-3"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-primary mb-1">Correo Electrónico</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="tu@correo.com"
                    className="w-full min-h-[56px] px-4 rounded-2xl border-2 border-outline-variant bg-surface text-lg text-primary focus:border-secondary outline-none mb-3"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-primary mb-1">Contraseña</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Al menos 6 caracteres"
                    className="w-full min-h-[56px] px-4 rounded-2xl border-2 border-outline-variant bg-surface text-lg text-primary focus:border-secondary outline-none mb-4"
                  />
                </div>

                <label className="block text-sm font-bold text-primary mb-2">Rol Principal</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'senior', label: 'Adulto Mayor', icon: 'elderly' },
                    { id: 'caregiver', label: 'Cuidador', icon: 'family_restroom' },
                    { id: 'admin', label: 'Fisioterapeuta', icon: 'medical_services' }
                  ].map(r => (
                    <button
                      key={r.id}
                      type="button"
                      onClick={() => setRole(r.id)}
                      className={`min-h-[56px] p-3 rounded-2xl border-2 font-bold text-sm flex flex-col items-center justify-center gap-1 transition-all ${
                        role === r.id 
                          ? 'border-secondary bg-secondary-container text-on-secondary-container' 
                          : 'border-outline-variant bg-surface text-on-surface-variant'
                      }`}
                    >
                      <span className="material-symbols-outlined text-2xl">{r.icon}</span>
                      <span>{r.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* PASO 2: Rango de Edad */}
            {step === 2 && (
              <div className="space-y-4 animate-fade-in">
                <h2 className="text-headline-sm font-bold text-primary">Selecciona tu grupo de edad</h2>
                <p className="text-body-sm text-on-surface-variant">Nos ayuda a calibrar la intensidad de los ejercicios.</p>
                <div className="space-y-3 pt-2">
                  {[
                    { id: '60-69', label: '60 a 69 años', desc: 'Etapa de mantenimiento activo' },
                    { id: '70-79', label: '70 a 79 años', desc: 'Enfoque en estabilidad y fuerza funcional' },
                    { id: '80+', label: '80 años o más', desc: 'Prioridad en movilidad suave y equilibrio' }
                  ].map(age => (
                    <button
                      key={age.id}
                      type="button"
                      onClick={() => setAgeRange(age.id)}
                      className={`w-full min-h-[64px] p-4 rounded-2xl border-2 text-left flex items-center justify-between transition-all ${
                        ageRange === age.id
                          ? 'border-secondary bg-secondary-container text-primary font-bold shadow-soft-sm'
                          : 'border-outline-variant bg-surface hover:bg-surface-container'
                      }`}
                    >
                      <div>
                        <span className="block text-lg font-bold text-primary">{age.label}</span>
                        <span className="text-xs text-on-surface-variant font-medium">{age.desc}</span>
                      </div>
                      <span className="material-symbols-outlined text-2xl text-secondary">
                        {ageRange === age.id ? 'check_circle' : 'radio_button_unchecked'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* PASO 3: Nivel de Movilidad */}
            {step === 3 && (
              <div className="space-y-4 animate-fade-in">
                <h2 className="text-headline-sm font-bold text-primary">¿Cuál describe mejor tu movilidad hoy?</h2>
                <div className="space-y-3 pt-2">
                  {mobilityOptions.map(m => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setMobilityLevel(m.id)}
                      className={`w-full min-h-[72px] p-4 rounded-2xl border-2 text-left flex items-center gap-4 transition-all ${
                        mobilityLevel === m.id
                          ? 'border-secondary bg-secondary-container shadow-soft-sm'
                          : 'border-outline-variant bg-surface hover:bg-surface-container'
                      }`}
                    >
                      <div className="w-12 h-12 rounded-xl bg-surface flex items-center justify-center text-secondary shrink-0 shadow-soft-sm">
                        <span className="material-symbols-outlined text-3xl">{m.icon}</span>
                      </div>
                      <div className="flex-1">
                        <span className="block text-lg font-bold text-primary">{m.title}</span>
                        <span className="text-xs text-on-surface-variant font-medium">{m.description}</span>
                      </div>
                      <span className="material-symbols-outlined text-2xl text-secondary">
                        {mobilityLevel === m.id ? 'check_circle' : 'radio_button_unchecked'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* PASO 4: Restricciones Médicas */}
            {step === 4 && (
              <div className="space-y-4 animate-fade-in">
                <h2 className="text-headline-sm font-bold text-primary">Restricciones Médicas y Articulares</h2>
                <p className="text-body-sm text-on-surface-variant">El Agente Wellness IA adaptará los movimientos para protegerte.</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                  {restrictionOptions.map(r => {
                    const isSelected = restrictions.includes(r.id)
                    return (
                      <button
                        key={r.id}
                        type="button"
                        onClick={() => toggleRestriction(r.id)}
                        className={`min-h-[60px] p-4 rounded-2xl border-2 text-left flex items-center justify-between transition-all ${
                          isSelected
                            ? 'border-tertiary bg-tertiary-container font-bold text-primary shadow-soft-sm'
                            : 'border-outline-variant bg-surface hover:bg-surface-container'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="material-symbols-outlined text-2xl text-tertiary">{r.icon}</span>
                          <span className="text-base font-bold text-primary">{r.label}</span>
                        </div>
                        <span className="material-symbols-outlined text-xl text-tertiary">
                          {isSelected ? 'check_box' : 'check_box_outline_blank'}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* PASO 5: Objetivos de Bienestar */}
            {step === 5 && (
              <div className="space-y-4 animate-fade-in">
                <h2 className="text-headline-sm font-bold text-primary">¿Qué meta te gustaría alcanzar?</h2>
                <div className="space-y-3 pt-2">
                  {goalOptions.map(g => {
                    const isSelected = goals.includes(g.id)
                    return (
                      <button
                        key={g.id}
                        type="button"
                        onClick={() => toggleGoal(g.id)}
                        className={`w-full min-h-[64px] p-4 rounded-2xl border-2 text-left flex items-center gap-4 transition-all ${
                          isSelected
                            ? 'border-secondary bg-secondary-container shadow-soft-sm'
                            : 'border-outline-variant bg-surface hover:bg-surface-container'
                        }`}
                      >
                        <div className="w-10 h-10 rounded-xl bg-surface flex items-center justify-center text-secondary shrink-0">
                          <span className="material-symbols-outlined text-2xl">{g.icon}</span>
                        </div>
                        <div className="flex-1">
                          <span className="block text-base font-bold text-primary">{g.title}</span>
                          <span className="text-xs text-on-surface-variant">{g.desc}</span>
                        </div>
                        <span className="material-symbols-outlined text-xl text-secondary">
                          {isSelected ? 'check_box' : 'check_box_outline_blank'}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Botones de Navegación del Wizard */}
            <div className="pt-6 mt-6 border-t border-outline-variant flex justify-between gap-3">
              <button
                type="button"
                onClick={() => {
                  if (step === 1) setMode('welcome')
                  else setStep(step - 1)
                }}
                className="min-h-[52px] px-6 rounded-2xl border-2 border-outline-variant bg-surface hover:bg-surface-container font-bold text-primary transition-colors"
              >
                Atrás
              </button>

              {step < 5 ? (
                <button
                  type="button"
                  onClick={() => setStep(step + 1)}
                  className="min-h-[52px] px-8 rounded-2xl bg-secondary text-on-secondary font-bold text-base hover:bg-red-700 transition-all flex items-center gap-2 shadow-soft-sm"
                >
                  <span>Siguiente</span>
                  <span className="material-symbols-outlined">arrow_forward</span>
                </button>
              ) : (
                <button
                  type="button"
                  disabled={loading}
                  onClick={handleFinishWizard}
                  className="min-h-[52px] px-8 rounded-2xl bg-tertiary text-on-tertiary font-bold text-base hover:bg-sage-dark transition-all flex items-center gap-2 shadow-soft-sm"
                >
                  <span className="material-symbols-outlined">check_circle</span>
                  <span>{loading ? 'Preparando...' : 'Comenzar Mi Plan'}</span>
                </button>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
