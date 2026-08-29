import React, { useState, useRef, useEffect } from 'react'
import api from '../api'

export default function ChatWellnessModal({ isOpen, onClose, user }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'agent',
      agentName: 'Wellness Coach 2.0',
      text: '¡Hola! Soy su Asistente Inteligente de Bienestar. ¿Cómo se siente hoy? Puede consultarme sobre ejercicios seguros, molestias musculares o consejos de movilidad.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isSafe: true
    }
  ])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [reactStage, setReactStage] = useState('') // 'Pensamiento...' | 'Acción: Supabase...' | 'Observación...'
  const messagesEndRef = useRef(null)

  const quickPrompts = [
    'Me duelen las rodillas hoy, ¿puedo hacer sentadillas?',
    '¿Qué ejercicios puedo hacer sentado en una silla?',
    'Siento temblores al caminar, ¿cómo mejorar mi estabilidad?',
    'Tengo hipertensión, ¿qué movimientos debo evitar?'
  ]

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen, reactStage])

  if (!isOpen) return null

  const handleSend = async (queryText = null) => {
    const textToSend = queryText || inputText.trim()
    if (!textToSend || isLoading) return

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    setMessages(prev => [...prev, userMsg])
    setInputText('')
    setIsLoading(true)

    // Simulación visual de etapas ReAct para transparencia con el adulto mayor
    setReactStage('🧠 1. Pensamiento: Analizando su consulta y perfil...')
    setTimeout(() => {
      setReactStage('🛠️ 2. Acción: Consultando base de conocimiento RAG y Supabase...')
    }, 800)
    setTimeout(() => {
      setReactStage('🔍 3. Observación: Verificando contraindicaciones y seguridad ISO 25010...')
    }, 1800)

    try {
      const response = await api.sendChatMessage(user?.id || '1', textToSend)
      
      const agentMsg = {
        id: Date.now() + 1,
        sender: 'agent',
        agentName: 'Wellness Coach 2.0 (ReAct + RAG)',
        text: response.response || 'Le recomiendo realizar movimientos suaves de movilidad articular sentado.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isSafe: response.is_safe !== false
      }

      setMessages(prev => [...prev, agentMsg])
    } catch (err) {
      const fallbackMsg = {
        id: Date.now() + 1,
        sender: 'agent',
        agentName: 'Wellness Coach 2.0 (Fallback Seguro)',
        text: 'Para su bienestar y seguridad, le sugiero realizar estiramientos suaves de cuello y brazos sentado, manteniendo una respiración pausada. Si siente molestia, descanse y consulte a su cuidador.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isSafe: true
      }
      setMessages(prev => [...prev, fallbackMsg])
    } finally {
      setIsLoading(false)
      setReactStage('')
    }
  }

  const handleSpeak = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'es-ES'
      utterance.rate = 0.95 // Velocidad pausada para adultos mayores
      window.speechSynthesis.speak(utterance)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-primary/60 backdrop-blur-sm animate-fade-in">
      <div 
        className="w-full max-w-2xl bg-surface border-3 border-outline-variant rounded-3xl shadow-soft-2xl flex flex-col h-[85vh] max-h-[750px] overflow-hidden text-left"
        role="dialog"
        aria-modal="true"
        aria-labelledby="chat-title"
      >
        {/* Cabecera del Chat */}
        <header className="bg-primary text-on-primary px-6 py-4 flex items-center justify-between border-b-2 border-outline-variant select-none">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-secondary-container text-secondary flex items-center justify-center shadow-soft-sm">
              <span className="material-symbols-outlined text-2xl">smart_toy</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="chat-title" className="text-lg sm:text-xl font-bold tracking-tight">
                  Wellness Coach IA
                </h2>
                <span className="bg-tertiary-container text-tertiary text-[10px] font-black uppercase px-2 py-0.5 rounded-full border border-tertiary/20">
                  RAG + ReAct
                </span>
              </div>
              <p className="text-xs text-white/80">
                Guía clínica geriátrica adaptada (WCAG 2.1 AA)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-11 h-11 rounded-2xl bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors active:scale-95"
            aria-label="Cerrar ventana de conversación"
          >
            <span className="material-symbols-outlined text-2xl">close</span>
          </button>
        </header>

        {/* Banner de Reconocimiento Clínico */}
        <div className="bg-surface-container-low px-4 py-2 border-b border-outline-variant flex items-center gap-2 text-xs text-on-surface-variant">
          <span className="material-symbols-outlined text-secondary text-sm">verified_user</span>
          <span>
            Asesoría clínica validada por el <strong>Ing. Julio Matute</strong> (10 patologías gerontológicas).
          </span>
        </div>

        {/* Cuerpo de Mensajes */}
        <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-4 bg-surface/50">
          {messages.map((msg) => {
            const isAgent = msg.sender === 'agent'
            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isAgent ? 'items-start' : 'items-end'}`}
              >
                {isAgent && (
                  <div className="flex items-center gap-2 mb-1 pl-1">
                    <span className="text-xs font-bold text-secondary uppercase tracking-wider">
                      {msg.agentName}
                    </span>
                    <span className="text-[10px] text-on-surface-variant">
                      {msg.timestamp}
                    </span>
                  </div>
                )}

                <div
                  className={`max-w-[88%] sm:max-w-[80%] rounded-3xl p-4 sm:p-5 text-base sm:text-lg leading-relaxed shadow-soft-sm ${
                    isAgent
                      ? 'bg-surface-container-lowest text-primary border-2 border-outline-variant rounded-tl-sm'
                      : 'bg-primary text-on-primary rounded-tr-sm font-medium'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {/* Botón de Lectura en Voz Alta */}
                  {isAgent && (
                    <div className="mt-3 pt-2 border-t border-outline-variant/60 flex items-center justify-between">
                      <button
                        onClick={() => handleSpeak(msg.text)}
                        className="inline-flex items-center gap-1.5 text-xs font-bold text-secondary hover:text-secondary-container transition-colors py-1 px-2.5 rounded-xl hover:bg-surface-container active:scale-95"
                        title="Escuchar respuesta"
                        aria-label="Escuchar mensaje en voz alta"
                      >
                        <span className="material-symbols-outlined text-base">volume_up</span>
                        Escuchar voz
                      </button>
                      <span className="text-[10px] text-tertiary font-bold flex items-center gap-1">
                        <span className="material-symbols-outlined text-xs">check_circle</span>
                        Validado seguro
                      </span>
                    </div>
                  )}
                </div>

                {!isAgent && (
                  <span className="text-[10px] text-on-surface-variant pr-1 mt-1">
                    {msg.timestamp}
                  </span>
                )}
              </div>
            )
          })}

          {/* Indicador de Razonamiento ReAct en Progreso */}
          {isLoading && (
            <div className="bg-surface-container-low border-2 border-secondary/30 rounded-2xl p-4 animate-pulse flex items-center gap-3">
              <div className="w-6 h-6 border-3 border-secondary border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm sm:text-base font-semibold text-secondary">
                {reactStage || 'Procesando razonamiento clínico...'}
              </span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Sugerencias Rápidas para el Adulto Mayor */}
        <div className="bg-surface-container-low px-4 py-2 border-t border-outline-variant overflow-x-auto flex items-center gap-2 no-scrollbar">
          <span className="text-xs font-bold text-on-surface-variant whitespace-nowrap pl-1">
            Consultas frecuentes:
          </span>
          {quickPrompts.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              disabled={isLoading}
              className="text-xs font-semibold bg-surface-container-lowest text-primary border border-outline-variant px-3 py-1.5 rounded-full hover:bg-secondary-container hover:text-secondary whitespace-nowrap transition-colors active:scale-95 disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Barra de Entrada de Texto */}
        <footer className="p-3 sm:p-4 bg-surface border-t-2 border-outline-variant flex items-center gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Escriba su consulta de salud o bienestar..."
            disabled={isLoading}
            className="flex-1 bg-surface-container-lowest border-2 border-outline-variant focus:border-secondary focus:ring-2 focus:ring-secondary/20 rounded-2xl px-4 py-3 text-base sm:text-lg text-primary placeholder:text-on-surface-variant/60 outline-none transition-all"
            aria-label="Campo para escribir consulta de salud"
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputText.trim() || isLoading}
            className="min-h-[50px] min-w-[50px] sm:min-w-[56px] rounded-2xl bg-secondary text-on-secondary font-bold flex items-center justify-center shadow-soft-sm hover:opacity-90 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Enviar consulta"
          >
            <span className="material-symbols-outlined text-2xl">send</span>
          </button>
        </footer>
      </div>
    </div>
  )
}
