# Informe Clínico Maestro: SeniorVital
## Protocolos de Geriatría y Fisioterapia para Sistemas de Inteligencia Artificial

---

## 1. Introducción: Importancia de la Movilidad en el Adulto Mayor

La convergencia entre la ciencia de datos, la geriatría y la fisioterapia representa un cambio de paradigma en el abordaje del envejecimiento poblacional. Según el estudio Global Burden of Disease (GBD) 2021, las caídas constituyen una emergencia de salud pública geriátrica, con una tasa de incidencia de 6,198.42 por cada 100,000 habitantes. La Organización Panamericana de la Salud (OPS) proyecta que las necesidades de cuidado a largo plazo en América Latina se triplicarán para 2050, alcanzando los 30 millones de adultos mayores dependientes [3, 4].

La movilidad y el ejercicio terapéutico estructurado son intervenciones fundamentales para mitigar estas métricas, revirtiendo la fragilidad y preservando la autonomía. En este contexto, el proyecto **SeniorVital** emplea Generación Aumentada por Recuperación (RAG) para proporcionar recomendaciones de bienestar. Sin embargo, para garantizar la seguridad del adulto mayor, es innegociable que los algoritmos de IA estén subordinados a **filtros duros deterministas (Guardrails)** que impidan la prescripción de movimientos biomecánicamente peligrosos. Este informe consolida la evidencia clínica y los límites de seguridad (Contraindicaciones Estrictas) para las 10 patologías limitantes más comunes, estructurando el conocimiento para su ingesta en sistemas de razonamiento algorítmico [1, 5, 6].

---

## 2. Catálogo de Condiciones Clínicas Limitantes

### 2.1. Osteoartritis (OA) de Rodilla y Cadera
* **Limitaciones**: Dolor nociceptivo mecánico desencadenado por la compresión articular, rigidez matutina prolongada, inhibición muscular artrogénica adaptativa (reducción del reclutamiento del cuádriceps que perpetúa la inestabilidad) y kinesiofobia reactiva [7].
* **Plan de Movimiento (Evidencia)**:
  * **Fuerza**: Intervención en el reclutamiento del cuádriceps, glúteos e isquiotibiales mediante ejercicios de cadena cinética cerrada de bajo ángulo (sentadillas parciales asistidas, prensa asistida o isométricos) [7, 29, 32].
  * **Aeróbico/Flexibilidad**: Movimientos cíclicos que minimicen fuerzas de cizallamiento (ciclismo estacionario, natación, hidroterapia). Flexibilidad diaria de isquiotibiales y psoas [7].
* **Recomendaciones de Estilo de Vida**: Intervención dietética para reducción de peso (5-7.5%). Por cada 1 kg de peso perdido, se reducen 4 kg de fuerza compresiva en la rodilla [7, 30]. Uso de bastones calibrados, calzado amortiguador y técnicas de conservación de energía.
* **Contraindicaciones Estrictas**: Queda estrictamente prohibida la prescripción de ejercicios que incluyan pliometría (saltos), impactos balísticos continuos sobre superficies duras, posturas de torsión extrema bajo carga y flexión profunda de rodilla (>90 grados) sin soporte estructural, por riesgo de fisura meniscal [7, 30].

### 2.2. Sarcopenia (Falla Muscular Primaria y Secundaria)
* **Limitaciones**: Dinapenia (marcada reducción de la fuerza de prensión palmar), lentitud en la velocidad de marcha (< 0.8 m/s), infiltración grasa intramuscular (miosteatosis) y grave dificultad mecánica para efectuar transiciones como levantarse de una silla sin apoyo [9, 10, 34].
* **Plan de Movimiento (Evidencia)**:
  * **Fuerza**: Entrenamiento de Fuerza Progresiva (PRT) obligatorio (2-3 días/semana al 40-80% de 1-RM) usando bandas elásticas, pesos libres ligeros o calistenia geriátrica simplificada para estimular fibras musculares Tipo II de contracción rápida [9, 10].
  * **Aeróbico/Potencia**: Ejercicios multicomponente que incluyan balance inestable (ej. programa Otago) y entrenamiento de la fase concéntrica a máxima velocidad para ganar fuerza explosiva anticaídas [9].
