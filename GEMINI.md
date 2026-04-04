# Project Overview: py-mail

`py-mail` es un asistente local diseñado para automatizar el envío de correos académicos (bienvenida a alumnos, inicio de curso a docentes e informes semanales) integrándose directamente con **Outlook Classic** mediante la API de Windows (`pywin32`).

El sistema procesa datos de programación académica, estudiantes y docentes almacenados en archivos **Parquet** y genera correos personalizados utilizando plantillas **Jinja2**.

## Architecture & Tech Stack

- **Lógica de Negocio**: `MailingService` en `services/mailing.py` orquestra la carga de datos, renderizado de plantillas y preparación de correos.
- **Modelos de Dominio**: Definidos en `domain/models.py` (`Estudiante`, `Docente`, `SesionProgramada`).
- **Acceso a Datos**: `data/data_loader.py` utiliza `pandas` y `pyarrow` para leer archivos Parquet.
- **Integración con Outlook**: `mail/outlook.py` maneja la conexión con la aplicación de escritorio de Outlook, incluyendo lógica de reconexión RPC.
- **Configuración**: 
  - `config/config.toml`: Define los asuntos de los correos, adjuntos y rutas base por tipo de plantilla.
  - `.env`: (Basado en `plantilla.env`) Contiene las rutas absolutas a los archivos de datos y adjuntos.
- **Interfaz**: CLI interactivo en `main.py`.

## Building and Running

El proyecto utiliza `uv` como gestor de paquetes y entorno virtual.

- **Instalar dependencias**:
  ```powershell
  uv sync
  ```
- **Ejecutar la aplicación**:
  ```powershell
  uv run main.py
  ```
- **Pruebas de carga (Unitarias/Humo)**:
  ```powershell
  uv run python -m data.data_loader
  ```

## Development Conventions

- **Persistencia**: Por seguridad, los correos se guardan en la carpeta de **Borradores** de Outlook (`mail.Save()`) en lugar de enviarse inmediatamente.
- **Privacidad (BCC)**: En el flujo de bienvenida a alumnos, todos los destinatarios deben ir en el campo **BCC (CCO)** para cumplir con las normativas de protección de datos.
- **Manejo de Errores**: Se utiliza `loguru` para el registro de eventos, errores y trazabilidad.
- **Tipado**: Uso de `dataclasses` y `typing` para mantener la integridad de los datos entre capas.
- **Orden de Sesiones**: Las sesiones siempre deben ordenarse por el campo `sesion` (entero) antes de renderizar o extraer fechas de inicio.

## Key Files

- `config/config.toml`: Corazón de la personalización de mensajes y adjuntos.
- `services/mailing.py`: Lógica principal de los flujos de envío.
- `mail/outlook.py`: Driver de comunicación con Outlook Classic.
- `templates/`: Archivos HTML para `bienvenida_alumnos` e `inicio_docentes`.
- `SPECIFICATION.md`: Documentación técnica del diseño original.
- `OPERATIONS.md`: Guía de flujos y fuentes de datos.
