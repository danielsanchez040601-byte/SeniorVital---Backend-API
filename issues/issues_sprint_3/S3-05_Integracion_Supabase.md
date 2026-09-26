# 🗄️ Issue S3-05: Integración con Supabase PostgreSQL y Consultas JSONB

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  

---

## 🎯 1. Reemplazo de BigQuery por Supabase PostgreSQL + JSONB

Para cumplir con la directriz de stack 100% libre de costos y cloud-native, toda la analítica preventiva se ejecuta directamente en Supabase mediante SQLAlchemy asíncrono y operadores nativos de PostgreSQL:

```sql
-- Detección de estancamiento y fatiga crítica en Supabase
SELECT 
    er.senior_id,
    AVG(er.rpe_score) AS promedio_rpe,
    COUNT(CASE WHEN er.reported_pain != 'Sin Dolor' THEN 1 END) AS reportes_dolor,
    COUNT(dr.id) AS rutinas_completadas
FROM exercise_records er
LEFT JOIN daily_routines dr ON dr.senior_id = er.senior_id AND dr.status = 'completed'
WHERE er.completed_at >= NOW() - INTERVAL '14 days'
GROUP BY er.senior_id;
```

---

## ⚡ 2. Optimización del Pool de Conexiones (PgBouncer Puerto 6543)

* **Parámetro `statement_cache_size=0`:** Resuelve de forma definitiva el error de *prepared statements* duplicados en transacciones concurrentes de PgBouncer.
* **Pool Defensivo:** Configurado con `pool_size=5`, `max_overflow=5` y `pool_pre_ping=True` para soportar latencias variables en despliegues cloud.
