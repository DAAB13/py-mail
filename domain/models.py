# domain/models.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class Estudiante:
    """Representa a un estudiante inscrito en un NRC específico."""
    id: str
    periodo: str
    nrc: str
    codigo_estudiante: str
    nombre_estudiante: str
    email_upn: Optional[str] = None
    correo_est_personal: Optional[str] = None
    cel_estudiante: Optional[str] = None

    @property
    def email_destino(self) -> str:
        """Prioriza el correo institucional (UPN), si no hay, usa el personal."""
        return self.email_upn or self.correo_est_personal or ""

@dataclass
class Docente:
    """Información de contacto del docente."""
    codigo_banner: str
    nombre_docente: str
    email_upn: Optional[str] = None
    celular: Optional[str] = None
    email_personal: Optional[str] = None

@dataclass
class SesionProgramada:
    """Datos de una sesión de clase específica de la programación académica."""
    id: str
    periodo: str
    nrc: str
    coordinador: str
    tipo_programa: str
    programa: str
    categoria_programa: str
    curso: str
    codigo_banner: str  # ID del docente
    docente: str
    sesion: int
    fechas: str
    estado_clase: str
    hora_inicio: str
    hora_fin: str
    total_horas: float
    soporte: Optional[str] = None # Movido al final para evitar el TypeError

    def get_resumen(self) -> str:
        """Un pequeño resumen para usar en correos o logs."""
        return f"{self.curso} (NRC: {self.nrc}) - {self.fechas} {self.hora_inicio}-{self.hora_fin}"
