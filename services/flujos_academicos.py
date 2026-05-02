# services/flujos_academicos.py

from typing import Set
from loguru import logger

from data import data_loader
from services.core_mailer import CoreMailer


class FlujosAcademicos:
    """Maneja los flujos de comunicación con alumnos y docentes."""

    def __init__(self, core: CoreMailer):
        self.core = core

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
            key=lambda x: x.sesion,
        )
        if not sesiones_id:
            logger.error(f"No se encontraron sesiones para el ID {id_objetivo}.")
            return

        sesion_principal = sesiones_id[0]  # Para sacar el nombre del curso, nrc, etc.

        # Filtrado de todos los estudiantes
        estudiantes_curso = [
            e for e in todos_los_estudiantes if str(e.id).strip() == id_objetivo
        ]
        if not estudiantes_curso:
            logger.warning(f"No se encontraron estudiantes para el ID {id_objetivo}.")
            return

        # Recolectar todos los correos disponibles (UPN + Personal) sin duplicados
        destinatarios_set: Set[str] = set()
        for est in estudiantes_curso:
            if est.email_upn:
                destinatarios_set.add(est.email_upn.strip())
            if est.correo_est_personal:
                destinatarios_set.add(est.correo_est_personal.strip())

        # Filtramos posibles vacíos
        destinatarios_lista = [d for d in destinatarios_set if d]

        if not destinatarios_lista:
            logger.error("No se encontraron correos para este curso.")
            return

        # Configuración de la plantilla
        conf = self.core.get_template_config("bienvenida_alumnos")

        # Renderizado
        try:
            # Formatear sesiones para la plantilla
            sesiones_formateadas = [s.dict_plantilla for s in sesiones_id]

            template = self.core.jinja_env.get_template("bienvenida_alumnos.html")
            html_contenido = template.render(
                curso=sesion_principal.curso,
                periodo=sesion_principal.periodo,
                nrc=sesion_principal.nrc,
                docente=sesion_principal.docente,
                sesiones=sesiones_formateadas,
                **self.core.config.get("content_vars", {}),
            )
        except Exception:
            logger.exception("Error crítico al renderizar la plantilla de bienvenida")
            return

        # Preparar Asunto dinámico
        subject_template = conf.get("subject", "Bienvenida al curso: {curso}")
        try:
            asunto = subject_template.format(
                curso=sesion_principal.curso, id=id_objetivo, nrc=sesion_principal.nrc
            )
        except Exception:
            logger.warning("Error al formatear el asunto dinámico. Usando fallback.")
            asunto = f"Bienvenido al curso {sesion_principal.curso}"

        # Preparar Adjuntos
        env_var_adjuntos = conf.get("attachments_path", "PATH_ADJUNTOS_ALUMNOS")
        adjuntos = self.core.resolve_attachments(
            conf.get("attachments", []), env_var_adjuntos
        )

        # Envío único con BCC
        # Agregamos al jefe a la lista de CCO
        if "william.cruzado@upn.edu.pe" not in destinatarios_lista:
            destinatarios_lista.append("william.cruzado@upn.edu.pe")
            
        bcc_string = "; ".join(destinatarios_lista)

        self.core.outlook.enviar(
            destinatario="diego.alvarado@upn.edu.pe",  # Etiqueta visual (Tú)
            asunto=asunto,
            cuerpo_html=html_contenido,
            bcc=bcc_string,
            adjuntos=adjuntos,
        )
        logger.success(
            f"Correo de bienvenida preparado para {len(estudiantes_curso)} alumnos con {len(adjuntos)} adjuntos."
        )

    def enviar_inicio_docentes(self, id_objetivo: str):
        """[Flujo 2] Envía un correo por docente con sus sesiones específicas."""
        id_objetivo = id_objetivo.strip()
        logger.info(f"Procesando Inicio de Curso para Docentes del ID: {id_objetivo}")

        # 1. Cargar datos
        todas_las_sesiones = data_loader.load_programacion()
        todos_los_docentes = data_loader.load_docentes()

        # 2. Filtrar todas las sesiones de este curso ID
        sesiones_id = [
            s for s in todas_las_sesiones if str(s.id).strip() == id_objetivo
        ]
        if not sesiones_id:
            logger.error(f"No hay sesiones para el ID {id_objetivo}.")
            return

        # 3. Identificar docentes únicos en este ID
        ids_docentes_presentes = set(s.codigo_banner for s in sesiones_id)

        # Configuración de la plantilla
        conf = self.core.get_template_config("inicio_docentes")

        try:
            template = self.core.jinja_env.get_template("inicio_docentes.html")
        except Exception:
            logger.exception(
                "Plantilla de inicio de docentes no encontrada o con errores"
            )
            return

        # Preparar Adjuntos
        env_var_adjuntos = conf.get("attachments_path", "PATH_ADJUNTOS_DOCENTES")
        adjuntos = self.core.resolve_attachments(
            conf.get("attachments", []), env_var_adjuntos
        )

        for cod_docente in ids_docentes_presentes:
            info_docente = next(
                (d for d in todos_los_docentes if d.codigo_banner == cod_docente), None
            )
            sesiones_docente_raw = sorted(
                [s for s in sesiones_id if s.codigo_banner == cod_docente],
                key=lambda x: x.sesion,
            )
            sesiones_docente = [s.dict_plantilla for s in sesiones_docente_raw]

            email_dest = None
            if info_docente:
                email_dest = info_docente.email_upn or info_docente.email_personal
                nombre = info_docente.nombre_docente
            else:
                nombre = sesiones_docente_raw[0].docente
                logger.warning(
                    f"Docente {nombre} no encontrado en maestro de docentes."
                )
                continue

            if not email_dest:
                logger.warning(f"Docente {nombre} no tiene correo registrado.")
                continue

            try:
                html = template.render(
                    nombre_docente=nombre,
                    curso=sesiones_docente_raw[0].curso,
                    nrc=sesiones_docente_raw[0].nrc,
                    sesiones=sesiones_docente,
                    **self.core.config.get("content_vars", {}),
                )
            except Exception:
                logger.exception(
                    f"Error renderizando plantilla para el docente {nombre}"
                )
                continue

            subject_template = conf.get("subject", "Inicio de Clases: {curso}")
            try:
                asunto = subject_template.format(
                    fecha_inicio=sesiones_docente[0]["fecha"],
                    curso=sesiones_docente_raw[0].curso,
                    id=id_objetivo,
                    codigo_banner=cod_docente,
                    nrc=sesiones_docente_raw[0].nrc,
                )
            except Exception:
                logger.warning(
                    f"Error al formatear asunto para {nombre}. Usando fallback."
                )
                asunto = f"Inicio de Curso: {sesiones_docente[0]['curso']}"

            self.core.outlook.enviar(
                destinatario=email_dest,
                asunto=asunto,
                cuerpo_html=html,
                adjuntos=adjuntos,
            )
            logger.success(
                f"Correo preparado para el docente: {nombre} con {len(adjuntos)} adjuntos."
            )
