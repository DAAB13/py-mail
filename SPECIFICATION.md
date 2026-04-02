# SPECIFICATION

## Objetivo
Asistente local para automatizar el envío de correos académicos desde **Outlook Classic**.

## Stack Técnico (Verificado)
- **Python 3.13** + **uv** (Dependency Manager).
- **pandas + pyarrow**: Lectura de Parquet (fuente limpia de datos).
- **jinja2**: Motor de plantillas HTML.
- **pywin32**: Integración con Outlook (con lógica de reconexión RPC).
- **loguru**: Trazabilidad y logs de colores.
- **dataclasses**: Modelos de dominio ligeros y tipados.

## Arquitectura
1. **`domain/`**: Modelos (`Estudiante`, `Docente`, `SesionProgramada`).
2. **`data/`**: Cargadores de datos Parquet (filtrado por ID).
3. **`mail/`**: Driver de Outlook (con persistencia de borrador `mail.Save()`).
4. **`services/`**: Orquestación de lógica (MailingService).
5. **`templates/`**: HTML dinámico.
6. **`main.py`**: Interfaz de consola e interacción.
