#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import glob
from datetime import datetime


def listar_planes_ejercicio():
    """
    Lista todos los planes de ejercicio generados en el directorio data_usuario.
    """
    # Comprobar que el directorio existe
    if not os.path.exists("data_usuario"):
        print("No se encontró el directorio data_usuario.")
        return []

    # Buscar archivos JSON de planes de ejercicio
    patron_busqueda = os.path.join("data_usuario", "plan_ejercicio_*.json")
    archivos = glob.glob(patron_busqueda)

    if not archivos:
        print("No se encontraron planes de ejercicio guardados.")
        return []

    # Ordenar por fecha de modificación (más reciente primero)
    archivos.sort(key=os.path.getmtime, reverse=True)

    return archivos


def mostrar_detalles_plan(ruta_archivo):
    """
    Muestra los detalles de un plan de ejercicio específico.
    """
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            plan = json.load(f)

        # Extraer metadatos
        metadata = plan.get("metadata", {})
        usuario = metadata.get("nombre", "No especificado")
        fecha = metadata.get("fecha_creacion", "No especificada")
        objetivos = metadata.get("objetivos", [])

        print(f"\n{'='*50}")
        print(f"PLAN DE EJERCICIO")
        print(f"{'='*50}")
        print(f"Usuario: {usuario}")
        print(f"Fecha de creación: {fecha}")
        print(f"Objetivos: {', '.join(objetivos)}")
        print(f"{'-'*50}")

        # Mostrar resumen de días
        plan_semanal = plan.get("plan_semanal", {})
        print("RESUMEN SEMANAL:")
        for dia, ejercicios in plan_semanal.items():
            if ejercicios:
                print(f"  - {dia.capitalize()}: {len(ejercicios)} ejercicio(s)")
            else:
                print(f"  - {dia.capitalize()}: Descanso")

        # Preguntar si se desea ver detalles completos
        ver_detalles = (
            input("\n¿Desea ver todos los detalles del plan? (s/n): ").lower() == "s"
        )

        if ver_detalles:
            print("\nDETALLES DEL PLAN:")
            for dia, ejercicios in plan_semanal.items():
                print(f"\n{dia.upper()}")
                print("-" * 30)

                if not ejercicios:
                    print("Día de descanso")
                    continue

                for i, ejercicio in enumerate(ejercicios, 1):
                    nombre = ejercicio.get("nombre", "No especificado")
                    tipo = ejercicio.get("tipo", "No especificado")
                    series = ejercicio.get("series", 0)
                    repeticiones = ejercicio.get("repeticiones", 0)
                    descanso = ejercicio.get("descanso_segundos", 0)

                    print(f"Ejercicio {i}: {nombre}")
                    print(f"  Tipo: {tipo}")
                    print(f"  Series: {series}")
                    print(f"  Repeticiones: {repeticiones}")
                    print(f"  Descanso: {descanso} segundos")

                    # Mostrar descripción si existe
                    if "descripcion" in ejercicio:
                        print(f"  Descripción: {ejercicio['descripcion']}")

                    # Mostrar instrucciones si existen
                    if "instrucciones" in ejercicio and ejercicio["instrucciones"]:
                        print("  Instrucciones:")
                        for j, instruccion in enumerate(ejercicio["instrucciones"], 1):
                            print(f"    {j}. {instruccion}")

                    if i < len(ejercicios):
                        print()  # Línea en blanco entre ejercicios

            # Mostrar recomendaciones adicionales
            recomendaciones = plan.get("recomendaciones_adicionales", {})
            if recomendaciones:
                print("\nRECOMENDACIONES ADICIONALES:")
                for clave, valor in recomendaciones.items():
                    if valor:
                        print(f"\n{clave.capitalize()}:")
                        print(f"  {valor}")

        return True

    except Exception as e:
        print(f"Error al leer el plan: {str(e)}")
        return False


def main():
    """
    Función principal para ver los planes de ejercicio.
    """
    print("VISOR DE PLANES DE EJERCICIO")
    print("-" * 30)

    # Listar planes disponibles
    archivos = listar_planes_ejercicio()

    if not archivos:
        return

    print("\nPlanes de ejercicio disponibles:")
    for i, archivo in enumerate(archivos, 1):
        fecha_mod = datetime.fromtimestamp(os.path.getmtime(archivo)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        nombre_archivo = os.path.basename(archivo)
        print(f"{i}. {nombre_archivo} (modificado: {fecha_mod})")

    # Seleccionar plan para ver
    while True:
        try:
            seleccion = input(
                "\nSeleccione un número de plan para ver detalles (0 para salir): "
            )
            if seleccion == "0":
                break

            indice = int(seleccion) - 1
            if 0 <= indice < len(archivos):
                mostrar_detalles_plan(archivos[indice])
            else:
                print("Número no válido. Inténtelo de nuevo.")
        except ValueError:
            print("Por favor, ingrese un número válido.")
        except KeyboardInterrupt:
            print("\nSaliendo del programa...")
            break

        continuar = input("\n¿Desea ver otro plan? (s/n): ").lower() != "s"
        if continuar:
            break


if __name__ == "__main__":
    main()