* **Recomendaciones de Estilo de Vida**: Incremento de la ingesta proteica (1.2 a 1.5 g/kg/día rica en aminoácidos esenciales como leucina, salvo contraindicación renal) para revertir la resistencia anabólica. Monitorización de vitamina D [9, 10, 34].
* **Contraindicaciones Estrictas**: El reposo prolongado está terminantemente desaconsejado. La prescripción aislada de ejercicio aeróbico de baja intensidad como única modalidad de entrenamiento se considera una negligencia terapéutica, ya que no produce hipertrofia celular satélite [9]. Se deben bloquear cargas pesadas ante dolor osteoarticular agudo o fracturas recientes.

### 2.3. Insuficiencia Cardíaca Crónica (ICC - HFrEF / HFpEF)
* **Limitaciones**: Astenia (fatiga generalizada), disnea paroxística, originadas por disfunción endotelial periférica y congestión vascular pulmonar. Déficits sutiles de atención y memoria por hipoperfusión cerebral crónica [12, 13, 14, 35].
* **Plan de Movimiento (Evidencia)**:
  * **Aeróbico**: Actividad rítmica continua (40-50% VO2R o RPE de Borg 11-12 inicial, progresando a 70-80% en pacientes de bajo riesgo). Entrenamiento por intervalos HIIT (80-90%) solo en pacientes muy estables [13, 35].
  * **Fuerza y Respiratorio**: Intensidades ligeras (<30% 1-RM) incrementando paulatinamente. Entrenamiento de músculos inspiratorios (PImax) de 5 a 7 días/semana para mitigar disnea [13].
* **Recomendaciones de Estilo de Vida**: Restricción estricta de sodio (<1500 mg/día) y monitorización rigurosa del peso corporal diario en ayunas. Abandono definitivo del tabaco, moderación de líquidos y vacunación estacional [12, 14, 35].
* **Contraindicaciones Estrictas**: Suspender inmediatamente la actividad física e inducir alarma si el paciente reporta: aumento de peso >1.8 kg (3 lbs) en 1-3 días, empeoramiento agudo de la disnea en reposo o aparición de estertores húmedos, angina inestable, o uso de inotrópicos intravenosos [12, 35].

### 2.4. Enfermedad de Parkinson (EP)
* **Limitaciones**: Trastornos motores cardinales (bradicinesia extrema, rigidez axial en rueda dentada, temblor de reposo), inestabilidad postural y episodios de congelamiento de la marcha (Freezing of Gait). Disfunción ejecutiva, lentitud de procesamiento, apatía y kinesiofobia [15, 16, 17, 39].
* **Plan de Movimiento (Evidencia)**:
  * **Aeróbico**: Entrenamiento de intensidad moderada a alta (70-85% FC máxima) en dispositivos estables (bicicleta estática, elíptica con soporte) para inducir neuroplasticidad cortico-estriatal [15, 38].
  * **Neuromotor/Fuerza**: Integración de baile (Tango adaptado) o Tai Chi para propiocepción y rotación del tronco [15]. Uso mandatorio de Pistas Externas (metrónomos rítmicos o guías visuales) para normalizar la zancada y evitar congelamiento [43].
* **Recomendaciones de Estilo de Vida**: Coordinación farmacocinética rigurosa: programar el ejercicio de mayor demanda física durante las fases "ON" de la medicación (niveles máximos de levodopa) para asegurar fluidez articular y prevenir agotamiento [15, 17].
* **Contraindicaciones Estrictas**: Prohibición absoluta del uso no supervisado de cintas rodantes motorizadas sin soporte de arnés (riesgo de retropulsión severa y caídas). Ejecución de ejercicios de doble tarea (motor + cognitivo simultáneo) contraindicada en etapas avanzadas por agotamiento atencional [15, 17].

