# services/flujos_reportes.py

from datetime import datetime, timedelta
from loguru import logger

from data import data_loader
from services.core_mailer import CoreMailer

class FlujosReportes:
    """Maneja los flujos de reportería administrativa."""

    def __init__(self, core: CoreMailer):
        self.core = core

    def enviar_informe_semanal(self):
        """[Flujo 3] Envía un reporte consolidado de la semana actual a William."""
        
        logger.info("Generando Informe Semanal de Supervisión...")
        
        # 1. Determinar rango: Lunes a Domingo de la semana actual
        hoy = datetime.now()
        dia_semana = hoy.weekday() 
        lunes = hoy - timedelta(days=dia_semana)
        domingo = lunes + timedelta(days=6)
        
        fecha_lunes_str = lunes.strftime("%d/%m")
        fecha_domingo_str = domingo.strftime("%d/%m")
        
        inicio_iso = lunes.strftime("%Y-%m-%d")
        fin_iso = domingo.strftime("%Y-%m-%d")

        # 2. Cargar datos
        todas_las_sesiones = data_loader.load_programacion()
        
        # 3. Filtrar y Procesar
        sesiones_semana = []
        for s in todas_las_sesiones:
            if inicio_iso <= str(s.fechas) <= fin_iso:
                sesiones_semana.append(s.dict_plantilla)

        if not sesiones_semana:
            logger.warning("No hay sesiones registradas para esta semana.")
            return

        sesiones_semana.sort(key=lambda x: x['fecha_iso'])

        # 4. Estadísticas
        total_p = len(sesiones_semana)
        total_d = sum(1 for s in sesiones_semana if s['estado'] == 'DICTADA')
        total_r = sum(1 for s in sesiones_semana if s['estado'] == 'REPROGRAMADA')
        
        repro_lista = [s for s in sesiones_semana if s['estado'] == 'REPROGRAMADA']

        # 5. Configuración y Renderizado
        conf = self.core.get_template_config("informe_semanal")
        destinatario = conf.get("fixed_recipient", "william.cruzado@upn.edu.pe")
        
        try:
            template = self.core.jinja_env.get_template("informe_semanal.html")
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

        subject_template = conf.get("subject", "Reporte semanal supervisión")
        asunto = subject_template.format(fecha_lunes=fecha_lunes_str, fecha_domingo=fecha_domingo_str)

        # 7. Envío
        self.core.outlook.enviar(
            destinatario=destinatario, asunto=asunto, cuerpo_html=html
        )
        logger.success(f"Informe semanal enviado a {destinatario} con {total_p} sesiones analizadas.")