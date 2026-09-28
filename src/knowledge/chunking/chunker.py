"""
Módulo de Chunking Semántico y Segmentación de Conocimiento Clínico.
Divide el corpus documental geriátrico preservando metadata contextual.
"""
from typing import List, Dict, Any
import json
import re


class ClinicalSemanticChunker:
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 60):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pathology_data(self, kb_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera chunks estructurados con metadatos a partir de la base de conocimiento."""
        chunks = []
        pathologies = kb_data.get("pathologies", [])

        for path_obj in pathologies:
            pid = path_obj["id"]
            pname = path_obj["name"]
            category = path_obj.get("category", "General")
            description = path_obj.get("description", "")
            limitations = path_obj.get("biomechanical_limitations", [])
            recommended = path_obj.get("recommended_modalities", [])
            contraindicated = path_obj.get("strict_contraindications", [])
            max_levels = path_obj.get("safe_progression_levels", [1, 2])

            # Chunk 1: Descripción y Limitaciones Biomecánicas
            content_desc = (
                f"PATOLOGÍA: {pname} (Código: {pid}, Categoría: {category}).\n"
                f"DESCRIPCIÓN CLÍNICA: {description}\n"
                f"LIMITACIONES BIOMECÁNICAS: {'; '.join(limitations)}."
            )
            chunks.append({
                "chunk_id": f"{pid}_DESC",
                "pathology_id": pid,
                "pathology_name": pname,
                "chunk_type": "clinical_profile",
                "content": content_desc,
                "metadata": {
                    "category": category,
                    "max_safe_level": max(max_levels),
                    "allowed_levels": max_levels
                }
            })

            # Chunk 2: Modalidades Recomendadas y Prescripción
            content_rec = (
                f"PRESCRIPCIÓN DE EJERCICIO PARA {pname}:\n"
                f"MODALIDADES RECOMENDADAS: {'; '.join(recommended)}.\n"
                f"NIVELES DE PROGRESIÓN SEGUROS: Niveles {', '.join(map(str, max_levels))}."
            )
            chunks.append({
                "chunk_id": f"{pid}_REC",
                "pathology_id": pid,
                "pathology_name": pname,
                "chunk_type": "recommended_exercises",
                "content": content_rec,
                "metadata": {
                    "category": category,
                    "safe_levels": max_levels
                }
            })

            # Chunk 3: Filtros Duros y Contraindicaciones Estrictas
            content_contra = (
                f"CONTRAINDICACIONES ESTRICTAS Y FILTROS DUROS PARA {pname}:\n"
                f"MOVIMIENTOS Y ACCIONES PROHIBIDAS: {'; '.join(contraindicated)}."
            )
            chunks.append({
                "chunk_id": f"{pid}_CONTRA",
                "pathology_id": pid,
                "pathology_name": pname,
                "chunk_type": "contraindications",
                "content": content_contra,
                "metadata": {
                    "category": category,
                    "is_safety_critical": True
                }
            })

        return chunks
