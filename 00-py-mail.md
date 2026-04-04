---
tags:
  - python
  - upn
fuente:
  - "[[programacion]]"
---
## Objetivo
Asistente local para automatizar el envío de correos académicos desde **Outlook Classic**.

## Fuentes de Datos (Parquet)
- **Programación**: Sesiones detalladas.
-  **Estudiantes**: Matrícula por ID único
-  **Docentes**: Maestro de contactos (UPN + Personal).

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

## Flujos Implementados

### [F1] Bienvenida a Alumnos
- **Entrada**: ID del curso (Ej. `226201.1001`).
- **Lógica**: Agrupa todos los estudiantes del ID.
- **Salida**: UN SOLO correo con todos en **BCC (CCO)**.
- **Contenido**: Tabla HTML completa de todas las sesiones ordenadas.

### [F2] Inicio para Docentes
- **Entrada**: ID del curso.
- **Lógica**: Identifica docentes del curso y filtra **solo sus sesiones**.
- **Salida**: Un correo INDIVIDUAL por docente con su tabla de horario específica.

## Criterios de Calidad 
- **Persistencia**: Todos los correos se guardan en **Borradores** (`mail.Save()`).
- **Resiliencia**: Reconexión automática si el servidor RPC de Outlook falla.
- **Privacidad**: Nunca exponer correos de alumnos entre sí (BCC).
- Avance: [[roadmap]]