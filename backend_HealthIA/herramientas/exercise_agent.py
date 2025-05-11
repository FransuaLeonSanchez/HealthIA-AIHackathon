from openai import OpenAI
import os
import base64
import json
from datetime import datetime
from typing import Dict, Any, Optional


class ExerciseAgent:
    """
    Agente especializado en proporcionar información y recomendaciones sobre ejercicios físicos.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el agente de ejercicios con la API key de OpenAI.

        Args:
            api_key: Clave API de OpenAI. Si no se proporciona, intentará obtenerla de las variables de entorno.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Se requiere una clave API de OpenAI. Proporciónela como argumento o establezca la variable de entorno OPENAI_API_KEY."
            )

        self.client = OpenAI(api_key=self.api_key)

    def process(self, user_input: str) -> str:
        """
        Procesa la consulta del usuario relacionada con ejercicios.

        Args:
            user_input: Texto de entrada del usuario.

        Returns:
            Respuesta generada por el agente de ejercicios.
        """
        system_prompt = """
        Eres un entrenador personal experto que proporciona información precisa sobre ejercicios, 
        rutinas de entrenamiento, técnicas correctas y recomendaciones personalizadas.
        
        Tus conocimientos incluyen:
        - Diferentes tipos de ejercicios (cardiovasculares, fuerza, flexibilidad, etc.)
        - Técnicas correctas para evitar lesiones
        - Rutinas para diferentes objetivos (pérdida de peso, ganancia muscular, resistencia, etc.)
        - Adaptaciones para diferentes niveles de condición física
        - Recomendaciones para problemas específicos
        
        Proporciona respuestas claras, precisas y personalizadas. Cuando sea apropiado, 
        sugiere ejercicios específicos con instrucciones detalladas.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
        )

        return response.choices[0].message.content or ""

    def process_with_user_data(self, user_input: str, user_data: Dict[str, Any]) -> str:
        """
        Procesa la consulta del usuario utilizando sus datos personales para proporcionar
        información sobre ejercicios personalizada.

        Args:
            user_input: Texto de entrada del usuario.
            user_data: Diccionario con los datos personales del usuario.

        Returns:
            Respuesta generada por el agente de ejercicios, personalizada según los datos del usuario.
        """
        system_prompt = f"""
        Eres un entrenador personal experto que proporciona información precisa sobre ejercicios, 
        rutinas de entrenamiento, técnicas correctas y recomendaciones personalizadas.
        
        Datos del usuario:
        - Nombre: {user_data.get('nombre', 'No especificado')}
        - Edad: {user_data.get('edad', 'No especificada')}
        - Peso: {user_data.get('peso', 'No especificado')} kg
        - Altura: {user_data.get('altura', 'No especificada')} cm
        - Género: {user_data.get('genero', 'No especificado')}
        - Condiciones médicas: {', '.join(user_data.get('condiciones_medicas', [])) or 'Ninguna reportada'}
        - Objetivos: {', '.join(user_data.get('objetivos', [])) or 'No especificados'}
        - Nivel de actividad: {user_data.get('nivel_actividad', 'No especificado')}
        
        Tus conocimientos incluyen:
        - Diferentes tipos de ejercicios (cardiovasculares, fuerza, flexibilidad, etc.)
        - Técnicas correctas para evitar lesiones
        - Rutinas para diferentes objetivos (pérdida de peso, ganancia muscular, resistencia, etc.)
        - Adaptaciones para diferentes niveles de condición física
        - Recomendaciones para problemas específicos
        
        Proporciona respuestas claras, precisas y personalizadas según los datos del usuario. 
        Cuando sea apropiado, sugiere ejercicios específicos con instrucciones detalladas y 
        adaptados a las características particulares del usuario.
        
        Ten especial cuidado con las condiciones médicas informadas y adapta tus recomendaciones 
        para que sean seguras y apropiadas para el usuario.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
        )

        return response.choices[0].message.content or ""

    def generar_plan_semanal_ejercicio(
        self, user_data: Dict[str, Any], instrucciones_adicionales: str = ""
    ) -> str:
        """
        Genera un plan de ejercicio semanal personalizado y lo guarda como JSON.

        Args:
            user_data: Diccionario con los datos personales del usuario.
            instrucciones_adicionales: Instrucciones específicas para el plan.

        Returns:
            Mensaje de confirmación con la ruta del archivo guardado.
        """
        system_prompt = f"""
        Eres un entrenador personal experto especializado en crear planes de ejercicio semanales personalizados.
        
        Datos del usuario:
        - Nombre: {user_data.get('nombre', 'No especificado')}
        - Edad: {user_data.get('edad', 'No especificada')}
        - Peso: {user_data.get('peso', 'No especificado')} kg
        - Altura: {user_data.get('altura', 'No especificada')} cm
        - Género: {user_data.get('genero', 'No especificado')}
        - Condiciones médicas: {', '.join(user_data.get('condiciones_medicas', [])) or 'Ninguna reportada'}
        - Objetivos: {', '.join(user_data.get('objetivos', [])) or 'No especificados'}
        - Nivel de actividad: {user_data.get('nivel_actividad', 'No especificado')}
        
        Crea un plan de ejercicio semanal detallado que:
        1. Sea apropiado para el nivel de actividad del usuario
        2. Se alinee con sus objetivos de fitness
        3. Tenga en cuenta sus condiciones médicas
        4. Incluya variedad de ejercicios para cada día de la semana
        5. Especifique series, repeticiones y descansos para cada ejercicio
        6. Incluya días de descanso cuando sea apropiado
        
        El plan debe tener EXACTAMENTE esta estructura JSON:
        {{
            "metadata": {{
                "usuario_id": "{user_data.get('usuario_id', 'usuario')}",
                "nombre": "{user_data.get('nombre', 'No especificado')}",
                "fecha_creacion": "{datetime.now().strftime('%Y-%m-%d')}",
                "objetivos": {json.dumps(user_data.get('objetivos', []))}
            }},
            "plan_semanal": {{
                "lunes": [
                    {{
                        "nombre": "NOMBRE_EJERCICIO",
                        "tipo": "TIPO_EJERCICIO",
                        "series": NUMERO_SERIES,
                        "repeticiones": NUMERO_REPETICIONES,
                        "descanso_segundos": TIEMPO_DESCANSO,
                        "descripcion": "DESCRIPCION_DETALLADA",
                        "instrucciones": ["PASO1", "PASO2", "PASO3"]
                    }}
                ],
                "martes": [],
                "miercoles": [],
                "jueves": [],
                "viernes": [],
                "sabado": [],
                "domingo": []
            }},
            "recomendaciones_adicionales": {{
                "calentamiento": "DESCRIPCION_CALENTAMIENTO",
                "enfriamiento": "DESCRIPCION_ENFRIAMIENTO",
                "hidratacion": "RECOMENDACIONES_HIDRATACION",
                "nutricion": "RECOMENDACIONES_NUTRICIONALES"
            }}
        }}
        
        La respuesta debe contener SOLAMENTE el JSON completo, nada más. Asegúrate de que sea un JSON válido.
        Para cada día incluye al menos 2-3 ejercicios o marca como día de descanso dejando el array vacío.
        """

        user_prompt = "Genera un plan de ejercicios semanal personalizado."
        if instrucciones_adicionales:
            user_prompt += f" {instrucciones_adicionales}"

        try:
            print("Enviando solicitud a OpenAI para generar plan de ejercicio...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )

            # Obtener el contenido JSON de la respuesta
            json_content = response.choices[0].message.content

            # Verificar que tenemos un JSON válido
            try:
                plan_data = json.loads(json_content)
                print("JSON recibido correctamente desde la API.")
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"La respuesta de la API no es un JSON válido: {str(e)}"
                )

            # Crear directorio data_usuario si no existe
            data_dir = os.path.abspath("data_usuario")
            os.makedirs(data_dir, exist_ok=True)
            print(f"Directorio para datos asegurado: {data_dir}")

            # Generar nombre de archivo único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            usuario_id = user_data.get("usuario_id", "usuario")
            nombre_archivo = f"plan_ejercicio_{usuario_id}_{timestamp}.json"
            ruta_archivo = os.path.join(data_dir, nombre_archivo)

            # Guardar el plan como archivo JSON
            print(f"Guardando archivo en: {ruta_archivo}")
            with open(ruta_archivo, "w", encoding="utf-8") as archivo:
                # Guardar JSON con formato para mejor legibilidad
                json.dump(plan_data, archivo, ensure_ascii=False, indent=2)

            print(f"Archivo JSON guardado exitosamente en: {ruta_archivo}")
            return f"Plan de ejercicio semanal generado y guardado en: {ruta_archivo}"

        except Exception as e:
            error_msg = f"Error al generar o guardar el plan de ejercicio: {str(e)}"
            print(error_msg)
            return error_msg

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

    def process_image(
        self, image_path: str, user_prompt: Optional[str], user_data: Dict[str, Any]
    ) -> str:
        """
        Procesa una imagen relacionada con ejercicios físicos utilizando los datos del usuario.

        Args:
            image_path: Ruta al archivo de imagen.
            user_prompt: Texto adicional proporcionado por el usuario sobre la imagen.
            user_data: Diccionario con los datos personales del usuario.

        Returns:
            Respuesta generada por el agente de ejercicios sobre la imagen.
        """
        try:
            base64_image = self.encode_image_to_base64(image_path)
        except Exception as e:
            return f"Error al procesar la imagen: {str(e)}"

        # Preparar el prompt para analizar la imagen
        system_prompt = f"""
        Eres un entrenador personal experto que analiza imágenes relacionadas con ejercicios,
        actividad física, equipos de gimnasio, postura, técnica deportiva y dispositivos de fitness.
        
        Datos del usuario:
        - Nombre: {user_data.get('nombre', 'No especificado')}
        - Edad: {user_data.get('edad', 'No especificada')}
        - Peso: {user_data.get('peso', 'No especificado')} kg
        - Altura: {user_data.get('altura', 'No especificada')} cm
        - Género: {user_data.get('genero', 'No especificado')}
        - Condiciones médicas: {', '.join(user_data.get('condiciones_medicas', [])) or 'Ninguna reportada'}
        - Objetivos: {', '.join(user_data.get('objetivos', [])) or 'No especificados'}
        - Nivel de actividad: {user_data.get('nivel_actividad', 'No especificado')}
        
        Al analizar esta imagen:
        1. Identifica el tipo de ejercicio, equipo o actividad mostrada
        2. Evalúa la técnica o postura si es visible (sin juzgar, solo informar)
        3. Proporciona recomendaciones para mejorar o adaptar el ejercicio al nivel y objetivos del usuario
        4. Sugiere variaciones o alternativas si corresponde
        5. Considera las condiciones médicas del usuario al dar recomendaciones
        
        Si la imagen muestra:
        - Un ejercicio específico: explica la técnica correcta, músculos trabajados y beneficios
        - Un equipo de gimnasio: describe su uso adecuado y ejercicios posibles con él
        - Datos de entrenamiento (smartwatch, app): interpreta los datos y sugiere mejoras
        - Un plan de entrenamiento: analiza su idoneidad para los objetivos del usuario
        
        Proporciona consejos prácticos, científicamente respaldados y adaptados a las características
        particulares del usuario. Enfatiza la seguridad y la correcta ejecución.
        """

        # Definir el prompt del usuario
        user_text_prompt = "Analiza esta imagen relacionada con ejercicios o actividad física y proporciona información detallada."
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
            model="gpt-4o-mini", messages=messages
        )

        return response.choices[0].message.content or ""
