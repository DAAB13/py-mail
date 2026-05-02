# services/flujos_reportes.py

from datetime import datetime, timedelta
from loguru import logger

from data import data_loader
from services.core_mailer import CoreMailer

class FlujosReportes:
    """Maneja los flujos de reportería administrativa."""

    def __init__(self, core: CoreMailer):
        self.core = core

    def enviar_informe_semanal(self, start_date: str = None, end_date: str = None):
        """[Flujo 3] Envía un reporte consolidado a William.

        Args:
            start_date: Fecha de inicio en formato YYYY-MM-DD.
                        Si es None, usa el lunes de la semana actual.
            end_date: Fecha de fin en formato YYYY-MM-DD.
                    Si es None, usa el domingo de la semana actual.
        """
        logger.info("Generando Informe Semanal de Supervisión...")
        
        # 1. Determinar rango de fechas
        if start_date and end_date:
            try:
                lunes = datetime.strptime(start_date, "%Y-%m-%d")
                domingo = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                logger.error(f"Formato de fecha inválido. Se esperaba YYYY-MM-DD. Recibido: '{start_date}', '{end_date}'")
                return
            if lunes > domingo:
                logger.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
                return
        else:
            # Calcular lunes a domingo de la semana actual
            hoy = datetime.now()
            lunes = hoy - timedelta(days=hoy.weekday())
            domingo = lunes + timedelta(days=6)
        
        fecha_lunes_str = lunes.strftime("%d/%m")
        fecha_domingo_str = domingo.strftime("%d/%m")
        
        inicio_iso = lunes.strftime("%Y-%m-%d")
        fin_iso = domingo.strftime("%Y-%m-%d")

        # 2. Cargar datos
        todas_las_sesiones = data_loader.load_programacion()
        
        # 3. Filtrar y Procesar: rango de fechas + soporte 'diego'
        sesiones_semana = []
        for s in todas_las_sesiones:
            fecha_str = str(s.fechas).split(" ")[0]  # Ignoramos la parte de la hora (00:00:00)
            es_del_rango = inicio_iso <= fecha_str <= fin_iso
            es_diego = str(s.soporte or "").strip().upper() == "DIEGO"
            if es_del_rango and es_diego:
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
        except Exception:
            logger.exception("Error crítico al renderizar el informe semanal")
            return

        subject_template = conf.get("subject", "Reporte semanal supervisión")
        asunto = subject_template.format(fecha_lunes=fecha_lunes_str, fecha_domingo=fecha_domingo_str)

        # 7. Envío
        self.core.outlook.enviar(
            destinatario=destinatario, asunto=asunto, cuerpo_html=html
        )
        logger.success(f"Informe semanal enviado a {destinatario} con {total_p} sesiones analizadas.")