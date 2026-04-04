# services/core_mailer.py

import os
import toml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from typing import List, Dict

from mail.outlook import OutlookMail

class CoreMailer:
    """Motor base: configuración, plantillas y conexión con Outlook."""

    def __init__(self, templates_dir: str = "templates"):
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        self.outlook = OutlookMail()
        
        # Cargar configuración desde TOML
        config_path = Path("config/config.toml")
        if config_path.exists():
            self.config = toml.load(config_path)
            logger.info("Configuración cargada correctamente desde config.toml")
        else:
            self.config = {}
            logger.warning("No se encontró config/config.toml. Se usará configuración por defecto.")

    def get_template_config(self, template_name: str) -> Dict:
        """Obtiene la configuración específica para una plantilla."""
        return self.config.get("templates", {}).get(template_name, {})

    def resolve_attachments(self, filenames: List[str], env_var_name: str) -> List[str]:
        """Convierte nombres de archivos en rutas absolutas usando la variable de entorno indicada."""
        rutas = []
        base_path = os.getenv(env_var_name, "")
        
        if not base_path:
            if filenames:
                logger.warning(f"La variable de entorno {env_var_name} no está definida o está vacía.")
            return rutas
            
        for name in filenames:
            ruta_completa = Path(base_path) / name
            if ruta_completa.exists():
                rutas.append(str(ruta_completa.absolute()))
            else:
                logger.error(f"Adjunto no encontrado en {env_var_name}: {ruta_completa}")
        return rutas