### 2.5. Diabetes Mellitus Tipo 2 (DMT2)
* **Limitaciones**: Neuropatía sensitivo-motora distal (pérdida de sensibilidad plantar protectora), neuropatía autonómica (respuesta cardíaca atenuada e hipotensión ortostática), daño endotelial microvascular y riesgo de retinopatía proliferativa [18, 19, 46].
* **Plan de Movimiento (Evidencia)**:
  * **Aeróbico**: Dosis óptima ~1,100 METs-min/semana. Prescripción obligatoria de 150-300 min/semana (intensidad moderada). Fundamental: no transcurrir más de 48 horas sin ejercicio por la rápida disipación de la sensibilidad celular a la insulina [45, 46, 47].
  * **Fuerza/Balance**: 2-3 sesiones semanales de 8-10 ejercicios multiarticulares (50-85% 1-RM) [47]. Incorporar balance inestable (Tai Chi) para compensar déficits propioceptivos [18].
* **Recomendaciones de Estilo de Vida**: Interrupción estricta del comportamiento sedentario: por cada 30 min sentados, ejecutar mínimo 3 min de actividad ligera (ej. extensiones de piernas). Inspección diaria de pies, uso de calzado sin costuras y monitoreo de glucemia de rescate [18, 44].
* **Contraindicaciones Estrictas**: Prohibido iniciar si la glucemia es >300 mg/dL (o >250 con cetonas) o <100 mg/dL sin corrección previa. La maniobra de Valsalva, saltos axiales o posturas invertidas están categóricamente contraindicadas si existe retinopatía proliferativa activa (riesgo de hemorragia vítrea). Cero carga axial en pie de Charcot o úlceras activas [18, 47].

### 2.6. Demencias y Enfermedad de Alzheimer
* **Limitaciones**: Deterioro severo de funciones ejecutivas corticales, amnesia anterógrada, apraxia ideomotora, desorientación espacial, comportamiento motor aberrante, apatía severa, agitación e ilusiones paranoides [20, 21, 48].
* **Plan de Movimiento (Evidencia)**:
  * **Aeróbico/Multicomponente**: Rutinas automatizadas de muy baja complejidad cognitiva (Nivel 1 o 2: sentados o bipedestación estática con soporte). Caminatas supervisadas, ciclismo estático y estiramientos activos con tareas duales muy simples. Todo mediado por cuidador (p. ej., protocolo RDAD) [20, 21, 51].
* **Recomendaciones de Estilo de Vida**: Establecer un cronograma circadiano inquebrantable, ejecutando las sesiones siempre a la misma hora para estructurar temporalmente la cognición (evitar síndrome del atardecer). Control intensivo de variabilidad de presión arterial y lípidos [21, 50, 53].
* **Contraindicaciones Estrictas**: Se descartará automáticamente la prescripción de coreografías complejas, secuencias con alta demanda de memoria o combinaciones asimétricas que induzcan agresividad catastrófica y estrés. Absoluta prohibición de entrenamientos peripatéticos (caminar sin rumbo) en exteriores no cercados o sin supervisión continua uno a uno [20, 21].

### 2.7. Enfermedad Pulmonar Obstructiva Crónica (EPOC)
* **Limitaciones**: Atrapamiento de aire, hiperinsuflación pulmonar dinámica durante esfuerzo que aplana los hemidiafragmas, disnea paralizante (asfixia), ansiedad reactiva severa, y miopatía caquéctica (debilidad de cuádriceps que limita la marcha) [22, 23, 55].
* **Plan de Movimiento (Evidencia)**:
  * **Aeróbico**: Se prefiere el entrenamiento por intervalos cortos de alta intensidad relativa (80-100% de la capacidad pico) con descansos activos, frente al continuo, para evitar que la taquipnea induzca el colapso espiratorio y el atrapamiento de aire [22, 23, 56].
  * **Fuerza y Respiratorio**: Fortalecimiento de piernas y miembros superiores (apoyados). Entrenamiento diario (5-7 días) de músculos inspiratorios con Threshold IMT (>= 30% PImax) [22].
