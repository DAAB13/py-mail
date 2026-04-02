# OPERATIONS (Flujos & Datos)

## Fuentes de Datos (Parquet)
1. **Programación**: Sesiones detalladas.
2. **Estudiantes**: Matrícula por NRC y su ID único.
3. **Docentes**: Maestro de contactos (UPN + Personal).

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

## Criterios de Calidad (Actualizados)
- **Persistencia**: Todos los correos se guardan en **Borradores** (`mail.Save()`).
- **Resiliencia**: Reconexión automática si el servidor RPC de Outlook falla.
- **Privacidad**: Nunca exponer correos de alumnos entre sí (BCC).
