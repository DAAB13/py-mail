import sys
from pathlib import Path
from loguru import logger

def setup_logging():
    """Configura loguru para registrar en consola y archivo con rotación semanal."""
    # Determinamos la raíz del proyecto (un nivel arriba de donde está este archivo si estuviera en config/)
    # Pero como lo invocaremos desde los puntos de entrada, lo mejor es usar rutas relativas al CWD
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    # Limpiar configuración por defecto (consola básica)
    logger.remove()

    # Log a la consola con colores y formato amigable
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # Log al archivo con rotación, retención y compresión
    logger.add(
        log_file,
        rotation="1 week",      # Refrescar cada semana
        retention="4 weeks",    # Mantener un mes de historial
        compression="zip",      # Comprimir logs antiguos
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",          # El archivo guarda todo para debugging profundo
        encoding="utf-8"
    )
    
    logger.info("Sistema de logging inicializado correctamente.")