* **Recomendaciones de Estilo de Vida**: Instrucción imperativa en la técnica de respiración con labios fruncidos para generar PEP fisiológica y vaciado espiratorio. Soporte nutricional hipercalórico contra caquexia y cese absoluto del hábito tabáquico o exposición a biomasa [22].
* **Contraindicaciones Estrictas**: Queda estrictamente prohibido el ejercicio físico dinámico durante episodios de exacerbación respiratoria aguda (infecciones). Suspender inmediatamente ante caídas de SpO2 <88% sostenida, dolor torácico, cianosis peribucal, sibilancias audibles o confusión por hipercapnia [22].

### 2.8. Accidente Cerebrovascular (ACV) y Desórdenes Isquémicos
* **Limitaciones**: Hemiparesia, espasticidad piramidal, flacidez contralateral, déficit cinestésico y propioceptivo, desplazamiento asimétrico del centro de gravedad, negligencia espacial unilateral y profunda desacondicionamiento cardiovascular post-evento [24, 57].
* **Plan de Movimiento (Evidencia)**:
  * **Motor Orientado / Fuerza**: Entrenamiento de tareas motrices específicas y repetitivas orientadas a metas (p. ej. restricción de la extremidad sana). 2-3 días a la semana adaptados a la espasticidad individual (poleas, máquinas neumáticas) [24].
  * **Aeróbico**: Cicloergómetros de doble acoplamiento o marcha asistida (con órtesis AFO si hay pie péndulo y soporte de peso corporal parcial) a 40-70% FCR. El inicio temprano favorece la plasticidad [24].
* **Recomendaciones de Estilo de Vida**: Bipedestación frecuente para mitigar el sedentarismo. Adaptación ergonómica extrema del entorno y control riguroso de la presión arterial sistémica y el perfil lipídico como prevención secundaria [24].
* **Contraindicaciones Estrictas**: Contraindicación absoluta del uso de cargas pesadas libres asimétricas en el miembro hemipléjico que fomenten patrones de hipertonía flexora o causen subluxación articular inferior del hombro flácido. Evitar estiramientos balísticos si hay espasticidad severa (>4 Ashworth) [24].

### 2.9. Cardiopatía Isquémica (Riesgo Cardiovascular Global)
* **Limitaciones**: Umbral miocárdico hipóxico patológico que desata crisis de angina de pecho (dolor opresivo retroesternal) al sobrepasar esfuerzo físico determinado. Severa ansiedad generalizada y kinesiofobia post-infarto o post-revascularización [13, 25].
* **Plan de Movimiento (Evidencia)**:
  * **Aeróbico**: Prescripción rigurosa: la frecuencia cardíaca de entrenamiento debe fijarse entre 10 y 15 latidos por minuto por debajo del umbral isquémico comprobado (antes del dolor o cambios ST) [25].
  * **Fuerza**: Entrenamiento en circuito de alta repetición (10-15 reps) con cargas ligeras, estrictamente sin pausas apneicas (no Borg alto) ni maniobra de Valsalva [25].
* **Recomendaciones de Estilo de Vida**: Adherencia indefectible a farmacoterapia (antiagregación, betabloqueantes, estatinas). Modificación nutricional (dieta Mediterránea clásica o DASH) y retirada rotunda de tabaquismo [25].
* **Contraindicaciones Estrictas**: Las reglas de la base de datos deben denegar toda prescripción de esfuerzo frente a síntomas de estenosis valvular aórtica severa sintomática, angina de pecho inestable de progresión reciente o arritmias complejas graves incontroladas (requiere compensación invasiva previa) [13, 25].

### 2.10. Osteoporosis y Trastornos de Fragilidad Ósea
* **Limitaciones**: Pérdida de densidad mineral ósea (DMO), fragilidad esquelética trabecular, colapso de cuerpos vertebrales, hipercifosis dorsal progresiva, déficit profundo de balance y miedo paralizante a las caídas [3, 27, 28].
* **Plan de Movimiento (Evidencia)**:
  * **Alto Impacto y Resistencia Ósea (HiRIT/LIFTMOR)**: Desmintiendo tabúes, el protocolo exige entrenamiento supervisado a cargas altas (80-85% 1-RM) en ejercicios como peso muerto y sentadillas para generar mecanotransducción ósea [3, 27].
  * **Carga de Impacto/Equilibrio**: Fuerzas de reacción moderadas a altas (saltos, dominadas con caída) y rutinas de equilibrio dinámico (Tai Chi) para reducir la tasa global de caídas [3, 28].
