from openai import OpenAI
import os
import base64
import json
from typing import Dict, Any, Optional, List
from datetime import datetime


class MedicalAgent:
    """
    Agente especializado en proporcionar información y orientación sobre temas médicos y de salud.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_data_dir: str = "data_usuario",
        medical_info_file: str = "medical_info.json",
    ):
        """
        Inicializa el agente médico con la API key de OpenAI.

        Args:
            api_key: Clave API de OpenAI. Si no se proporciona, intentará obtenerla de las variables de entorno.
            user_data_dir: Directorio donde se almacenarán los datos de los usuarios.
            medical_info_file: Nombre del archivo principal de información médica.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Se requiere una clave API de OpenAI. Proporciónela como argumento o establezca la variable de entorno OPENAI_API_KEY."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.user_data_dir = user_data_dir
        self.medical_info_file = medical_info_file
        self.medical_info_path = os.path.join(
            self.user_data_dir, self.medical_info_file
        )

        # Crear el directorio de datos de usuario si no existe
        os.makedirs(self.user_data_dir, exist_ok=True)

    def _save_user_medical_data(self, user_data: Dict[str, Any]) -> str:
        """
        Guarda los datos médicos del usuario en el archivo medical_info.json.

        Args:
            user_data: Diccionario con los datos personales y médicos del usuario.

        Returns:
            Ruta al archivo donde se guardaron los datos.
        """
        # Si ya existe el archivo, actualizarlo en lugar de sobrescribirlo
        if os.path.exists(self.medical_info_path):
            try:
                with open(self.medical_info_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)

                # Preservar los datos personales básicos del usuario (no sobrescribir)
                datos_personales = [
                    "id",
                    "nombre",
                    "edad",
                    "peso",
                    "altura",
                    "genero",
                    "fecha_nacimiento",
                    "grupo_sanguineo",
                    "email",
                    "telefono",
                ]

                # Actualizar datos, excepto los datos personales que ya existen
                for key in user_data:
                    if key not in datos_personales or key not in existing_data:
                        existing_data[key] = user_data[key]

                # Actualizar listas (agregar nuevos elementos)
                for key in [
                    "condiciones_medicas",
                    "alergias",
                    "medicamentos",
                    "cirugias",
                    "antecedentes_familiares",
                    "vacunas",
                ]:
                    if key in user_data and user_data[key]:
                        if key not in existing_data:
                            existing_data[key] = []
                        # Añadir solo elementos que no existan ya
                        for item in user_data[key]:
                            if isinstance(item, dict):
                                # Para elementos complejos como medicamentos o cirugías
                                if item not in existing_data[key]:
                                    existing_data[key].append(item)
                            elif item not in existing_data[key]:
                                existing_data[key].append(item)

                # Añadir a la lista de consultas si hay una nueva consulta
                if "consulta_actual" in user_data and user_data["consulta_actual"]:
                    if "historial_consultas" not in existing_data:
                        existing_data["historial_consultas"] = []

                    consulta = user_data["consulta_actual"]
                    consulta["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    existing_data["historial_consultas"].append(consulta)

                # Actualizar estudios médicos si hay nuevos
                if "estudios_medicos" in user_data and user_data["estudios_medicos"]:
                    if "estudios_medicos" not in existing_data:
                        existing_data["estudios_medicos"] = []

                    for estudio in user_data["estudios_medicos"]:
                        if estudio not in existing_data["estudios_medicos"]:
                            existing_data["estudios_medicos"].append(estudio)

                # Mantener la sección de hábitos si ya existe
                if "habitos" in user_data and user_data["habitos"]:
                    if "habitos" not in existing_data:
                        existing_data["habitos"] = user_data["habitos"]

                # Actualizar la fecha de última actualización
                existing_data["ultima_actualizacion"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                user_data_to_save = existing_data
            except Exception as e:
                print(f"Error al cargar el historial médico existente: {str(e)}")
                # Si hay error al cargar, crear un nuevo archivo
                user_data_to_save = user_data
                user_data_to_save["ultima_actualizacion"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        else:
            # Si no existe, crear un nuevo archivo
            user_data_to_save = user_data
            user_data_to_save["ultima_actualizacion"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        with open(self.medical_info_path, "w", encoding="utf-8") as f:
            json.dump(user_data_to_save, f, ensure_ascii=False, indent=2)

        return self.medical_info_path

    def get_user_medical_data(
        self, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Recupera los datos médicos del archivo medical_info.json.

        Args:
            user_id: ID del usuario (ignorado, se usa solo para compatibilidad).

        Returns:
            Diccionario con los datos médicos o None si no se encuentra.
        """
        if not os.path.exists(self.medical_info_path):
            return None

        try:
            with open(self.medical_info_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar los datos médicos: {str(e)}")
            return None

    def add_medical_record(
        self, user_id: Optional[str] = None, medical_record: Dict[str, Any] = None
    ) -> bool:
        """
        Añade un registro médico al archivo medical_info.json.

        Args:
            user_id: ID del usuario (ignorado, se usa solo para compatibilidad).
            medical_record: Registro médico a añadir (consulta, estudio, medicamento, etc.)

        Returns:
            True si se añadió correctamente, False en caso contrario.
        """
        user_data = self.get_user_medical_data()
        if not user_data:
            return False

        if not medical_record:
            return False

        # Hacer una copia del historial médico para no modificar los datos personales
        historial_actualizado = user_data.copy()

        # Determinar el tipo de registro y añadirlo al historial correspondiente
        record_type = medical_record.get("tipo", "consulta")
        medical_record["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if record_type == "consulta":
            if "historial_consultas" not in historial_actualizado:
                historial_actualizado["historial_consultas"] = []
            historial_actualizado["historial_consultas"].append(medical_record)
        elif record_type == "medicamento":
            if "medicamentos" not in historial_actualizado:
                historial_actualizado["medicamentos"] = []
            historial_actualizado["medicamentos"].append(medical_record)
        elif record_type == "estudio" or record_type == "examen":
            if "estudios_medicos" not in historial_actualizado:
                historial_actualizado["estudios_medicos"] = []
            historial_actualizado["estudios_medicos"].append(medical_record)
        elif record_type == "cirugia":
            if "cirugias" not in historial_actualizado:
                historial_actualizado["cirugias"] = []
            historial_actualizado["cirugias"].append(medical_record)
        elif record_type == "alergia":
            if "alergias" not in historial_actualizado:
                historial_actualizado["alergias"] = []
            if (
                isinstance(medical_record.get("detalle"), str)
                and medical_record["detalle"] not in historial_actualizado["alergias"]
            ):
                historial_actualizado["alergias"].append(medical_record["detalle"])
        elif record_type == "condicion_medica":
            if "condiciones_medicas" not in historial_actualizado:
                historial_actualizado["condiciones_medicas"] = []
            if (
                isinstance(medical_record.get("detalle"), str)
                and medical_record["detalle"]
                not in historial_actualizado["condiciones_medicas"]
            ):
                historial_actualizado["condiciones_medicas"].append(
                    medical_record["detalle"]
                )
        elif record_type == "vacuna":
            if "vacunas" not in historial_actualizado:
                historial_actualizado["vacunas"] = []
            historial_actualizado["vacunas"].append(medical_record)

        # Actualizar la fecha de última actualización
        historial_actualizado["ultima_actualizacion"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Guardar los datos actualizados directamente
        try:
            with open(self.medical_info_path, "w", encoding="utf-8") as f:
                json.dump(historial_actualizado, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error al guardar el registro médico: {str(e)}")
            return False

    def process(self, user_input: str) -> str:
        """
        Procesa la consulta del usuario relacionada con temas médicos y de salud.

        Args:
            user_input: Texto de entrada del usuario.

        Returns:
            Respuesta generada por el agente médico.
        """
        system_prompt = """
        Eres un asistente médico especializado en proporcionar información sobre temas de salud. 
        
        Importante: No eres un médico licenciado y no puedes diagnosticar enfermedades ni recetar 
        medicamentos. Siempre debes aconsejar a los usuarios que consulten a profesionales de la 
        salud para diagnósticos y tratamientos.
        
        Tus conocimientos incluyen:
        - Información general sobre condiciones médicas comunes
        - Explicaciones de procedimientos médicos habituales
        - Consejos generales de salud y prevención
        - Interpretación de términos médicos en lenguaje comprensible
        - Orientación sobre cuándo buscar atención médica
        
        Proporciona información clara, precisa y basada en evidencia científica.
        Evita dar consejos médicos específicos y en caso de emergencia siempre recomienda 
        buscar atención médica inmediata.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
        )

        return response.choices[0].message.content or ""

    def process_with_user_data(
        self,
        user_input: str,
        user_data: Optional[Dict[str, Any]] = None,
        consult_history: bool = True,
    ) -> str:
        """
        Procesa la consulta del usuario utilizando los datos del archivo medical_info.json.

        Args:
            user_input: Texto de entrada del usuario.
            user_data: Diccionario con datos adicionales del usuario (opcional).
            consult_history: Si es True, consultará el historial médico completo.

        Returns:
            Respuesta generada por el agente médico, contextualizada con los datos del usuario.
        """
        # Obtener los datos médicos existentes
        medical_history = self.get_user_medical_data()

        # Si no hay datos médicos, retornar un mensaje
        if not medical_history:
            if user_data:
                # Si no hay datos médicos pero se proporcionan datos de usuario, usarlos
                medical_history = user_data
            else:
                return "No se encontraron datos médicos para consultar. Por favor, proporciona tu información médica primero."

        # Registrar la consulta actual sin modificar los datos personales del usuario
        consulta_actual = {
            "tipo": "consulta",
            "descripcion": user_input,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Crea una copia del historial médico y solo añade la consulta
        historial_actualizado = medical_history.copy()
        if "historial_consultas" not in historial_actualizado:
            historial_actualizado["historial_consultas"] = []
        historial_actualizado["historial_consultas"].append(consulta_actual)
        historial_actualizado["ultima_actualizacion"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Guardar solo la nueva consulta sin modificar datos personales
        with open(self.medical_info_path, "w", encoding="utf-8") as f:
            json.dump(historial_actualizado, f, ensure_ascii=False, indent=2)

        # Preparar el historial de consultas para el contexto
        consultas_previas = ""
        if (
            consult_history
            and "historial_consultas" in medical_history
            and len(medical_history["historial_consultas"]) > 1
        ):
            consultas_previas = "Consultas previas:\n"
            # Excluir la consulta actual
            for i, consulta in enumerate(
                medical_history["historial_consultas"][-5:], 1
            ):  # Mostrar solo las últimas 5
                consultas_previas += f"{i}. Fecha: {consulta.get('fecha', 'No especificada')} - {consulta.get('descripcion', 'No especificada')}\n"

        # Preparar información de medicamentos
        medicamentos_info = ""
        if "medicamentos" in medical_history and medical_history["medicamentos"]:
            medicamentos_info = "Medicamentos actuales:\n"
            for med in medical_history["medicamentos"]:
                if isinstance(med, dict):
                    nombre = med.get("nombre", "No especificado")
                    dosis = med.get("dosis", "No especificada")
                    frecuencia = med.get("frecuencia", "No especificada")
                    medicamentos_info += (
                        f"- {nombre} | Dosis: {dosis} | Frecuencia: {frecuencia}\n"
                    )
                else:
                    medicamentos_info += f"- {med}\n"

        # Preparar información de estudios médicos
        estudios_info = ""
        if (
            "estudios_medicos" in medical_history
            and medical_history["estudios_medicos"]
        ):
            estudios_info = "Estudios médicos recientes:\n"
            for estudio in medical_history["estudios_medicos"][
                -3:
            ]:  # Mostrar solo los últimos 3
                if isinstance(estudio, dict):
                    tipo = estudio.get("nombre", "No especificado")
                    fecha = estudio.get("fecha", "No especificada")
                    resultado = estudio.get("resultado", "No especificado")
                    estudios_info += (
                        f"- {tipo} | Fecha: {fecha} | Resultado: {resultado}\n"
                    )
                else:
                    estudios_info += f"- {estudio}\n"

        # Construir el prompt con toda la información médica
        system_prompt = f"""
        Eres un asistente médico especializado en proporcionar información sobre temas de salud. 
        
        Importante: No eres un médico licenciado y no puedes diagnosticar enfermedades ni recetar 
        medicamentos. Siempre debes aconsejar a los usuarios que consulten a profesionales de la 
        salud para diagnósticos y tratamientos.
        
        Datos del usuario:
        - Nombre: {medical_history.get('nombre', 'No especificado')}
        - Edad: {medical_history.get('edad', 'No especificada')}
        - Peso: {medical_history.get('peso', 'No especificado')} kg
        - Altura: {medical_history.get('altura', 'No especificada')} cm
        - Género: {medical_history.get('genero', 'No especificado')}
        - Grupo sanguíneo: {medical_history.get('grupo_sanguineo', 'No especificado')}
        - Condiciones médicas: {', '.join(medical_history.get('condiciones_medicas', [])) or 'Ninguna reportada'}
        - Alergias: {', '.join(medical_history.get('alergias', [])) or 'Ninguna reportada'}
        
        {medicamentos_info}
        
        {estudios_info}
        
        {consultas_previas}
        
        Tus conocimientos incluyen:
        - Información general sobre condiciones médicas comunes
        - Explicaciones de procedimientos médicos habituales
        - Consejos generales de salud y prevención
        - Interpretación de términos médicos en lenguaje comprensible
        - Orientación sobre cuándo buscar atención médica
        
        Proporciona información clara, precisa y basada en evidencia científica.
        Evita dar consejos médicos específicos y en caso de emergencia siempre recomienda 
        buscar atención médica inmediata.
        
        Ten en cuenta las condiciones médicas y alergias del usuario al proporcionar información,
        pero recuerda que no estás diagnosticando ni recetando tratamientos. Siempre recomienda 
        la consulta con profesionales médicos para casos específicos.
        
        Si la consulta actual está relacionada con consultas previas o con las condiciones médicas
        del usuario, haz referencia a esta información en tu respuesta.
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

    def process_image(
        self,
        image_path: str,
        user_prompt: Optional[str] = None,
        user_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Procesa una imagen relacionada con temas médicos utilizando los datos del archivo medical_info.json.

        Args:
            image_path: Ruta al archivo de imagen.
            user_prompt: Texto adicional proporcionado por el usuario sobre la imagen.
            user_data: Diccionario con datos adicionales del usuario (opcional).

        Returns:
            Respuesta generada por el agente médico sobre la imagen.
        """
        # Obtener los datos médicos existentes
        medical_history = self.get_user_medical_data()

        # Si se proporcionan datos de usuario adicionales, actualizarlos
        if user_data:
            if medical_history:
                # Combinar con los datos existentes
                medical_history.update(
                    {
                        k: v
                        for k, v in user_data.items()
                        if k
                        in [
                            "nombre",
                            "edad",
                            "peso",
                            "altura",
                            "genero",
                            "fecha_nacimiento",
                            "grupo_sanguineo",
                        ]
                    }
                )
            else:
                medical_history = user_data

        # Si no hay datos médicos, crear un registro básico
        if not medical_history:
            medical_history = {}

        try:
            base64_image = self.encode_image_to_base64(image_path)
        except Exception as e:
            return f"Error al procesar la imagen: {str(e)}"

        # Registrar esta consulta en el historial médico
        consulta_imagen = {
            "tipo": "consulta_imagen",
            "descripcion": user_prompt or "Consulta de imagen médica",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "imagen_referencia": os.path.basename(image_path),
        }

        if "historial_consultas" not in medical_history:
            medical_history["historial_consultas"] = []
        medical_history["historial_consultas"].append(consulta_imagen)

        # Guardar los datos actualizados
        self._save_user_medical_data(medical_history)

        # Preparar el prompt para analizar la imagen
        system_prompt = f"""
        Eres un asistente médico especializado que analiza imágenes relacionadas con temas de salud.
        
        IMPORTANTE: NO PUEDES DIAGNOSTICAR ENFERMEDADES NI RECETAR TRATAMIENTOS.
        Tu función es informativa y educativa. Siempre debes aclarar que cualquier interpretación
        debe ser confirmada por un profesional de la salud calificado.
        
        Datos del usuario:
        - Nombre: {medical_history.get('nombre', 'No especificado')}
        - Edad: {medical_history.get('edad', 'No especificada')}
        - Peso: {medical_history.get('peso', 'No especificado')} kg
        - Altura: {medical_history.get('altura', 'No especificada')} cm
        - Género: {medical_history.get('genero', 'No especificado')}
        - Grupo sanguíneo: {medical_history.get('grupo_sanguineo', 'No especificado')}
        - Condiciones médicas: {', '.join(medical_history.get('condiciones_medicas', [])) or 'Ninguna reportada'}
        - Alergias: {', '.join(medical_history.get('alergias', [])) or 'Ninguna reportada'}
        
        Al analizar esta imagen:
        1. Describe lo que observas de manera objetiva
        2. Proporciona información educativa sobre lo que muestra la imagen
        3. Explica posibles implicaciones generales para la salud (SIN DIAGNOSTICAR)
        4. Si es pertinente, sugerir cuándo buscar atención médica
        5. SIEMPRE enfatiza la importancia de consultar a un profesional de la salud
        
        Si la imagen muestra:
        - Medicamentos: proporciona información general sobre su uso común, sin recetar
        - Lesiones o condiciones de la piel: descripción objetiva, sin diagnóstico
        - Resultados de exámenes médicos: explicación general de los parámetros, sin interpretación clínica
        - Equipamiento médico: información sobre su función y uso común
        
        Usa un lenguaje claro, comprensible y basado en evidencia científica.
        Mantén un tono empático y profesional en todo momento.
        """

        # Definir el prompt del usuario
        user_text_prompt = "Analiza esta imagen relacionada con temas médicos o de salud y proporciona información educativa."
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

        # Añadir un descargo de responsabilidad estándar a la respuesta
        disclaimer = "\n\n[Nota importante: Esta información es educativa y no constituye un diagnóstico médico. Consulte siempre a un profesional de la salud calificado para una evaluación adecuada.]"

        content = response.choices[0].message.content or ""
        return content + disclaimer
