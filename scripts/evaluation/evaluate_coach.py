#!/usr/bin/env python3
"""Coach Agent evaluation runner wrapper.

Punto de entrada estándar para la evaluación de los 20 escenarios clínicos del Wellness Coach.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from run_coach_evaluation import main

if __name__ == "__main__":
    main()
