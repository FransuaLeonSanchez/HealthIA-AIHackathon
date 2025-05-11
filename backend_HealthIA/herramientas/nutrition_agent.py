from openai import OpenAI
import os
import base64
import json
from typing import Dict, Any, Optional, List
from herramientas.meal_plan_generator import MealPlanGenerator
from datetime import datetime


class NutritionAgent:
    """
    Agente especializado en proporcionar información y recomendaciones sobre nutrición
    y alimentación saludable para un único usuario, leyendo sus datos médicos.
    """

    # Nombres de archivo fijos (relativos a data_dir)
    USER_DATA_SOURCE_FILENAME = "medical_info.json"
    MEAL_PLAN_FILENAME = "plan_alimenticio.json"

    def __init__(
        self,
        api_key: Optional[str] = None,
        meals_js_path: str = "data/meal.json",
        data_dir: str = "data_usuario",
    ):
        """
        Inicializa el agente de nutrición con la API key de OpenAI.

        Args:
            api_key: Clave API de OpenAI. Si no se proporciona, intentará obtenerla de las variables de entorno.
            meals_js_path: Ruta al archivo de comidas.
            data_dir: Directorio donde se encuentra medical_info.json y donde se guardará plan_alimenticio.json.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Se requiere una clave API de OpenAI. Proporciónela como argumento o establezca la variable de entorno OPENAI_API_KEY."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.meal_plan_generator = MealPlanGenerator(meals_js_path, self.client)
        self.data_dir = data_dir
        # Ruta fija para leer la información médica del usuario
        self.user_data_source_path = os.path.join(
            self.data_dir, self.USER_DATA_SOURCE_FILENAME
        )
        # Ruta fija para guardar el plan alimenticio
        self.meal_plan_path = os.path.join(self.data_dir, self.MEAL_PLAN_FILENAME)

        # Crear el directorio de datos si no existe
        os.makedirs(self.data_dir, exist_ok=True)

        # Cargar datos del usuario (solo lectura)
        self.user_data: Optional[Dict[str, Any]] = self._load_data_from_file(
            self.user_data_source_path
        )
        # Cargar plan alimenticio existente si lo hay
        self.meal_plan: Optional[Dict[str, Any]] = self._load_data_from_file(
            self.meal_plan_path
        )

    def _load_data_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Carga datos desde un archivo JSON.

        Args:
            file_path: Ruta al archivo JSON.

        Returns:
            Diccionario con los datos o None si no existe el archivo o hay error.
        """
        if not os.path.exists(file_path):
            print(f"Advertencia: No se encontró el archivo de datos en {file_path}")
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar datos desde {file_path}: {str(e)}")
            return None

    def _save_meal_plan(self, meal_plan: Dict[str, Any]):
        """
        Guarda el plan alimenticio del usuario en el archivo fijo.

        Args:
            meal_plan: Diccionario con el plan alimenticio generado.
        """
        self.meal_plan = meal_plan  # Actualizar en memoria
        try:
            with open(self.meal_plan_path, "w", encoding="utf-8") as f:
                json.dump(meal_plan, f, ensure_ascii=False, indent=2)
            print(f"Plan alimenticio guardado en: {self.meal_plan_path}")
        except Exception as e:
            print(
                f"Error al guardar el plan alimenticio en {self.meal_plan_path}: {str(e)}"
            )

    def get_current_user_data(self) -> Optional[Dict[str, Any]]:
        """
        Devuelve los datos del usuario actualmente cargados (desde medical_info.json).

        Returns:
            Diccionario con los datos del usuario o None si no se pudieron cargar.
        """
        # Recargar por si el archivo fuente cambió externamente?
        # Por ahora, devolvemos la versión cargada en __init__
        return self.user_data

    def get_current_meal_plan(self) -> Optional[Dict[str, Any]]:
        """
        Devuelve el plan alimenticio actualmente cargado.

        Returns:
            Diccionario con el plan alimenticio o None si no hay plan guardado.
        """
        # Recargar desde el archivo para asegurar que tenemos la versión más actualizada
        self.meal_plan = self._load_data_from_file(self.meal_plan_path)
        return self.meal_plan

    def get_daily_menu(self, day: str) -> str:
        """
        Obtiene el menú para un día específico del plan alimenticio.

        Args:
            day: Día de la semana en inglés (Monday, Tuesday, etc.)

        Returns:
            Cadena de texto con el menú del día o mensaje de error.
        """
        # Recargar el plan alimenticio del archivo por si ha cambiado
        plan_data = self._load_data_from_file(self.meal_plan_path)

        if not plan_data:
            return "No se encontró un plan alimenticio. Genera uno primero usando el método create_meal_plan."

        # Buscar el día específico en el plan
        if isinstance(plan_data, list):
            # Formato simple: lista de objetos {day, meal}
            for item in plan_data:
                if item.get("day", "").lower() == day.lower():
                    return f"Menú para {item['day']}: {item['meal']}"

            # Si llegamos aquí, no se encontró el día
            return (
                f"No se encontró información para el día {day} en el plan alimenticio."
            )

        elif isinstance(plan_data, dict) and "plan_semanal" in plan_data:
            # Formato complejo del generador de planes
            plan_semanal = plan_data.get("plan_semanal", {})

            # Convertir el día a español si está en inglés (para compatibilidad)
            dia_espanol = self._translate_day_to_spanish(day)

            # Intentar primero con el nombre en español
            if dia_espanol in plan_semanal:
                comidas_dia = plan_semanal[dia_espanol]
                resultado = f"Menú para {dia_espanol}:\n"

                for comida, info in comidas_dia.items():
                    if comida != "totales_dia":  # Excluir los totales
                        if isinstance(info, dict) and "nombre" in info:
                            resultado += f"- {comida.capitalize()}: {info['nombre']}\n"
                        else:
                            resultado += f"- {comida.capitalize()}: {info}\n"

                return resultado

            # Si no encuentra el día en español, intentar con el nombre en inglés
            elif day in plan_semanal:
                comidas_dia = plan_semanal[day]
                resultado = f"Menú para {day}:\n"

                for comida, info in comidas_dia.items():
                    if comida != "totales_dia":  # Excluir los totales
                        if isinstance(info, dict) and "nombre" in info:
                            resultado += f"- {comida.capitalize()}: {info['nombre']}\n"
                        else:
                            resultado += f"- {comida.capitalize()}: {info}\n"

                return resultado

            # No se encontró el día
            return (
                f"No se encontró información para el día {day} en el plan alimenticio."
            )

        else:
            return "El formato del plan alimenticio no es compatible con esta función."

    def _translate_day_to_spanish(self, day: str) -> str:
        """
        Traduce el nombre del día de inglés a español.

        Args:
            day: Nombre del día en inglés.

        Returns:
            Nombre del día en español.
        """
        translations = {
            "monday": "Lunes",
            "tuesday": "Martes",
            "wednesday": "Miércoles",
            "thursday": "Jueves",
            "friday": "Viernes",
            "saturday": "Sábado",
            "sunday": "Domingo",
        }

        return translations.get(day.lower(), day)

    def get_today_menu(self) -> str:
        """
        Obtiene el menú del día actual basado en la fecha del sistema.

        Returns:
            Cadena de texto con el menú del día actual en formato 'Este es tu menú de tu día {nombre:...}'.
        """
        # Obtener el día actual en inglés
        days_of_week = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday",
        }

        # Obtener el número del día de la semana (0-6, donde 0 es lunes en formato ISO)
        current_day_num = datetime.now().weekday()
        current_day_name = days_of_week[current_day_num]

        # Obtener el menú del día utilizando la función existente
        menu_content = self.get_daily_menu(current_day_name)

        # Si no hay plan, devolver mensaje informativo
        if (
            "No se encontró" in menu_content
            or "No se encontró un plan alimenticio" in menu_content
        ):
            return "No tienes un plan alimenticio para hoy. Genera uno primero usando create_meal_plan."

        # Obtener el nombre del plan si está disponible
        plan_data = self._load_data_from_file(self.meal_plan_path)
        plan_name = "plan personalizado"

        if plan_data and isinstance(plan_data, dict) and "usuario" in plan_data:
            if "nombre" in plan_data["usuario"]:
                plan_name = plan_data["usuario"]["nombre"]

        # Devolver con el formato solicitado
        return f"Este es tu menú de tu día {{{plan_name}}}\n\n{menu_content}"

    def process(self, user_input: str) -> str:
        """
        Procesa una consulta general del usuario sobre nutrición y alimentación.
        Utiliza los datos cargados de medical_info.json para personalizar la respuesta si están disponibles.

        Args:
            user_input: Texto de entrada del usuario.

        Returns:
            Respuesta generada por el agente de nutrición.
        """
        # Verificar si el usuario está pidiendo el menú del día actual
        lower_input = user_input.lower()
        if (
            "menú" in lower_input or "menu" in lower_input or "comida" in lower_input
        ) and (
            "hoy" in lower_input
            or "día actual" in lower_input
            or "dia actual" in lower_input
        ):
            return self.get_today_menu()

        # Verificar si el usuario está pidiendo el menú de un día específico
        dias_semana = [
            "lunes",
            "martes",
            "miércoles",
            "miercoles",
            "jueves",
            "viernes",
            "sábado",
            "sabado",
            "domingo",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]

        for dia in dias_semana:
            if dia in lower_input and (
                "menú" in lower_input
                or "menu" in lower_input
                or "comida" in lower_input
                or "plan" in lower_input
            ):
                # Convertir nombre español a inglés si es necesario
                if dia in [
                    "lunes",
                    "martes",
                    "miércoles",
                    "miercoles",
                    "jueves",
                    "viernes",
                    "sábado",
                    "sabado",
                    "domingo",
                ]:
                    dia_traducido = {
                        "lunes": "Monday",
                        "martes": "Tuesday",
                        "miércoles": "Wednesday",
                        "miercoles": "Wednesday",
                        "jueves": "Thursday",
                        "viernes": "Friday",
                        "sábado": "Saturday",
                        "sabado": "Saturday",
                        "domingo": "Sunday",
                    }[dia]
                    return self.get_daily_menu(dia_traducido)
                else:
                    return self.get_daily_menu(dia.capitalize())

        if self.user_data:
            # Usar el método con datos si existen
            return self._process_with_loaded_user_data(user_input)
        else:
            # Usar el método general si no hay datos
            print(
                "Advertencia: No se encontraron datos del usuario. La respuesta será genérica."
            )
            system_prompt = """
            Eres un experto en nutrición que proporciona información precisa sobre alimentación
            saludable, nutrientes, dietas y recomendaciones alimentarias.
            Proporciona consejos claros, precisos y basados en evidencia científica.
            """
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
            )
            return response.choices[0].message.content or ""

    def _process_with_loaded_user_data(self, user_input: str) -> str:
        """
        Procesa la consulta del usuario utilizando los datos cargados (medical_info.json).
        No guarda cambios en los datos del usuario.

        Args:
            user_input: Texto de entrada del usuario.

        Returns:
            Respuesta generada por el agente de nutrición, personalizada según los datos cargados.
        """
        if not self.user_data:
            return "Error: No se pudieron cargar los datos del usuario para procesar la solicitud."

        # Si se solicita específicamente un plan alimenticio
        if (
            "plan alimenticio" in user_input.lower()
            or "dieta" in user_input.lower()
            or "plan nutricional" in user_input.lower()
        ):
            return self.create_meal_plan(
                user_input
            )  # Llama a crear plan con datos cargados

        # Para consultas generales, incluir los datos del usuario en el contexto
        # Adaptar los campos a los presentes en medical_info.json
        system_prompt = f"""
        Eres un experto en nutrición que proporciona información precisa sobre alimentación
        saludable, nutrientes, dietas y recomendaciones alimentarias, adaptadas al usuario.

        Datos del usuario (provenientes de su historial médico):
        - Nombre: {self.user_data.get('nombre', 'No especificado')}
        - Edad: {self.user_data.get('edad', 'No especificada')}
        - Peso: {self.user_data.get('peso', 'No especificado')} kg
        - Altura: {self.user_data.get('altura', 'No especificada')} m (Nota: Asegúrate si es cm o m en el JSON original)
        - Género: {self.user_data.get('genero', 'No especificado')}
        - Condiciones médicas: {', '.join(self.user_data.get('condiciones_medicas', [])) or 'Ninguna reportada'}
        - Alergias: {', '.join(self.user_data.get('alergias', [])) or 'Ninguna reportada'}
        - Medicamentos actuales: {json.dumps(self.user_data.get('medicamentos', []), indent=2) if self.user_data.get('medicamentos') else 'Ninguno reportado'}
        - Hábitos (Dieta): {self.user_data.get('habitos', {}).get('dieta', 'No especificada')}
        - Hábitos (Actividad Física): {self.user_data.get('habitos', {}).get('actividad_fisica', 'No especificada')}
        # Puedes añadir más campos relevantes del JSON aquí si es necesario

        Tus conocimientos incluyen:
        - Principios de una alimentación equilibrada
        - Propiedades y fuentes de diferentes nutrientes
        - Recomendaciones dietéticas adaptadas a condiciones médicas, alergias y medicamentos.
        - Alternativas alimentarias para diferentes restricciones dietéticas
        - Interacciones entre alimentos y medicamentos (si aplica)

        Proporciona consejos claros, precisos y personalizados según los datos del usuario.
        Considera sus condiciones, alergias y medicación al hacer recomendaciones.
        No promueves dietas extremas o no saludables.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
        )

        return response.choices[0].message.content or ""

    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Codifica una imagen a base64 para el procesamiento por la API.

        Args:
            image_path: Ruta al archivo de imagen.

        Returns:
            Imagen codificada en base64.
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def process_image(self, image_path: str, user_prompt: Optional[str], *args) -> str:
        """
        Procesa una imagen relacionada con nutrición y alimentación utilizando los datos cargados del usuario.

        Args:
            image_path: Ruta al archivo de imagen.
            user_prompt: Texto adicional proporcionado por el usuario sobre la imagen.

        Returns:
            Respuesta generada por el agente de nutrición sobre la imagen.
        """
        if not self.user_data:
            return "No se pueden procesar imágenes sin datos del usuario cargados (de medical_info.json)."

        try:
            base64_image = self.encode_image_to_base64(image_path)
        except Exception as e:
            return f"Error al procesar la imagen: {str(e)}"

        # Preparar el prompt para analizar la imagen con datos del usuario
        system_prompt = f"""
        Eres un experto nutricionista que analiza imágenes de alimentos, recetas, comidas y
        proporciona información nutricional detallada y recomendaciones adaptadas al usuario.

        Datos del usuario (provenientes de su historial médico):
        - Nombre: {self.user_data.get('nombre', 'No especificado')}
        - Edad: {self.user_data.get('edad', 'No especificada')}
        - Peso: {self.user_data.get('peso', 'No especificado')} kg
        - Altura: {self.user_data.get('altura', 'No especificada')} m
        - Género: {self.user_data.get('genero', 'No especificado')}
        - Condiciones médicas: {', '.join(self.user_data.get('condiciones_medicas', [])) or 'Ninguna reportada'}
        - Alergias: {', '.join(self.user_data.get('alergias', [])) or 'Ninguna reportada'}
        - Medicamentos actuales: {json.dumps(self.user_data.get('medicamentos', []), indent=2) if self.user_data.get('medicamentos') else 'Ninguno reportado'}
        - Hábitos (Dieta): {self.user_data.get('habitos', {}).get('dieta', 'No especificada')}
        - Hábitos (Actividad Física): {self.user_data.get('habitos', {}).get('actividad_fisica', 'No especificada')}
        # Objetivos (Inferir si es posible o indicar que no están explícitos en los datos médicos)

        Cuando analices esta imagen:
        1. Identifica los alimentos o platos presentes.
        2. Estima su valor nutricional aproximado (calorías, macronutrientes).
        3. Evalúa si es adecuado para el usuario considerando sus datos médicos (condiciones, alergias, etc.).
        4. Proporciona sugerencias o mejoras si corresponde.
        5. Menciona posibles ingredientes problemáticos según las alergias o condiciones del usuario.
        6. Si aplica, comenta posibles interacciones con sus medicamentos.

        Si la imagen muestra una receta o plan alimenticio, analízalo en detalle y comenta su idoneidad para el usuario.
        Si es una etiqueta nutricional, interpreta la información y explica si es adecuada.
        Si es un alimento o plato específico, proporciona alternativas más saludables si es necesario.

        Basa tus recomendaciones en evidencia científica y principios de nutrición sólidos, adaptados al contexto médico del usuario.
        """

        # Definir el prompt del usuario
        user_text_prompt = "Analiza esta imagen relacionada con alimentación y proporciona información nutricional detallada y personalizada."
        if user_prompt:
            user_text_prompt = f"{user_text_prompt} {user_prompt}"

        # Crear los mensajes para la API
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            },
        ]

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Considera gpt-4-vision-preview si necesitas análisis de imagen más potente
            messages=messages,
            max_tokens=1024,  # Ajusta según necesidad
        )

        return response.choices[0].message.content or ""

    def create_meal_plan(self, user_input: str) -> str:
        """
        Crea un plan alimenticio personalizado basado en los datos del usuario cargados (medical_info.json).
        Guarda el plan generado en plan_alimenticio.json.

        Args:
            user_input: Texto de entrada del usuario (puede influir en la explicación, no en la generación).

        Returns:
            Plan alimenticio personalizado explicado, o el JSON crudo si se solicita.
        """
        if not self.user_data:
            return "No se puede generar un plan alimenticio sin datos del usuario cargados (de medical_info.json)."

        # Usar el generador de planes para crear el plan alimenticio en formato JSON
        # Asegúrate de que MealPlanGenerator puede usar los campos de medical_info.json
        # Puede que necesites mapear/extraer campos específicos de self.user_data aquí
        # Por ejemplo, podrías necesitar pasar explícitamente objetivos o nivel de actividad
        # si no están directamente en medical_info.json pero se infieren o se piden
        print(
            f"Generando plan alimenticio con los datos de usuario: {list(self.user_data.keys())}"
        )
        meal_plan_json = self.meal_plan_generator.generate_meal_plan_json(
            self.user_data
        )

        # Convertir el JSON a un diccionario Python y guardar
        try:
            meal_plan_dict = json.loads(meal_plan_json)
            if "error" in meal_plan_dict:
                return (
                    f"Error al generar el plan alimenticio: {meal_plan_dict['error']}"
                )

            self._save_meal_plan(meal_plan_dict)  # Guarda en self.meal_plan_path
        except Exception as e:
            return f"Error al procesar o guardar el plan alimenticio generado: {str(e)}"

        # Si solo queremos el JSON crudo
        if (
            "json" in user_input.lower()
            or "raw" in user_input.lower()
            or "formato json" in user_input.lower()
        ):
            return meal_plan_json

        # Preparar el prompt para que GPT explique el plan
        system_prompt = f"""
        Eres un dietista-nutricionista profesional especializado en explicar planes alimenticios personalizados,
        considerando el historial médico del usuario.

        Debes explicar de forma clara y detallada el siguiente plan alimenticio generado para el usuario,
        basado en sus datos médicos.
        El plan se presenta en formato JSON.

        Datos del usuario utilizados (resumen):
        - Condiciones médicas: {', '.join(self.user_data.get('condiciones_medicas', [])) or 'Ninguna'}
        - Alergias: {', '.join(self.user_data.get('alergias', [])) or 'Ninguna'}
        - Medicamentos: {len(self.user_data.get('medicamentos', [])) if self.user_data.get('medicamentos') else 0}
        - Dieta habitual: {self.user_data.get('habitos', {}).get('dieta', 'No especificada')}
        # Añade otros datos relevantes usados si es necesario

        Haz un resumen claro, destacando:
        1. Las recomendaciones calóricas y de macronutrientes (si están en el JSON del plan).
        2. Los aspectos más importantes del plan semanal.
        3. Cómo este plan se adapta a las condiciones médicas, alergias y posibles interacciones
           con medicamentos del usuario.
        4. Si el plan considera las preferencias o hábitos alimenticios del usuario.

        Sé conciso pero informativo, enfocándote en la información más relevante y práctica para el usuario.
        Menciona explícitamente cómo se han tenido en cuenta sus datos médicos.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"""Aquí está el plan alimenticio generado basado en mis datos médicos:
{meal_plan_json}

Explica este plan de manera clara y concisa, indicando cómo considera mi salud.""",
                },
            ],
        )

        explanation = response.choices[0].message.content or ""

        # Añadir mensaje informativo sobre dónde se guardó el plan
        save_message = f"\n\nTu plan alimenticio ha sido guardado en formato JSON y se puede consultar en: {self.meal_plan_path}"
        save_message += "\nPuedes consultar tu plan completo con 'get_weekly_menu()' o un día específico con 'get_daily_menu(día)'."

        return f"{explanation}{save_message}"

    def get_weekly_menu(self) -> str:
        """
        Obtiene el menú completo de la semana del plan alimenticio.

        Returns:
            Cadena de texto con el menú completo de la semana o mensaje de error.
        """
        # Recargar el plan alimenticio del archivo por si ha cambiado
        plan_data = self._load_data_from_file(self.meal_plan_path)

        if not plan_data:
            return "No se encontró un plan alimenticio. Genera uno primero usando el método create_meal_plan."

        # Formato simple: lista de objetos {day, meal}
        if isinstance(plan_data, list):
            resultado = "Plan alimenticio semanal:\n\n"
            for item in plan_data:
                resultado += f"- {item.get('day', 'Día no especificado')}: {item.get('meal', 'Comida no especificada')}\n"

            return resultado

        # Formato complejo del generador de planes
        elif isinstance(plan_data, dict) and "plan_semanal" in plan_data:
            plan_semanal = plan_data.get("plan_semanal", {})
            resultado = "Plan alimenticio semanal:\n\n"

            for dia, comidas in plan_semanal.items():
                resultado += f"** {dia} **\n"

                for comida, info in comidas.items():
                    if comida != "totales_dia":  # Excluir los totales
                        if isinstance(info, dict) and "nombre" in info:
                            resultado += f"- {comida.capitalize()}: {info['nombre']}\n"
                        else:
                            resultado += f"- {comida.capitalize()}: {info}\n"

                resultado += "\n"

            # Añadir información nutricional si está disponible
            if "usuario" in plan_data and "datos_calculados" in plan_data["usuario"]:
                datos = plan_data["usuario"]["datos_calculados"]
                resultado += "\nRecomendaciones nutricionales diarias:\n"
                if "calorias_diarias_recomendadas" in datos:
                    resultado += (
                        f"- Calorías: {datos['calorias_diarias_recomendadas']} kcal\n"
                    )
                if "proteinas_gramos_diarios" in datos:
                    resultado += f"- Proteínas: {datos['proteinas_gramos_diarios']} g\n"
                if "carbohidratos_gramos_diarios" in datos:
                    resultado += (
                        f"- Carbohidratos: {datos['carbohidratos_gramos_diarios']} g\n"
                    )
                if "grasas_gramos_diarios" in datos:
                    resultado += f"- Grasas: {datos['grasas_gramos_diarios']} g\n"

            return resultado

        else:
            return "El formato del plan alimenticio no es compatible con esta función."

    def get_meal_plan_json(self) -> str:
        """
        Obtiene el plan alimenticio actual como una cadena JSON formateada.

        Returns:
            Cadena de texto con el plan alimenticio en formato JSON, o mensaje de error si no hay plan.
        """
        # Recargar el plan desde el archivo
        plan_data = self._load_data_from_file(self.meal_plan_path)

        if not plan_data:
            return "No se encontró un plan alimenticio. Genera uno primero usando el método create_meal_plan."

        # Convertir a cadena JSON formateada
        try:
            return json.dumps(plan_data, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Error al formatear el plan alimenticio como JSON: {str(e)}"
