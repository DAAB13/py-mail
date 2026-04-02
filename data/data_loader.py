# data/data_loader.py

import os
from pathlib import Path
from typing import List
import pandas as pd
from dotenv import load_dotenv
from loguru import logger

from domain.models import Estudiante, Docente, SesionProgramada

# Cargamos el entorno al inicio del módulo
load_dotenv()

def _get_env_variable(var_name: str) -> str:
    """Lee una variable de entorno y lanza un error si no se encuentra."""
    value = os.getenv(var_name)
    if value is None:
        logger.error(f"La variable de entorno '{var_name}' no está definida.")
        raise ValueError(f"La variable de entorno '{var_name}' no está definida. Por favor, configúrala en tu archivo .env.")
    return value

def _load_df_from_parquet(var_name: str, description: str) -> pd.DataFrame:
    """Función auxiliar para leer el DataFrame desde la ruta en el .env."""
    file_path = Path(_get_env_variable(var_name))
    if not file_path.exists():
        error_msg = f"Archivo de {description} no encontrado en '{file_path}'."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        df = pd.read_parquet(file_path)
        # Aseguramos que los nombres de las columnas no tengan espacios raros
        df.columns = [col.strip() for col in df.columns]
        return df
    except Exception as e:
        logger.error(f"Error al leer parquet de {description}: {e}")
        raise

def load_programacion() -> List[SesionProgramada]:
    """Carga y devuelve la lista de sesiones programadas."""
    df = _load_df_from_parquet("PATH_PROGRAMACION", "programación")
    # Convertimos cada fila en un objeto SesionProgramada
    # Usamos to_dict('records') para que sea más fácil mapear
    sesiones = [SesionProgramada(**row) for row in df.to_dict('records')]
    logger.success(f"Cargadas {len(sesiones)} sesiones de programación.")
    return sesiones

def load_estudiantes() -> List[Estudiante]:
    """Carga y devuelve la lista de estudiantes."""
    df = _load_df_from_parquet("PATH_ESTUDIANTES", "estudiantes")
    estudiantes = [Estudiante(**row) for row in df.to_dict('records')]
    logger.success(f"Cargados {len(estudiantes)} estudiantes.")
    return estudiantes

def load_docentes() -> List[Docente]:
    """Carga y devuelve la lista de docentes."""
    df = _load_df_from_parquet("PATH_DOCENTES", "docentes")
    docentes = [Docente(**row) for row in df.to_dict('records')]
    logger.success(f"Cargados {len(docentes)} docentes.")
    return docentes

if __name__ == '__main__':
    """Prueba rápida de carga."""
    try:
        est = load_estudiantes()
        if est:
            logger.info(f"Primer estudiante: {est[0].nombre_estudiante} ({est[0].email_destino})")
        
        prog = load_programacion()
        if prog:
            logger.info(f"Primer curso: {prog[0].curso} - Sesión: {prog[0].sesion}")

    except Exception as e:
        logger.critical(f"Fallo en la prueba de carga: {e}")
