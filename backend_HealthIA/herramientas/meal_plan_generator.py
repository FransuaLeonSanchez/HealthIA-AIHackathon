import json
import os
from typing import Dict, Any, List, Optional
from openai import OpenAI


class MealPlanGenerator:
    """
    Generador de planes alimenticios personalizados utilizando IA,
    basado en un catálogo de comidas disponibles y datos del usuario.
    """

    def __init__(self, meals_json_path: str, client: OpenAI):
        """
        Inicializa el generador de planes alimenticios.

        Args:
            meals_json_path: Ruta al archivo JSON de comidas (ej: "data/meals.json").
            client: Cliente de OpenAI inicializado.
        """
        self.meals_json_path = meals_json_path
        self.client = client
        self.meals_data = self._load_meals_data()

    def _load_meals_data(self) -> List[Dict[str, Any]]:
        """
        Carga los datos de comidas desde el archivo JSON especificado.

        Returns:
            Lista de diccionarios con la información de cada comida o lista vacía si hay error.
        """
        if not os.path.exists(self.meals_json_path):
            print(
                f"Error: No se encontró el archivo de comidas en {self.meals_json_path}"
            )
            return []
        try:
            with open(self.meals_json_path, "r", encoding="utf-8") as file:
                # Cargar directamente el JSON
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON desde {self.meals_json_path}: {str(e)}")
            return []
        except Exception as e:
            print(
                f"Error inesperado al cargar los datos de comidas desde {self.meals_json_path}: {str(e)}"
            )
            return []

    def generate_meal_plan(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un plan alimenticio personalizado para el usuario utilizando la IA de OpenAI.

        Args:
            user_data: Diccionario con los datos personales y médicos del usuario.
                       Debe incluir campos como 'nombre', 'edad', 'peso', 'altura', 'genero',
                       'nivel_actividad', 'objetivos', 'restricciones_alimentarias', 'alergias',
                       'condiciones_medicas'.

        Returns:
            Diccionario con el plan alimenticio generado por la IA en formato estructurado,
            o un diccionario de error si falla la generación.
        """
        if not self.meals_data:
            return {
                "error": "No se pudieron cargar los datos de comidas. No se puede generar el plan."
            }
        if not self.client:
            return {
                "error": "Cliente OpenAI no proporcionado. No se puede generar el plan."
            }

        # Extraer datos relevantes del usuario para el prompt
        user_info_str = f"""
        - Nombre: {user_data.get('nombre', 'No especificado')}
        - Edad: {user_data.get('edad', 'No especificada')}
        - Peso: {user_data.get('peso', 'No especificado')} kg
        - Altura: {user_data.get('altura', 'No especificada')} (asumir cm si no se especifica unidad)
        - Género: {user_data.get('genero', 'No especificado')}
        - Nivel de actividad física: {user_data.get('habitos', {}).get('actividad_fisica', 'No especificado')} (ej: sedentario, ligero, moderado, activo, muy activo)
        - Objetivos nutricionales/salud: {', '.join(user_data.get('objetivos', [])) or 'No especificados'} (ej: perder peso, ganar músculo, comer saludable, controlar diabetes)
        - Condiciones médicas relevantes: {', '.join(user_data.get('condiciones_medicas', [])) or 'Ninguna reportada'}
        - Alergias alimentarias: {', '.join(user_data.get('alergias', [])) or 'Ninguna reportada'}
        - Restricciones dietéticas (ej: vegetariano, vegano, sin gluten, sin lactosa): {', '.join(user_data.get('restricciones_alimentarias', [])) or 'Ninguna reportada'}
        - Preferencias alimentarias: {', '.join(user_data.get('preferencias_alimentarias', [])) or 'No especificadas'}
        """

        # Convertir la lista de comidas a una cadena JSON para incluirla en el prompt
        # Asegurarse de que no sea demasiado larga para los límites del modelo
        meals_json_str = json.dumps(self.meals_data, ensure_ascii=False, indent=2)
        # Considerar truncar o resumir si meals_json_str es muy grande

        system_prompt = """
        Eres un dietista-nutricionista experto encargado de crear planes alimenticios semanales personalizados.
        Tu objetivo es generar un plan de 7 días (Lunes a Domingo) con 4 comidas diarias (Desayuno, Almuerzo, Merienda, Cena).
        Debes basarte ESTRICTAMENTE en la lista de comidas proporcionada y adaptarlo a los datos y necesidades del usuario.

        Instrucciones:
        1.  Analiza los datos del usuario: edad, peso, altura, género, nivel de actividad, objetivos, condiciones médicas, alergias y restricciones.
        2.  Calcula o estima las necesidades calóricas y de macronutrientes diarias aproximadas para el usuario según sus datos y objetivos.
        3.  Revisa la lista de comidas disponibles proporcionada en formato JSON. Cada comida tiene nombre, categoría (Breakfast, Lunch, Snack, Dinner), información nutricional (energía, proteínas, carbohidratos, grasas), tiempo de preparación e imagen.
        4.  Selecciona comidas ÚNICAMENTE de la lista proporcionada para cada una de las 28 ranuras (7 días x 4 comidas).
        5.  Asegúrate de que las comidas seleccionadas sean coherentes con las alergias, restricciones y condiciones médicas del usuario. Si una comida contiene un alérgeno listado, NO la incluyas. Si una comida no es adecuada para una condición médica (ej: alto en azúcar para diabetes), evítala.
        6.  Intenta variar las comidas a lo largo de la semana para evitar la monotonía, pero puedes repetir comidas si es necesario o si la lista es limitada.
        7.  El plan debe intentar acercarse a las necesidades calóricas y de macronutrientes estimadas, distribuidas razonablemente a lo largo del día y la semana.
        8.  El resultado DEBE ser un objeto JSON VÁLIDO con la siguiente estructura exacta:

            {
              "usuario": {
                "nombre": "Nombre del Usuario",
                "datos_calculados": { // Datos estimados por ti
                  "calorias_diarias_recomendadas": <numero>,
                  "proteinas_gramos_diarios": <numero>,
                  "carbohidratos_gramos_diarios": <numero>,
                  "grasas_gramos_diarios": <numero>
                }
              },
              "justificacion_general": "Breve explicación de cómo el plan se adapta al usuario (objetivos, restricciones, etc.) y por qué se eligieron ciertos enfoques.",
              "plan_semanal": {
                "Lunes": {
                  "desayuno": { "nombre": "Nombre Comida Desayuno Lunes", "energia_kcal": <num>, "proteinas_g": <num>, "carbohidratos_g": <num>, "grasas_g": <num>, "imagen_url": "url..." },
                  "almuerzo": { "nombre": "Nombre Comida Almuerzo Lunes", ... },
                  "merienda": { "nombre": "Nombre Comida Merienda Lunes", ... },
                  "cena": { "nombre": "Nombre Comida Cena Lunes", ... },
                  "totales_dia": { "energia_kcal": <num>, "proteinas_g": <num>, "carbohidratos_g": <num>, "grasas_g": <num> }
                },
                "Martes": { ... }, // Estructura similar para Martes a Domingo
                ...
                "Domingo": { ... }
              },
              "advertencias": ["Lista de advertencias si alguna restricción fue difícil de cumplir", "O si alguna comida podría interactuar con condiciones/medicamentos no especificados explícitamente"]
            }

        Consideraciones Adicionales:
        - Si la lista de comidas es muy limitada o no permite cumplir todas las restricciones, indícalo en el campo "advertencias".
        - Prioriza la seguridad (alergias, condiciones médicas) sobre la variedad o el cumplimiento exacto de macros si hay conflicto.
        - No inventes comidas que no estén en la lista proporcionada.
        - Devuelve SÓLO el objeto JSON, sin texto introductorio ni explicaciones adicionales fuera del JSON.
        """

        user_content = f"""
        Por favor, genera el plan alimenticio semanal en formato JSON para el siguiente usuario:

        **Datos del Usuario:**
        {user_info_str}

        **Lista de Comidas Disponibles (JSON):**
        ```json
        {meals_json_str}
        ```

        Genera el plan siguiendo estrictamente las instrucciones y la estructura JSON requerida en el prompt del sistema. Asegúrate de que el JSON sea válido.
        """

        try:
            print("Generando plan alimenticio con IA...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
            )

            # Extraer el contenido JSON de la respuesta
            response_content = response.choices[0].message.content
            if not response_content:
                return {"error": "La respuesta de la IA estaba vacía."}

            # Parsear la respuesta JSON
            meal_plan = json.loads(response_content)
            print("Plan alimenticio generado por IA recibido.")
            return meal_plan

        except json.JSONDecodeError as e:
            print(f"Error: La respuesta de la IA no era un JSON válido: {str(e)}")
            print(f"Respuesta recibida: {response_content}")
            return {
                "error": "La respuesta de la IA no tenía el formato JSON esperado.",
                "raw_response": response_content,
            }
        except Exception as e:
            print(f"Error inesperado durante la llamada a la API de OpenAI: {str(e)}")
            return {"error": f"Error inesperado al generar el plan: {str(e)}"}

    def generate_meal_plan_json(self, user_data: Dict[str, Any]) -> str:
        """
        Genera un plan alimenticio personalizado para el usuario utilizando IA
        y lo devuelve en formato JSON (string).

        Args:
            user_data: Diccionario con los datos personales del usuario.

        Returns:
            Plan alimenticio personalizado en formato JSON (string),
            o un JSON de error si falla la generación.
        """
        meal_plan_dict = self.generate_meal_plan(user_data)
        return json.dumps(meal_plan_dict, ensure_ascii=False, indent=2)


# Eliminar o comentar el bloque __main__ ya que ahora depende de un cliente OpenAI
# if __name__ == "__main__":
#     # ... (ya no se puede ejecutar directamente sin un cliente OpenAI y datos reales)
#     pass