* **Recomendaciones de Estilo de Vida**: Suplementación obligatoria de Calcio (1200 mg/día) y Vitamina D3 (800 UI/día). Auditoría ambiental exhaustiva del hogar (cables, alfombras, iluminación) y reeducación postural "Strong, Steady and Straight" (evitar doblar la cintura) [3, 28].
* **Contraindicaciones Estrictas**: Intercepción dinámica y descarte de cualquier movimiento biomecánico que integre flexión espinal forzada con carga (p. ej. encogimientos abdominales crunch o tocar puntas de pies) o torsiones violentas rápidas de columna, por altísimo riesgo de fracturas patológicas por aplastamiento acuñado [3, 27, 28].

---

## 3. Referencias Bibliográficas (Formato APA 7ma Edición)

1. GBD 2021 Diseases and Injuries Collaborators (2024). Global burden of disease and its risk factors for adults aged 70 and older across 204 countries and territories. *ResearchGate*.
2. OPS - PAHO (2020). *El número de adultos mayores con necesidades de cuidado a largo plazo se triplicará para 2050 en las Américas*. Organización Panamericana de la Salud.
3. Watson, S. L., Weeks, B. K., Weis, L. J., Harding, A. T., Horan, S. A., & Beck, B. R. (2018). High-intensity resistance and impact training improves bone mineral density and physical function in postmenopausal women with osteopenia and osteoporosis: the LIFTMOR randomized controlled trial. *Journal of Bone and Mineral Research, 33*(2), 211-220. https://doi.org/10.1002/jbmr.3284
4. JMIR Aging (2024). Global, Regional, and National Burden of Falls Among Older Adults Aged 65 Years and Above: Secondary Data Analysis of the Global Burden of Disease Study 2021.
5. The Global Burden of Diseases and Injuries Among Older Adults. *IJAGE*.
6. Pan American Health Organization. (2021). Conclusions - Leading Causes of Death and Disease Burden in the Americas.
7. Bannuru, R. R., Osani, M. C., Vaysbrot, E. E., Arden, N. K., Bennell, K., Bierma-Zeinstra, S. M. A., ... & McAlindon, T. E. (2019). OARSI guidelines for the non-surgical management of knee, hip, and polyarticular osteoarthritis. *Osteoarthritis and Cartilage, 27*(11), 1578-1589. https://doi.org/10.1016/j.joca.2019.06.011
9. Cruz-Jentoft, A. J., Bahat, G., Bauer, J., Boirie, Y., Bruyère, O., Cederholm, T., ... & Zamboni, M. (2019). Sarcopenia: revised European consensus on definition and diagnosis. *Age and Ageing, 48*(1), 16-31. https://doi.org/10.1093/ageing/afy169
12. McDonagh, T. A., Metra, M., Adamo, M., Gardner, R. S., Baumbach, A., Böhm, M., ... & Skouri, H. (2021). 2021 ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure. *European Heart Journal, 42*(36), 3599-3726. https://doi.org/10.1093/eurheartj/ehab368
13. Practical Guidelines for Exercise Prescription in Patients with Chronic Heart Failure. *PMC*.
14. The Management of Chronic and Acute Heart Failure: What Patients Need to Know (2022). ESC Guidelines.
15. Osborne, J. A., Botkin, R., Colon-Semenza, C., DeAngelis, T. R., Gallardo, O. G., Kosakowski, H., ... & Ellis, T. D. (2022). Physical Therapist Management of Parkinson Disease: A Clinical Practice Guideline From the American Physical Therapy Association. *Physical Therapy, 102*(4), pzab302. https://doi.org/10.1093/ptj/pzab302
17. Correction to: Osborne JA, et al. (2022). Physical Therapist Management of Parkinson Disease.
18. Colberg, S. R., Sigal, R. J., Yardley, J. E., Riddell, M. C., Dunstan, D. W., Dempsey, P. C., ... & Tate, D. F. (2016). Physical Activity/Exercise and Diabetes: A Position Statement of the American Diabetes Association. *Diabetes Care, 39*(11), 2065-2079. https://doi.org/10.2337/dc16-1728
19. Physical activity guidelines for adults with type 2 Diabetes (2024). *Diabetes Research and Clinical Practice*.
20. Maestre, G. E., Mena, L. J., & Melgarejo, J. D. (2018). Incidence of dementia in elderly Latin Americans: Results of the Maracaibo Aging Study. *Alzheimer's & Dementia, 14*(2), 140-147. https://doi.org/10.1016/j.jalz.2017.06.2636
22. Spruit, M. A., Singh, S. J., Garvey, C., ZuWallack, R., Nici, L., Rochester, C., ... & Wouters, E. F. (2013). An official American Thoracic Society/European Respiratory Society statement: key concepts and advances in pulmonary rehabilitation. *American Journal of Respiratory and Critical Care Medicine, 188*(8), e13-e64. https://doi.org/10.1164/rccm.201309-1634ST
24. Billinger, S. A., Arena, R., Bernhardt, J., Eng, J. J., Franklin, B. A., Johnson, C. M., ... & Roth, E. J. (2014). Physical activity and exercise recommendations for stroke survivors: a statement for healthcare professionals from the American Heart Association/American Stroke Association. *Stroke, 45*(8), 2532-2553. https://doi.org/10.1161/STR.0000000000000022
25. Visseren, F. L. J., Mach, F., Smulders, Y. M., Carballo, D., Koskinas, K. C., Bäck, M., ... & ESC Scientific Document Group. (2021). 2021 ESC Guidelines on cardiovascular disease prevention in clinical practice. *European Heart Journal, 42*(34), 3227-3337. https://doi.org/10.1093/eurheartj/ehab484
27. LIFTMOR trial - ANZCTR Registration. High intensity progressive resistance training for postmenopausal women.
28. Replicating the LIFTMOR Trial for Osteopenia and Osteoporosis - Schroth DC.
29. Non-surgical management of knee osteoarthritis: comparison of ESCEO and OARSI 2019 guidelines.
30. Evidence-based guidelines for the nonpharmacological treatment of osteoarthritis of the hip and knee. *BC Medical Journal*.
32. OARSI guidelines for the non-surgical management of knee, hip, and polyarticular osteoarthritis.
34. Sarcopenia: revised European consensus on definition and diagnosis.
35. 2021 ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure.
38. Protocol: High-Intensity Endurance exercice program for Parkinson's Disease.
39. Physical Therapist Management of Parkinson Disease: A Clinical Practice Guideline.
43. Physical Therapist Management of Parkinson Disease: A Clinical Practice Guideline From the American Physical Therapy Association - Oxford Academic.
44. ADA: Guideline Recommends Light Activity Every 30 Minutes.
45. Personalizing Physical Activity for Glucose Control Among Individuals With Type 2 Diabetes.
46. Exercise/Physical Activity in Individuals with Type 2 Diabetes: A Consensus Statement from the American College of Sports Medicine.
47. Physical Activity/Exercise and Diabetes: A Position Statement of the American Diabetes Association.
48. Physical activity and cognition in the elderly: A review.
50. Vista de Epidemiología de las demencias | Archivos del Hospital Universitario "General Calixto García".
51. The Effects of Exercise for Cognitive Function in Older Adults: A Systematic Review and Meta-Analysis of Randomized Controlled Trials - MDPI.
53. Nighttime Blood Pressure Interacts with APOE Genotype to Increase the Risk of Incident Dementia of the Alzheimer's Type in Hispanics.
55. Pulmonary Rehabilitation for Adults with Chronic Respiratory Disease: An Official American Thoracic Society Clinical Practice Guideline.
56. Learn from the past and create the future: The 2013 ATS/ERS statement on pulmonary rehabilitation.
57. Healthy Aging: Data and Visualizations - PAHO/WHO.
