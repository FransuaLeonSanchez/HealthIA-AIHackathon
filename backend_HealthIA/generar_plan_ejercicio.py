#!/usr/bin/env python
# -*- coding: utf-8 -*-

from herramientas.exercise_agent import ExerciseAgent
import os
import json
import sys
from dotenv import load_dotenv


def obtener_datos_usuario():
    """
    Obtiene los datos del usuario desde el archivo _datos.json o usa datos de ejemplo.
    """
    ruta_datos = os.path.join("data_usuario", "_datos.json")

    # Verificar si existe archivo de datos
    if os.path.exists(ruta_datos):
        try:
            with open(ruta_datos, "r", encoding="utf-8") as f:
                print(f"Cargando datos de usuario desde: {os.path.abspath(ruta_datos)}")
                return json.load(f)
        except Exception as e:
            print(f"Error al leer datos del usuario: {str(e)}")

    # Si no existe el archivo o hubo un error, usar datos de ejemplo
    print("No se encontró archivo de datos de usuario, usando datos de ejemplo")
    return {
        "usuario_id": "user123",
        "nombre": "María López",
        "edad": 35,
        "peso": 68,
        "altura": 165,
        "genero": "femenino",
        "condiciones_medicas": ["dolor leve de rodilla"],
        "objetivos": ["tonificación muscular", "mejorar resistencia", "reducir estrés"],
        "nivel_actividad": "intermedio",
    }


def main():
    """
    Ejemplo de generación de un plan de ejercicio semanal personalizado
    usando el agente de ejercicios.
    """
    # Cargar variables de entorno
    load_dotenv()

    # Verificar que existe la clave API de OpenAI
    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "Error: No se encontró la clave API de OpenAI en las variables de entorno."
        )
        print(
            "Por favor, crea un archivo .env con tu clave API como OPENAI_API_KEY=tu_clave_api"
        )
        return

    # Asegurarse de que el directorio data_usuario existe
    data_dir = os.path.abspath("data_usuario")
    os.makedirs(data_dir, exist_ok=True)
    print(f"Directorio para guardar datos verificado: {data_dir}")

    try:
        # Crear el agente de ejercicios
        print("Inicializando agente de ejercicio...")
        agente = ExerciseAgent()

        # Obtener datos del usuario
        datos_usuario = obtener_datos_usuario()

        print(f"Generando plan para: {datos_usuario.get('nombre', 'Usuario')}")

        # Solicitar instrucciones adicionales al usuario
        print("\nPuedes agregar instrucciones específicas para tu plan de ejercicios.")
        print(
            "Por ejemplo: 'Ejercicios en casa', 'Énfasis en cardio', 'Para principiantes', etc."
        )
        instrucciones = input(
            "Instrucciones adicionales (presiona Enter para omitir): "
        )

        if not instrucciones:
            instrucciones = "Me gustaría ejercicios que pueda hacer en casa con mínimo equipamiento. Prefiero sesiones de 45 minutos máximo."
            print(f"Usando instrucciones predeterminadas: {instrucciones}")

        print("\nGenerando plan de ejercicio semanal personalizado...")
        # Generar y guardar el plan de ejercicio semanal
        resultado = agente.generar_plan_semanal_ejercicio(datos_usuario, instrucciones)

        # Mostrar el resultado
        print(resultado)

        # Extraer la ruta del archivo del mensaje de resultado
        ruta_archivo = resultado.split(": ")[-1]

        # Verificar que el archivo existe
        if os.path.exists(ruta_archivo):
            print(
                f"Verificado: El archivo JSON se creó correctamente en: {os.path.abspath(ruta_archivo)}"
            )

            # Leer y mostrar parte del contenido para verificación
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                contenido = json.load(f)

            print("\nResumen del plan generado:")
            print(
                f"Usuario: {contenido.get('metadata', {}).get('nombre', 'No especificado')}"
            )
            print(
                f"Fecha creación: {contenido.get('metadata', {}).get('fecha_creacion', 'No especificada')}"
            )
            print("Días con ejercicios programados:")
            for dia in contenido.get("plan_semanal", {}).keys():
                num_ejercicios = len(contenido["plan_semanal"][dia])
                if num_ejercicios > 0:
                    print(f"  - {dia.capitalize()}: {num_ejercicios} ejercicio(s)")
                else:
                    print(f"  - {dia.capitalize()}: Descanso")

            print(
                "\nPara ver este plan en detalle, ejecuta: python ver_planes_ejercicio.py"
            )
        else:
            print(
                f"Error: No se encontró el archivo JSON en la ruta especificada: {ruta_archivo}"
            )

    except Exception as e:
        print(f"Error al generar el plan de ejercicio: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
