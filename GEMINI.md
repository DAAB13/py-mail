# py-mail: Asistente de Gestión Académica (UPN)

Este proyecto es una herramienta de automatización diseñada para simplificar y agilizar la comunicación académica en la **Escuela de Postgrado de la Universidad Privada del Norte (UPN)**. Su función principal es el envío masivo y personalizado de correos electrónicos a estudiantes y docentes utilizando Microsoft Outlook como motor de salida.

## 🚀 Resumen del Proyecto

*   **Propósito**: Automatizar flujos de comunicación (bienvenida a alumnos, inicio de cursos para docentes, informes semanales).
*   **Tecnologías Clave**:
    *   **Python 3.13**: Lenguaje base.
    *   **uv**: Gestor de paquetes y entorno virtual.
    *   **Jinja2**: Motor de plantillas HTML para correos dinámicos.
    *   **Pandas & PyArrow**: Procesamiento de datos desde archivos Parquet.
    *   **PyWin32 (COM)**: Integración con Outlook Classic (Windows).
    *   **Loguru**: Sistema de logging avanzado.
    *   **Pydantic / Dataclasses**: Modelado de datos (`Estudiante`, `Docente`, `SesionProgramada`).

## 🏗️ Arquitectura y Estructura

El proyecto sigue un patrón de diseño por capas y utiliza una fachada (`Facade`) para simplificar el acceso a los servicios de mailing:

*   `main.py`: Punto de entrada con un menú interactivo en consola.
*   `domain/`: Modelos de datos que representan las entidades del negocio.
*   `services/`:
    *   `mailing.py`: Fachada principal que coordina los flujos.
    *   `core_mailer.py`: Motor base para carga de configuración, plantillas y conexión Outlook.
    *   `flujos_academicos.py` / `flujos_reportes.py`: Lógica específica de cada proceso de envío.
*   `mail/`: Implementación de la comunicación con Outlook (`outlook.py`).
*   `data/`: Módulo de carga de datos desde archivos Parquet mapeados por variables de entorno.
*   `templates/`: Plantillas HTML responsivas para los diferentes tipos de correos.
*   `config/`: Configuración centralizada en archivos TOML.

## 🛠️ Comandos y Configuración

### Instalación
```powershell
uv sync
```

### Configuración
1.  Copia `plantilla.env` a `.env`.
2.  Define las rutas a los archivos Parquet de datos (`PATH_PROGRAMACION`, `PATH_ESTUDIANTES`, `PATH_DOCENTES`).
3.  Define las rutas de los directorios de adjuntos (`PATH_ADJUNTOS_ALUMNOS`, `PATH_ADJUNTOS_DOCENTES`).
4.  Revisa `config/config.toml` para ajustar asuntos, destinatarios fijos y variables de contenido (enlaces, contactos).

### Ejecución
```powershell
uv run main.py
```

## 📜 Convenciones de Desarrollo

*   **Seguridad y Validación**: El sistema no envía los correos directamente. En su lugar, los guarda en la carpeta de **Borradores (Drafts)** de Outlook y los muestra en pantalla (`mail.Display()`) para una revisión final antes del envío manual.
*   **Gestión de Datos**: Se asume que los datos fuente están en formato **Parquet**. Si se requiere usar Excel/CSV, se deben convertir previamente o modificar `data_loader.py`.
*   **Logging**: Se usa `loguru` para rastrear el éxito de las operaciones y diagnosticar errores de conexión con Outlook o archivos faltantes.
*   **Plantillas**: Todos los correos deben usar plantillas `.html` en la carpeta `templates/` y ser renderizados vía `Jinja2`.
*   **Tipado**: Se debe mantener el uso de `Type Hints` en todas las funciones y clases para asegurar la consistencia del código.

## 📝 Notas del Sistema
*   Este sistema requiere **Microsoft Outlook Classic** instalado y configurado en Windows.
*   La conexión COM se inicializa mediante `pythoncom.CoInitialize()` para evitar problemas con hilos y procesos colgados.
