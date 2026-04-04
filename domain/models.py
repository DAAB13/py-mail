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

    @property
    def fecha_formateada(self) -> str:
        """Devuelve la fecha en formato DD/MM/AAAA si está en formato YYYY-MM-DD."""
        f_raw = str(self.fechas)
        if "-" in f_raw and len(f_raw) >= 10:
            parts = f_raw.split("-")
            if len(parts[0]) == 4:
                return f"{parts[2][:2]}/{parts[1]}/{parts[0]}"
        return f_raw

    @property
    def dict_plantilla(self) -> dict:
        """Devuelve un diccionario listo para ser consumido por las plantillas Jinja2."""
        return {
            'sesion': self.sesion,
            'fecha': self.fecha_formateada,
            'fecha_iso': str(self.fechas),  # Útil para ordenamiento
            'hora_inicio': str(self.hora_inicio)[:5],
            'hora_fin': str(self.hora_fin)[:5],
            'tipo': self.soporte or "Clase",
            'periodo': self.periodo,
            'nrc': self.nrc,
            'curso': self.curso,
            'estado': str(self.estado_clase).upper(),
            'docente': self.docente
        }
