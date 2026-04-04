# main.py

import sys
import time
from loguru import logger
from services.mailing import MailingService
from config.logging_config import setup_logging

def mostrar_bienvenida():
    """Un saludo con un toque de estilo."""
    print("\n" + "="*50)
    print("   ASISTENTE DE GESTIÓN ACADÉMICA (py-mail)   ")
    print("="*50)

def main():
    setup_logging()
    mostrar_bienvenida()
    
    # Inicializamos el servicio
    try:
        service = MailingService()
    except Exception:
        logger.exception("No se pudo iniciar el servicio de mailing")
        input("\nPresiona Enter para salir...")
        return

    while True:
        try:
            print("\n--- MENÚ DE OPERACIONES ---")
            print("1. [Flujo 1] Bienvenida a Alumnos (por ID)")
            print("2. [Flujo 2] Inicio de Curso a Docentes (por ID)")
            print("3. [Flujo 3] Informe Semanal (Próximamente)")
            print("0. Salir")
            
            opcion = input("\nSelecciona una opción > ").strip()
            
            if not opcion:
                continue

            if opcion == "1":
                id_curso = input("Ingresa el ID del curso (ej. 226201.1019): ").strip()
                if id_curso:
                    service.enviar_bienvenida_curso(id_curso)
                else:
                    print("❌ El ID no puede estar vacío.")
            
            elif opcion == "2":
                id_curso = input("Ingresa el ID del curso para docentes: ").strip()
                if id_curso:
                    service.enviar_inicio_docentes(id_curso)
                else:
                    print("❌ El ID no puede estar vacío.")
            
            elif opcion == "3":
                service.enviar_informe_semanal()
            
            elif opcion == "0":
                print("\n¡Cerrando el sistema! Que tengas un gran día, Diego.")
                break
            
            else:
                print(f"\n❌ '{opcion}' no es una opción válida.")
            
            time.sleep(1)

        except EOFError:
            logger.warning("Entrada de datos interrumpida (EOF).")
            break
        except KeyboardInterrupt:
            print("\n\nSaliendo por interrupción de usuario...")
            break
        except Exception:
            logger.exception("Error no controlado durante la operación")
            print("Hubo un problema, pero seguimos adelante...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Error fatal: {e}")
        sys.exit(1)
