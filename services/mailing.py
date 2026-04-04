# services/mailing.py

import os
import toml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from typing import List, Set, Optional, Dict

from data import data_loader
from mail.outlook import OutlookMail

class MailingService:
    """Cerebro del sistema: coordina datos, plantillas y envío."""

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
            
        # Directorio base de adjuntos desde .env
        self.path_adjuntos = os.getenv("PATH_ADJUNTOS", "")
        if not self.path_adjuntos:
            logger.warning("La variable PATH_ADJUNTOS no está definida en el .env.")

    def _get_template_config(self, template_name: str) -> Dict:
        """Obtiene la configuración específica para una plantilla."""
        return self.config.get("templates", {}).get(template_name, {})

    def _resolve_attachments(self, filenames: List[str], env_var_name: str) -> List[str]:
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

    def enviar_bienvenida_curso(self, id_objetivo: str):
        """[Flujo 1] Envía un solo correo a todos los alumnos usando CCO."""
        id_objetivo = id_objetivo.strip()
        logger.info(f"Procesando Bienvenida para el ID: {id_objetivo}")

        # Carga de datos
        todas_las_sesiones = data_loader.load_programacion()
        todos_los_estudiantes = data_loader.load_estudiantes()

        # Filtrado de sesiones de este ID (ordenadas por número de sesión)
        sesiones_id = sorted(
            [s for s in todas_las_sesiones if str(s.id).strip() == id_objetivo],
            key=lambda x: x.sesion
        )
        if not sesiones_id:
            logger.error(f"No se encontraron sesiones para el ID {id_objetivo}.")
            return

        sesion_principal = sesiones_id[0] # Para sacar el nombre del curso, nrc, etc.

        # Filtrado de todos los estudiantes
        estudiantes_curso = [e for e in todos_los_estudiantes if str(e.id).strip() == id_objetivo]
        if not estudiantes_curso:
            logger.warning(f"No se encontraron estudiantes para el ID {id_objetivo}.")
            return

        # Recolectar todos los correos disponibles (UPN + Personal) sin duplicados
        destinatarios_set: Set[str] = set()
        for est in estudiantes_curso:
            if est.email_upn: destinatarios_set.add(est.email_upn.strip())
            if est.correo_est_personal: destinatarios_set.add(est.correo_est_personal.strip())
        
        # Filtramos posibles vacíos
        destinatarios_lista = [d for d in destinatarios_set if d]
        
        if not destinatarios_lista:
            logger.error("No se encontraron correos para este curso.")
            return

        # Configuración de la plantilla
        conf = self._get_template_config("bienvenida_alumnos")
        
        # Renderizado
        try:
            # Formatear sesiones para la plantilla
            sesiones_formateadas = []
            for s in sesiones_id:
                # Intentar formatear fecha si es posible, si no, usar original
                # El usuario pide dd/mm/aaaa y hh:mm
                # Asumimos que vienen como strings o objetos que podemos manipular
                # Si son strings "2026-04-01", los pasamos a "01/04/2026"
                
                fecha_str = str(s.fechas)
                # Intento de parseo simple si viene ISO
                if "-" in fecha_str and len(fecha_str) >= 10:
                    parts = fecha_str.split("-")
                    if len(parts[0]) == 4: # yyyy-mm-dd
                        fecha_str = f"{parts[2][:2]}/{parts[1]}/{parts[0]}"

                hora_i = str(s.hora_inicio)[:5] # hh:mm
                hora_f = str(s.hora_fin)[:5]    # hh:mm

                sesiones_formateadas.append({
                    'sesion': s.sesion,
                    'fecha': fecha_str,
                    'hora_inicio': hora_i,
                    'hora_fin': hora_f,
                    'tipo': s.soporte or "Clase"
                })

            template = self.jinja_env.get_template("bienvenida_alumnos.html")
            html_contenido = template.render(
                curso=sesion_principal.curso,
                periodo=sesion_principal.periodo,
                nrc=sesion_principal.nrc,
                docente=sesion_principal.docente,
                sesiones=sesiones_formateadas,
                **self.config.get("content_vars", {})
            )
        except Exception as e:
            logger.error(f"Error renderizando plantilla: {e}")
            return

        # Preparar Asunto dinámico
        subject_template = conf.get("subject", "Bienvenida al curso: {curso}")
        try:
            asunto = subject_template.format(
                curso=sesion_principal.curso,
                id=id_objetivo,
                nrc=sesion_principal.nrc
            )
        except Exception as e:
            logger.warning(f"Error al formatear asunto: {e}. Usando fallback.")
            asunto = f"Bienvenido al curso {sesion_principal.curso}"

        # Preparar Adjuntos
        env_var_adjuntos = conf.get("attachments_path", "PATH_ADJUNTOS_ALUMNOS")
        adjuntos = self._resolve_attachments(conf.get("attachments", []), env_var_adjuntos)

        # Envío único con BCC
        bcc_string = "; ".join(destinatarios_lista)
        
        self.outlook.enviar(
            destinatario="alumnos@upn.pe",  # Etiqueta visual
            asunto=asunto,
            cuerpo_html=html_contenido,
            bcc=bcc_string,
            adjuntos=adjuntos
        )
        logger.success(f"Correo de bienvenida preparado para {len(estudiantes_curso)} alumnos con {len(adjuntos)} adjuntos.")

    def enviar_inicio_docentes(self, id_objetivo: str):
        """[Flujo 2] Envía un correo por docente con sus sesiones específicas."""
        id_objetivo = id_objetivo.strip()
        logger.info(f"Procesando Inicio de Curso para Docentes del ID: {id_objetivo}")

        # 1. Cargar datos
        todas_las_sesiones = data_loader.load_programacion()
        todos_los_docentes = data_loader.load_docentes()

        # 2. Filtrar todas las sesiones de este curso ID
        sesiones_id = [s for s in todas_las_sesiones if str(s.id).strip() == id_objetivo]
        if not sesiones_id:
            logger.error(f"No hay sesiones para el ID {id_objetivo}.")
            return

        # 3. Identificar docentes únicos en este ID
        ids_docentes_presentes = set(s.codigo_banner for s in sesiones_id)
        
        # Configuración de la plantilla
        conf = self._get_template_config("inicio_docentes")
        
        try:
            template = self.jinja_env.get_template("inicio_docentes.html")
        except Exception as e:
            logger.error(f"Plantilla no encontrada: {e}")
            return

        # Preparar Adjuntos (comunes para todos los docentes en este flujo)
        env_var_adjuntos = conf.get("attachments_path", "PATH_ADJUNTOS_DOCENTES")
        adjuntos = self._resolve_attachments(conf.get("attachments", []), env_var_adjuntos)

        for cod_docente in ids_docentes_presentes:
            # Buscar info del docente
            info_docente = next((d for d in todos_los_docentes if d.codigo_banner == cod_docente), None)
            
            # Sesiones de ESTE docente en ESTE curso
            sesiones_docente_raw = sorted([s for s in sesiones_id if s.codigo_banner == cod_docente], key=lambda x: x.sesion)
            
            # Formatear sesiones para la plantilla
            sesiones_docente = []
            for s in sesiones_docente_raw:
                fecha_str = str(s.fechas)
                if "-" in fecha_str and len(fecha_str) >= 10:
                    parts = fecha_str.split("-")
                    if len(parts[0]) == 4: # yyyy-mm-dd
                        fecha_str = f"{parts[2][:2]}/{parts[1]}/{parts[0]}"

                hora_i = str(s.hora_inicio)[:5]
                hora_f = str(s.hora_fin)[:5]

                sesiones_docente.append({
                    'sesion': s.sesion,
                    'fecha': fecha_str,
                    'hora_inicio': hora_i,
                    'hora_fin': hora_f
                })

            # Determinar destinatario
            email_dest = None
            if info_docente:
                email_dest = info_docente.email_upn or info_docente.email_personal
                nombre = info_docente.nombre_docente
            else:
                nombre = sesiones_docente_raw[0].docente
                logger.warning(f"Docente {nombre} no encontrado en maestro de docentes.")
                continue

            if not email_dest:
                logger.warning(f"Docente {nombre} no tiene correo registrado.")
                continue

            # Renderizado individual
            html = template.render(
                nombre_docente=nombre,
                curso=sesiones_docente_raw[0].curso,
                nrc=sesiones_docente_raw[0].nrc,
                sesiones=sesiones_docente,
                **self.config.get("content_vars", {})
            )
            
            # Preparar Asunto dinámico
            subject_template = conf.get("subject", "Inicio de Clases: {curso}")
            try:
                asunto = subject_template.format(
                    fecha_inicio=sesiones_docente[0]['fecha'],
                    curso=sesiones_docente_raw[0].curso,
                    id=id_objetivo,
                    codigo_banner=cod_docente,
                    nrc=sesiones_docente_raw[0].nrc
                )
            except Exception as e:
                logger.warning(f"Error al formatear asunto: {e}. Usando fallback.")
                asunto = f"Inicio de Curso: {sesiones_docente[0].curso}"
            
            self.outlook.enviar(
                destinatario=email_dest,
                asunto=asunto,
                cuerpo_html=html,
                adjuntos=adjuntos
            )
            logger.success(f"Correo preparado para el docente: {nombre} con {len(adjuntos)} adjuntos.")

    def enviar_informe_semanal(self):
        """[Flujo 3] Envía un reporte consolidado de la semana actual a William."""
        from datetime import datetime, timedelta
        
        logger.info("Generando Informe Semanal de Supervisión...")
        
        # 1. Determinar rango: Lunes a Domingo de la semana actual
        hoy = datetime.now()
        # En Python, lunes es 0, domingo es 6
        dia_semana = hoy.weekday() 
        lunes = hoy - timedelta(days=dia_semana)
        domingo = lunes + timedelta(days=6)
        
        fecha_lunes_str = lunes.strftime("%d/%m")
        fecha_domingo_str = domingo.strftime("%d/%m")
        
        # Para filtrar los datos (asumiendo formato yyyy-mm-dd en el parquet)
        inicio_iso = lunes.strftime("%Y-%m-%d")
        fin_iso = domingo.strftime("%Y-%m-%d")

        # 2. Cargar datos
        todas_las_sesiones = data_loader.load_programacion()
        
        # 3. Filtrar y Procesar
        sesiones_semana = []
        for s in todas_las_sesiones:
            # Filtro por rango de fechas (comparación de strings ISO es válida)
            if inicio_iso <= str(s.fechas) <= fin_iso:
                # Formatear para la tabla
                f_raw = str(s.fechas)
                f_formateada = f"{f_raw[8:10]}/{f_raw[5:7]}/{f_raw[0:4]}" if "-" in f_raw else f_raw
                
                sesiones_semana.append({
                    'fecha': f_formateada,
                    'fecha_iso': f_raw, # para ordenar
                    'periodo': s.periodo,
                    'nrc': s.nrc,
                    'curso': s.curso,
                    'sesion': s.sesion,
                    'estado': str(s.estado_clase).upper(),
                    'docente': s.docente
                })

        if not sesiones_semana:
            logger.warning("No hay sesiones registradas para esta semana.")
            return

        # Ordenar por fecha (antigua a actual)
        sesiones_semana.sort(key=lambda x: x['fecha_iso'])

        # 4. Estadísticas
        total_p = len(sesiones_semana)
        total_d = sum(1 for s in sesiones_semana if s['estado'] == 'DICTADA')
        total_r = sum(1 for s in sesiones_semana if s['estado'] == 'REPROGRAMADA')
        
        repro_lista = [s for s in sesiones_semana if s['estado'] == 'REPROGRAMADA']

        # 5. Configuración y Renderizado
        conf = self._get_template_config("informe_semanal")
        destinatario = conf.get("fixed_recipient", "william.cruzado@upn.edu.pe")
        
        try:
            template = self.jinja_env.get_template("informe_semanal.html")
            html = template.render(
                total_programadas=total_p,
                total_dictadas=total_d,
                total_reprogramadas=total_r,
                reprogramadas_lista=repro_lista,
                todas_sesiones=sesiones_semana
            )
        except Exception as e:
            logger.error(f"Error renderizando informe semanal: {e}")
            return

        # 6. Asunto dinámico
        subject_template = conf.get("subject", "Reporte semanal supervisión")
        asunto = subject_template.format(
            fecha_lunes=fecha_lunes_str,
            fecha_domingo=fecha_domingo_str
        )

        # 7. Envío
        self.outlook.enviar(
            destinatario=destinatario,
            asunto=asunto,
            cuerpo_html=html
        )
        logger.success(f"Informe semanal enviado a {destinatario} con {total_p} sesiones analizadas.")

if __name__ == "__main__":
    service = MailingService()
    # service.enviar_bienvenida_curso("226201.1001")
