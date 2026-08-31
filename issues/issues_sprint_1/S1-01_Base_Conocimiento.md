# 📚 Issue S1-01: Ingeniería del Conocimiento y Ontología Médica Geriátrica

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Ecosistema Inteligente de Salud Gerontológica  
**Sprint Técnico:** Sprint 1 — Ingeniería del Conocimiento y Sistemas RAG  

---

## 🎯 1. Objetivo del Issue
Estructurar y formalizar la **Base de Conocimiento Clínico y Gerontológico** a partir del informe médico maestro `Informe_Clinico_SeniorVital`, estableciendo una ontología estructurada de las 10 patologías y afecciones limitantes de mayor prevalencia en adultos mayores de 60 años para su ingesta en el sistema RAG (*Retrieval-Augmented Generation*).

---

## 🏥 2. Catálogo de Patologías y Reglas Clínicas

| # | Patología / Condición | Limitaciones Biomecánicas | Plan de Movimiento Recomendado | Contraindicaciones Estrictas (Filtros Duros) |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Osteoartritis (OA) de Rodilla y Cadera** | Dolor nociceptivo compresivo, rigidez matutina, inhibición artrogénica del cuádriceps. | Cadena cinética cerrada de bajo ángulo (sentadilla parcial asistida), ciclismo estático, natación. | Prohibido: pliometría (saltos), flexión de rodilla $>90^\circ$ sin apoyo, torsiones axiales. |
| **2** | **Sarcopenia (Dinapenia)** | Pérdida de fuerza de prensión, lentitud de marcha ($<0.8\text{ m/s}$), miosteatosis. | Entrenamiento de Fuerza Progresiva (PRT) al 40-80% 1-RM, bandas elásticas, calistenia adaptada. | Prohibido: reposo prolongado, aeróbico exclusivo de baja intensidad (no genera hipertrofia). |
| **3** | **Insuficiencia Cardíaca Crónica (ICC)** | Astenia, disnea paroxística, hipoperfusión cerebral y congestión vascular. | Actividad rítmica continua (Borg 11-12), entrenamiento de musculatura inspiratoria (PImax). | Prohibido: ejercicio con aumento de peso $>1.8\text{ kg}$ en 3 días, disnea en reposo, angina inestable. |
| **4** | **Enfermedad de Parkinson** | Bradicinesia, temblor de reposo, rigidez axial, episodios de congelamiento (*Freezing*). | Baile/Tango adaptado, Tai Chi, pistas auditivas rítmicas externas (metrónomo), fases "ON". | Prohibido: cintas rodantes sin arnés de seguridad, doble tarea motora compleja en etapas avanzadas. |
| **5** | **Diabetes Mellitus Tipo 2 (DMT2)** | Neuropatía sensitivo-motora distal, riesgo de hipoglucemia e hipotensión ortostática. | Dosis 150-300 min/sem (no pasar $>48\text{h}$ sin ejercicio), fortalecimiento multiarticular. | Prohibido: inicio si glucemia $>300\text{ mg/dL}$ o $<100\text{ mg/dL}$, Valsalva si hay retinopatía. |
| **6** | **Demencias y Alzheimer** | Pérdida de funciones ejecutivas, desorientación espacial, apraxia ideomotora. | Rutinas automatizadas de muy baja complejidad (Nivel 1-2), protocolo RDAD, horario fijo. | Prohibido: coreografías complejas, cambios imprevistos de secuencia, caminatas peripatéticas no cercadas. |
| **7** | **EPOC** | Atrapamiento aéreo dinámico, disnea incapacitante, debilidad de cuádriceps. | Entrenamiento por intervalos cortos de alta intensidad relativa con descanso activo, labios fruncidos. | Prohibido: actividad durante exacerbaciones infecciosas, caídas de $\text{SpO}_2 < 88\%$, sibilancias. |
| **8** | **Accidente Cerebrovascular (ACV)** | Hemiparesia, espasticidad piramidal, negligencia espacial, riesgo de subluxación. | Entrenamiento orientado a tareas, cicloergómetros de doble acoplamiento, órtesis AFO. | Prohibido: cargas pesadas asimétricas en miembro hemipléjico que aumenten patrón flexor. |
| **9** | **Cardiopatía Isquémica** | Umbral miocárdico hipóxico, crisis anginosas al sobrepasar umbral de FC. | FC de entrenamiento fijada a $10\text{-}15\text{ lpm}$ por debajo del umbral isquémico comprobado. | Prohibido: ejercicio ante angina inestable de progresión reciente o estenosis aórtica severa. |
| **10** | **Osteoporosis y Fragilidad Ósea** | Pérdida de densidad mineral ósea (DMO), hipercifosis, riesgo de aplastamiento. | Protocolo HiRIT/LIFTMOR supervisado (80-85% 1-RM), Tai Chi para equilibrio, postura recta. | Prohibido: flexión espinal forzada con carga (abdominales crunch), torsiones violentas de tronco. |

---

## 📑 3. Bibliografía y Reconocimiento de Asesoría Médica

> ### 🌟 Reconocimiento Especial Obligatorio:
> **Reconocimiento especial al Ing. Julio Matute por su asesoría técnica y clínica en la validación de patologías, afecciones y enfermedades limitantes en adultos mayores, las cuales fundamentan esta base de conocimiento.**

### Referencias Bibliográficas Principales (Formato APA 7ma Edición):
1. **OARSI Guidelines (2019):** Bannuru, R. R., et al. *OARSI guidelines for the non-surgical management of knee, hip, and polyarticular osteoarthritis.* Osteoarthritis and Cartilage, 27(11), 1578-1589.
2. **EWGSOP2 Sarcopenia Consensus (2019):** Cruz-Jentoft, A. J., et al. *Sarcopenia: revised European consensus on definition and diagnosis.* Age and Ageing, 48(1), 16-31.
3. **ESC Heart Failure Guidelines (2021):** McDonagh, T. A., et al. *2021 ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure.* European Heart Journal, 42(36), 3599-3726.
4. **APTA Parkinson's Disease Guidelines (2022):** Osborne, J. A., et al. *Physical Therapist Management of Parkinson Disease.* Physical Therapy, 102(4), pzab302.
5. **ADA Standards of Medical Care (2024):** American Diabetes Association. *Physical Activity/Exercise and Diabetes.* Diabetes Care, 39(11), 2065-2079.
6. **LIFTMOR Osteoporosis Trial (2018):** Watson, S. L., et al. *High-intensity resistance and impact training improves bone mineral density in postmenopausal women: the LIFTMOR randomized controlled trial.* JBMR, 33(2), 211-220.
7. **ATS/ERS Pulmonary Rehabilitation (2013):** Spruit, M. A., et al. *An official American Thoracic Society/European Respiratory Society statement.* AJRCCM, 188(8), e13-e64.
8. **AHA/ASA Stroke Physical Activity (2014):** Billinger, S. A., et al. *Physical activity and exercise recommendations for stroke survivors.* Stroke, 45(8), 2532-2553.
