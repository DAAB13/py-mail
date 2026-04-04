# mail/outlook.py

import win32com.client as win32
from loguru import logger
from typing import Optional, List
import pythoncom

class OutlookMail:
    """Clase para enviar correos vía Outlook Classic con reconexión automática."""

    def __init__(self):
        self.app = None
        self._conectar()

    def _conectar(self):
        """Establece o refresca la conexión con Outlook."""
        try:
            # Forzamos la inicialización del COM para evitar hilos colgados
            pythoncom.CoInitialize()
            self.app = win32.Dispatch("Outlook.Application")
            logger.info("Conexión con Outlook establecida/refrescada.")
        except Exception as e:
            logger.error(f"Error al conectar con Outlook: {e}")
            self.app = None

    def enviar(
        self, 
        destinatario: str, 
        asunto: str, 
        cuerpo_html: str, 
        adjuntos: Optional[List[str]] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ):
        """Prepara, guarda en borradores y muestra un correo."""
        try:
            # Clave para hilos: inicializar COM en el hilo actual y conectar
            pythoncom.CoInitialize()
            app = win32.Dispatch("Outlook.Application")

            mail = app.CreateItem(0)  # 0 = olMailItem
            mail.To = destinatario
            if cc:
                mail.CC = cc
            if bcc:
                mail.BCC = bcc
            mail.Subject = asunto
            mail.HTMLBody = cuerpo_html

            if adjuntos:
                for ruta in adjuntos:
                    mail.Attachments.Add(ruta)

            # --- LA CLAVE ---
            # Guardamos el correo en la carpeta de Borradores (Drafts)
            mail.Save()
            # Lo mostramos en pantalla para revisión
            mail.Display()
            
            logger.success(f"Borrador guardado y mostrado para: {destinatario}")
            return True
        except Exception as e:
            logger.error(f"Error en Outlook (posible hilo o desconexión): {e}")
            return False
