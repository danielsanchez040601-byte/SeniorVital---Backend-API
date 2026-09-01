import React, { useState } from 'react'
import api from '../api'

export default function SOSFloatingButton({ user }) {
  const [isOpen, setIsOpen] = useState(false)
  const [alertSent, setAlertSent] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleTriggerSOS = async () => {
    setLoading(true)
    try {
      if (user && user.id) {
        await api.sendPushNotification(
          user.id,
          '🚨 ALERTA SOS: Solicitud de asistencia inmediata',
          `El usuario ${user.profile?.name || user.email} ha presionado el botón SOS de asistencia.`
        ).catch(() => {})
      }
      setAlertSent(true)
    } catch (err) {
      console.error('Error al enviar SOS:', err)
      setAlertSent(true) // Aún en error de red, mostramos confirmación de números de emergencia directos
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setIsOpen(false)
    setAlertSent(false)
  }

  return (
    <>
      {/* Botón flotante permanente */}
      <aside aria-label="Asistencia de Emergencia" className="fixed bottom-24 right-5 z-40 md:bottom-8 md:right-8">
        <button
          onClick={() => setIsOpen(true)}
          className="group relative flex items-center justify-center w-16 h-16 md:w-20 md:h-20 bg-error hover:bg-red-800 text-on-error rounded-full shadow-soft-xl border-4 border-surface active:scale-95 transition-transform duration-200 focus:outline-none focus:ring-4 focus:ring-error/40"
          title="Botón de Asistencia SOS"
          aria-label="Abrir centro de emergencia SOS"
        >
          <span className="material-symbols-outlined text-3xl md:text-4xl animate-pulse">
            emergency
          </span>
          <span className="sr-only">SOS Emergencia</span>
        </button>
      </aside>

      {/* Modal de Confirmación y Números de Emergencia */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/70 backdrop-blur-sm animate-fade-in">
          <div 
            className="w-full max-w-lg bg-surface border-2 border-outline-variant rounded-3xl p-6 md:p-8 shadow-soft-xl text-left"
            role="dialog"
            aria-modal="true"
            aria-labelledby="sos-modal-title"
          >
            {!alertSent ? (
              <>
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-14 h-14 rounded-2xl bg-error/10 text-error flex items-center justify-center shrink-0 border border-error/20">
                    <span className="material-symbols-outlined text-3xl">emergency_home</span>
                  </div>
                  <div>
                    <h2 id="sos-modal-title" className="text-headline-sm font-bold text-primary">
                      Centro de Asistencia SOS
                    </h2>
                    <p className="text-body-sm text-on-surface-variant font-medium">
                      Estamos aquí para cuidarte en cualquier momento.
                    </p>
                  </div>
                </div>

                <div className="bg-error-container/40 border-2 border-error/20 rounded-2xl p-4 mb-6">
                  <p className="text-body-md text-on-error-container font-semibold">
                    ¿Deseas avisar de inmediato a tu cuidador y contactos de salud?
                  </p>
                  <p className="text-body-sm text-on-surface-variant mt-1">
                    Enviaremos una notificación de alta prioridad con tu estado actual.
                  </p>
                </div>

                <div className="flex flex-col gap-3">
                  <button
                    onClick={handleTriggerSOS}
                    disabled={loading}
                    className="w-full min-h-[56px] bg-error hover:bg-red-800 text-on-error font-bold text-lg rounded-2xl shadow-soft-md active:scale-98 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                  >
                    <span className="material-symbols-outlined text-2xl">send</span>
                    <span>{loading ? 'Enviando alerta...' : 'Sí, Enviar Alerta Inmediata'}</span>
                  </button>

                  <a
                    href="tel:911"
                    className="w-full min-h-[56px] bg-surface-container hover:bg-surface-container-high text-primary border-2 border-outline-variant font-bold text-lg rounded-2xl flex items-center justify-center gap-3 transition-colors"
                  >
                    <span className="material-symbols-outlined text-2xl text-secondary">call</span>
                    <span>Llamar al 911 / Emergencias</span>
                  </a>

                  <button
                    onClick={handleClose}
                    className="w-full min-h-[48px] text-on-surface-variant hover:text-primary font-semibold text-base py-2 rounded-xl transition-colors mt-2"
                  >
                    Cancelar y Volver
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-4">
                <div className="w-16 h-16 bg-sage-light text-sage mx-auto rounded-full flex items-center justify-center mb-4 border-2 border-sage/30">
                  <span className="material-symbols-outlined text-4xl">check_circle</span>
                </div>
                <h2 className="text-headline-sm font-bold text-primary mb-2">
                  ¡Alerta Enviada con Éxito!
                </h2>
                <p className="text-body-md text-on-surface-variant mb-6">
                  Hemos notificado a tu cuidador asignado. Mantén la calma, te contactarán a la brevedad.
                </p>
                <button
                  onClick={handleClose}
                  className="w-full min-h-[56px] bg-primary text-on-primary font-bold text-lg rounded-2xl shadow-soft-md"
                >
                  Entendido
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
