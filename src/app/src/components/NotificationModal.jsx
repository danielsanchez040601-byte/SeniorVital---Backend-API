import React from 'react'

export default function NotificationModal({ isOpen, onClose }) {
  if (!isOpen) return null

  const notifications = [
    {
      id: 1,
      type: 'hydration',
      icon: 'water_drop',
      title: 'Momento de hidratarte con calma',
      message: 'Un vaso de agua fresca ahora mantendrá tus articulaciones y energía al máximo.',
      time: 'Hace 25 min',
      color: 'bg-blue-50 text-blue-800 border-blue-200'
    },
    {
      id: 2,
      type: 'workout',
      icon: 'self_improvement',
      title: 'Tu cuerpo agradece tu constancia',
      message: 'Completaste tu sesión de movilidad suave. ¡Gran paso para tu vitalidad de hoy!',
      time: 'Hoy, 10:15 AM',
      color: 'bg-sage-light text-sage-dark border-sage/30'
    },
    {
      id: 3,
      type: 'tip',
      icon: 'sunny',
      title: 'Consejo del Agente Wellness',
      message: 'Si sientes ligera pesadez en las piernas, unos estiramientos sentado te brindarán alivio inmediato.',
      time: 'Ayer',
      color: 'bg-secondary-container text-on-secondary-container border-secondary/20'
    }
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/60 backdrop-blur-sm animate-fade-in">
      <div 
        className="w-full max-w-lg bg-surface border-2 border-outline-variant rounded-3xl p-6 md:p-8 shadow-soft-xl max-h-[90vh] flex flex-col text-left"
        role="dialog"
        aria-modal="true"
        aria-labelledby="notifications-title"
      >
        <div className="flex items-center justify-between pb-4 border-b border-outline-variant mb-4">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-secondary text-3xl">notifications_active</span>
            <h2 id="notifications-title" className="text-headline-sm font-bold text-primary">
              Buzón de Bienestar
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-12 h-12 flex items-center justify-center rounded-full hover:bg-surface-container text-on-surface-variant transition-colors"
            aria-label="Cerrar notificaciones"
          >
            <span className="material-symbols-outlined text-2xl">close</span>
          </button>
        </div>

        <div className="overflow-y-auto space-y-4 pr-1 flex-1">
          {notifications.map((item) => (
            <div 
              key={item.id}
              className={`p-4 rounded-2xl border-2 flex gap-4 items-start ${item.color}`}
            >
              <div className="w-12 h-12 rounded-xl bg-surface flex items-center justify-center shrink-0 shadow-soft-sm">
                <span className="material-symbols-outlined text-2xl">{item.icon}</span>
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start mb-1">
                  <h3 className="font-bold text-body-md text-primary">{item.title}</h3>
                  <span className="text-xs text-on-surface-variant font-medium">{item.time}</span>
                </div>
                <p className="text-body-sm text-on-surface-variant leading-relaxed">
                  {item.message}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="pt-4 mt-2 border-t border-outline-variant">
          <button
            onClick={onClose}
            className="w-full min-h-[52px] bg-primary text-on-primary font-bold text-base rounded-2xl shadow-soft-sm hover:bg-primary-container transition-colors"
          >
            Aceptar y Continuar
          </button>
        </div>
      </div>
    </div>
  )
}
