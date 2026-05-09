# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ¿Qué hace este proyecto?

**py-mail** es una herramienta de automatización de correos académicos para UPN (Universidad Privada del Norte). Automatiza tres flujos de comunicación:

- **F1 – Bienvenida Alumnos**: Envía un correo masivo en BCC a todos los alumnos de un curso con el cronograma, enlaces y archivos adjuntos.
- **F2 – Inicio Docentes**: Envía correos individuales y personalizados a cada docente con su cronograma de sesiones.
- **F3 – Informe Semanal**: Genera un reporte semanal de supervisión al coordinador (William Cruzado) filtrando sesiones por la etiqueta de soporte "diego".

Todos los correos se guardan como **borradores en Outlook** (nunca se envían automáticamente) para revisión manual antes de enviar. El sistema lee datos desde **archivos parquet** (almacenados en OneDrive), renderiza **plantillas HTML con Jinja2**, y crea los borradores vía **COM de Outlook (pywin32)**.

**Requisito de plataforma**: Solo Windows (requiere Outlook Classic y pywin32).

## Cómo ejecutar la aplicación

```powershell
# Modo consola (menú interactivo)
python main.py

# Modo GUI (aplicación de escritorio con Flet)
python ui/app.py

# Ejecutar tests
pytest tests/ -v
```

**Gestor de paquetes**: `uv`. Para instalar dependencias:
```powershell
uv sync
```

## Arquitectura

```
main.py / ui/app.py
    └── MailingService (facade)
            ├── FlujosAcademicos  → F1 (bienvenida_alumnos) + F2 (inicio_docentes)
            ├── FlujosReportes    → F3 (informe_semanal)
            └── CoreMailer        → Jinja2 + OutlookMail + config TOML

Pipeline de datos:
  data/data_loader.py (pandas + parquet, @lru_cache)
      └── domain/models.py (dataclasses: Estudiante, Docente, SesionProgramada)
```

**Capas principales:**
- `domain/models.py` — Dataclasses puras sin dependencias externas; fuente de verdad para la forma de las entidades.
- `data/data_loader.py` — Lee archivos parquet desde las rutas definidas en `.env`. Los resultados se cachean con `@lru_cache`.
- `mail/outlook.py` — `OutlookMail` envuelve el COM de pywin32; llama a `mail.Save()` para crear borradores y `mail.Display()` para mostrarlos en Outlook.
- `services/core_mailer.py` — Hub compartido inyectado en todos los flujos; contiene el `Environment` de Jinja2, la instancia de `OutlookMail` y la config TOML parseada.
- `services/flujos_academicos.py` / `services/flujos_reportes.py` — Lógica de negocio de cada flujo; usan `core_mailer` para renderizar y enviar.
- `services/mailing.py` — Facade usado por los puntos de entrada; instancia y conecta todos los servicios.
- `config/config.toml` — Asuntos de los correos (como strings Jinja2), listas de archivos adjuntos, reglas de negocio y variables de contenido (URLs, correos de soporte, nombres del staff). **Preferir editar este archivo antes de hardcodear valores en los servicios.**
- `templates/*.html` — Plantillas HTML Jinja2 con CSS inline.

## Configuración

**`.env`** (no versionado): Define las rutas del sistema de archivos Windows para los parquet y directorios de adjuntos:
- `PATH_PROGRAMACION`, `PATH_ESTUDIANTES`, `PATH_DOCENTES` — fuentes parquet
- `PATH_ADJUNTOS_ALUMNOS`, `PATH_ADJUNTOS_DOCENTES` — carpetas de adjuntos
- `LOG_LEVEL` — nivel de log de loguru (por defecto: `INFO`)

**`config/config.toml`**: Controla asuntos, nombres de archivos adjuntos, máximo de destinatarios BCC y todas las variables de contenido (URLs, correos de soporte, números de WhatsApp, nombres del staff). Los cambios aquí se propagan automáticamente a todas las plantillas.

## Logging

Configurado en `config/logging_config.py` usando **loguru**:
- Consola: salida coloreada y legible
- Archivo: `logs/app.log` con rotación semanal, retención de 4 semanas y compresión ZIP

La GUI (`ui/app.py`) instala un sink personalizado de loguru para mostrar los logs en tiempo real con colores según la severidad en el panel de logs.

## Tests

Los tests usan **pytest** con `pythonpath = ["."]` para que los imports funcionen desde la raíz del proyecto.

```powershell
pytest                                # Ejecutar todos los tests
pytest tests/ -v                      # Salida detallada
pytest tests/test_data_loader.py      # Un solo archivo de tests
```

Los tests actuales mockean la carga de archivos parquet y validan la instanciación de dataclasses y el manejo de errores de `.env`. El COM de Outlook no se testea (requiere Windows + Outlook en tiempo de ejecución).
