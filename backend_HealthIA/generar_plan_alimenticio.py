import json
import os
from openai import OpenAI
from herramientas.meal_plan_generator import MealPlanGenerator
from dotenv import load_dotenv

# Cargar variables de entorno (para obtener OPENAI_API_KEY)
load_dotenv()


def generar_plan_alimenticio():
    """
    Genera un plan alimenticio personalizado basado en los datos médicos del usuario
    usando el catálogo de comidas de meal.json.
    """
    # Ruta al archivo de comidas (ajustar si es necesario)
    meals_json_path = "data/meal.json"

    # Ruta al archivo de datos médicos del usuario
    user_data_path = "data_usuario/medical_info.json"

    # Ruta donde se guardará el plan alimenticio
    output_path = "data_usuario/plan_alimenticio.json"

    # Verificar que existen los archivos necesarios
    if not os.path.exists(meals_json_path):
        print(f"Error: No se encontró el archivo de comidas en {meals_json_path}")
        return

    if not os.path.exists(user_data_path):
        print(f"Error: No se encontró el archivo de datos médicos en {user_data_path}")
        return

    # Inicializar cliente OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(
            "Error: No se encontró la clave API de OpenAI en las variables de entorno."
        )
        return

    client = OpenAI(api_key=api_key)

    # Cargar datos del usuario
    try:
        with open(user_data_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            print(f"Datos de usuario cargados correctamente desde {user_data_path}")
    except Exception as e:
        print(f"Error al cargar los datos del usuario: {str(e)}")
        return

    # Inicializar el generador de planes alimenticios
    meal_plan_generator = MealPlanGenerator(meals_json_path, client)

    # Generar el plan alimenticio
    print("Generando plan alimenticio...")
    meal_plan = meal_plan_generator.generate_meal_plan(user_data)

    # Guardar el plan generado
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(meal_plan, f, ensure_ascii=False, indent=2)
        print(f"Plan alimenticio generado y guardado correctamente en {output_path}")
    except Exception as e:
        print(f"Error al guardar el plan alimenticio: {str(e)}")
        return


if __name__ == "__main__":
    generar_plan_alimenticio()
