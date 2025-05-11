from openai import OpenAI
import os
import base64
from typing import Any, Dict, Optional


class SupervisorAgent:
    """
    Agente supervisor que coordina la interacción entre los agentes especializados.
    Actúa como el prompt principal del sistema.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el agente supervisor con la API key de OpenAI.

        Args:
            api_key: Clave API de OpenAI. Si no se proporciona, intentará obtenerla de las variables de entorno.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Se requiere una clave API de OpenAI. Proporciónela como argumento o establezca la variable de entorno OPENAI_API_KEY."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.agents = {}
        # Inicializar datos del usuario
        self.user_data = {
            "nombre": "",
            "edad": 0,
            "peso": 0.0,
            "altura": 0.0,
            "genero": "",
            "condiciones_medicas": [],
            "alergias": [],
            "restricciones_alimentarias": [],
            "objetivos": [],
            "nivel_actividad": "",
            "preferencias_alimentarias": [],
        }

        # Instrucción Markdown para los agentes
        self.markdown_instruction = """
        INSTRUCCIÓN DE FORMATO IMPORTANTE: 
        Cuando generes listas, planes o contenido estructurado, utiliza formato Markdown:
        
        # Encabezado principal (Título)
        ## Encabezado secundario (Sección)
        ### Encabezado terciario (Subsección)
        #### Encabezado de cuarto nivel
        ##### Encabezado de quinto nivel
        ###### Encabezado de sexto nivel
        
        Para listas:
        * Elemento de lista con viñeta
        * Otro elemento
          * Subítem anidado
          * Otro subítem
        
        Para listas numeradas:
        1. Primer paso
        2. Segundo paso
           1. Subpaso 1
           2. Subpaso 2
        
        Para enfatizar texto:
        **texto en negrita**
        *texto en cursiva*
        
        Para bloques de código o ejemplos:
        ```
        código o ejemplo aquí
        ```
        
        Para tablas:
        | Columna 1 | Columna 2 |
        |-----------|-----------|
        | Valor 1   | Valor 2   |
        """

    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """
        Registra un agente especializado para ser utilizado por el supervisor.

        Args:
            agent_name: Nombre único del agente.
            agent_instance: Instancia del agente especializado.
        """
        self.agents[agent_name] = agent_instance

    def update_user_data(self, data: Dict[str, Any]) -> None:
        """
        Actualiza los datos del usuario.

        Args:
            data: Diccionario con los datos a actualizar.
        """
        for key, value in data.items():
            if key in self.user_data:
                self.user_data[key] = value

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

    def process_image(self, image_path: str, user_prompt: Optional[str] = None) -> str:
        """
        Procesa una imagen y determina qué agente debe manejarla.

        Args:
            image_path: Ruta al archivo de imagen.
            user_prompt: Texto adicional proporcionado por el usuario sobre la imagen.

        Returns:
            Respuesta generada por el sistema de agentes.
        """
        # Codificar la imagen a base64
        try:
            base64_image = self.encode_image_to_base64(image_path)
        except Exception as e:
            return f"[Agente Supervisor] Error al procesar la imagen: {str(e)}"

        # Analizar la imagen para determinar qué agente debe procesarla
        prompt = f"""
        Analiza la siguiente imagen y determina qué agente especializado 
        debe manejarla. Los agentes disponibles son: {list(self.agents.keys())}
        
        Reglas para determinar el agente:
        - Si la imagen muestra algo médico (medicamentos, condiciones médicas, etc.), asignar al agente 'medico'
        - Si la imagen muestra comida, recetas, ingredientes o está relacionada con nutrición, asignar al agente 'nutricion'
        - Si la imagen muestra ejercicios, equipos de gimnasio, actividades físicas o dispositivos fitness, asignar al agente 'ejercicio'
        - Si no corresponde claramente a ninguna categoría, responder con 'ninguno'
        
        Texto adicional del usuario: {user_prompt or ''}
        
        Responde SOLO con el nombre del agente más adecuado: 'medico', 'nutricion', 'ejercicio' o 'ninguno'.
        """

        # Preparar mensajes para la API
        messages = [
            {
                "role": "system",
                "content": "Eres un analizador de imágenes que determina qué agente especializado debe procesarlas.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
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

        # Extraer el nombre del agente de la respuesta
        agent_selection = response.choices[0].message.content
        if agent_selection:
            agent_selection = agent_selection.strip().lower()
        else:
            agent_selection = "ninguno"

        print(
            f"DEBUG [process_image]: Clasificación del LLM para la imagen: {agent_selection}"
        )

        # Verificar si un agente específico fue identificado
        if agent_selection in self.agents:
            selected_agent = self.agents[agent_selection]

            # Agregar instrucción de formato Markdown al procesar la imagen
            md_prompt = user_prompt
            if md_prompt:
                md_prompt = f"{md_prompt}\n\n{self.markdown_instruction}"
            else:
                md_prompt = self.markdown_instruction

            # Procesar la imagen con el agente seleccionado
            if hasattr(selected_agent, "process_image"):
                agent_response = selected_agent.process_image(
                    image_path, md_prompt, self.user_data
                )
                return f"[Agente de {agent_selection.capitalize()}] {agent_response}"
            else:
                return f"[Agente Supervisor] El agente de {agent_selection} no puede procesar imágenes."

        print(
            f"DEBUG [process_image]: No se derivó. Selección fue '{agent_selection}'. Usando fallback para imagen."
        )
        # Si no se identifica ningún agente específico o se devuelve 'ninguno'
        # Analizar la imagen para generar una respuesta personalizada pero indicando limitaciones
        description_prompt = """
        Describe muy brevemente lo que ves en esta imagen (máximo 20 palabras) y 
        luego explica amablemente que solo puedes ayudar con temas de nutrición, ejercicio o salud.
        La respuesta completa debe ser concisa y natural.
        """

        fallback_messages = [
            {
                "role": "system",
                "content": "Eres un asistente especializado en salud que responde brevemente.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": description_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            },
        ]

        fallback_response = self.client.chat.completions.create(
            model="gpt-4o-mini", messages=fallback_messages, max_tokens=150
        )

        response_content = fallback_response.choices[0].message.content
        return f"[Agente Supervisor] {response_content}"

    def process_request(self, user_input: str, image_path: Optional[str] = None) -> str:
        """
        Procesa la entrada del usuario, determina qué agente debe manejarla
        y coordina la respuesta.

        Args:
            user_input: Texto de entrada del usuario.
            image_path: Ruta opcional a una imagen que el usuario desea procesar.

        Returns:
            Respuesta generada por el sistema de agentes.
        """
        # Si se proporciona una imagen, procesarla
        if image_path:
            return self.process_image(image_path, user_input)

        # Verificar si la entrada contiene actualización de datos de usuario
        if user_input.startswith("/datos"):
            try:
                # Parsear los datos proporcionados
                # Ejemplo: /datos peso=70 altura=175 objetivos=perder_peso,aumentar_musculo
                data_input = user_input.replace("/datos", "").strip()
                data_pairs = data_input.split()

                update_data = {}
                for pair in data_pairs:
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        # Procesar listas separadas por comas
                        if "," in value:
                            update_data[key] = value.split(",")
                        # Procesar valores numéricos
                        elif value.replace(".", "", 1).isdigit():
                            if "." in value:
                                update_data[key] = float(value)
                            else:
                                update_data[key] = int(value)
                        else:
                            update_data[key] = value

                self.update_user_data(update_data)
                return f"[Agente Supervisor] He actualizado tus datos: {', '.join(f'{k}={v}' for k, v in update_data.items())}"
            except Exception as e:
                return f"[Agente Supervisor] Error al actualizar datos: {str(e)}. Usa el formato: /datos clave1=valor1 clave2=valor2"

        # Verificar si el usuario pregunta sobre sus datos médicos personales
        prompt_datos_personales = f"""
        Analiza si la siguiente consulta del usuario se refiere a SUS PROPIOS datos médicos personales,
        historial médico, medicamentos, condiciones de salud o resultados médicos. 
        
        Consulta: "{user_input}"
        
        Responde SOLO con "si" o "no".
        """

        response_datos_personales = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un analizador preciso que determina si una consulta se refiere a datos médicos personales del usuario.",
                },
                {"role": "user", "content": prompt_datos_personales},
            ],
        )

        # Extraer la respuesta
        es_consulta_personal = (
            response_datos_personales.choices[0].message.content.strip().lower()
        )

        # Si es una consulta sobre datos médicos personales, usar directamente el agente médico
        if es_consulta_personal == "si" and "medico" in self.agents:
            selected_agent = self.agents["medico"]
            md_enhanced_input = f"{user_input}\n\n{self.markdown_instruction}"

            if hasattr(selected_agent, "process_with_user_data"):
                agent_response = selected_agent.process_with_user_data(
                    md_enhanced_input, self.user_data
                )
            else:
                agent_response = selected_agent.process(md_enhanced_input)

            return f"[Agente de Médico] {agent_response}"

        # Determinar el propósito de la solicitud usando GPT-4o-mini
        prompt = f"""
        Analiza la siguiente solicitud del usuario y determina qué agente especializado 
        debe manejarla. Los agentes disponibles son: {list(self.agents.keys())}
        
        Reglas claras para determinar el agente:
        1. Si la consulta está relacionada con ALIMENTACIÓN, DIETAS, COMIDAS, NUTRICIÓN, ALIMENTOS, RECETAS o PLANES ALIMENTICIOS, asignar al agente 'nutricion'
        2. Si la consulta está relacionada con EJERCICIO, ENTRENAMIENTO, ACTIVIDAD FÍSICA o RUTINAS DEPORTIVAS, asignar al agente 'ejercicio'
        3. Si la consulta está relacionada con MEDICAMENTOS, SÍNTOMAS, ENFERMEDADES o CONSULTAS MÉDICAS, asignar al agente 'medico'
        4. Si no corresponde claramente a ninguna categoría, responder con 'ninguno'
        
        Datos del usuario:
        {self.user_data}
        
        Solicitud del usuario: {user_input}
        
        Responde ÚNICAMENTE con el nombre del agente que debe manejar esta consulta: 'nutricion', 'ejercicio', 'medico' o 'ninguno'.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un coordinador preciso que asigna consultas al agente especializado correcto, siguiendo estrictamente las reglas definidas.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        # Extraer el nombre del agente de la respuesta
        agent_selection = response.choices[0].message.content.strip().lower()

        print(
            f"DEBUG [process_request]: Clasificación del LLM para la solicitud de texto: {agent_selection}"
        )

        print(
            f"DEBUG [process_request]: Estado de self.agents ANTES del chequeo: {list(self.agents.keys())}"
        )

        # Verificar si se seleccionó un agente válido y procesarlo directamente
        if agent_selection in self.agents:
            selected_agent = self.agents[agent_selection]

            # Preparar la consulta con instrucción de formato Markdown
            md_enhanced_input = f"{user_input}\n\n{self.markdown_instruction}"

            # Pasar los datos del usuario al agente especializado
            if hasattr(selected_agent, "process_with_user_data"):
                agent_response = selected_agent.process_with_user_data(
                    md_enhanced_input, self.user_data
                )
            else:
                agent_response = selected_agent.process(md_enhanced_input)
            # Retornar la respuesta del agente especializado directamente
            return f"[Agente de {agent_selection.capitalize()}] {agent_response}"

        else:
            print(
                f"DEBUG [process_request]: No se derivó. Selección fue '{agent_selection}'. Razón: '{agent_selection}' NO está en {list(self.agents.keys())}. Usando fallback."
            )
            # Si no se identifica ningún agente específico, generar respuesta personalizada pero indicando limitaciones
            fallback_messages = [
                {
                    "role": "system",
                    "content": """Eres un asistente especializado en nutrición, ejercicio y salud.
                    Responde concisamente (máximo 40 palabras) reconociendo brevemente lo que preguntó el usuario,
                    pero indicando amablemente que solo puedes ayudar con temas de salud, nutrición o ejercicio.""",
                },
                {"role": "user", "content": user_input},
            ]

            fallback_response = self.client.chat.completions.create(
                model="gpt-4o-mini", messages=fallback_messages, max_tokens=100
            )

            response_content = fallback_response.choices[0].message.content
            return f"[Agente Supervisor] {response_content}"
