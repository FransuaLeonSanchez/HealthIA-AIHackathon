import os
import json
import base64
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import pytz
import tempfile
from app.models.chat_models import InputType
from app.services.s3_service import S3Service

# Cargar variables de entorno
load_dotenv()

# Inicializar cliente de OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Obtener el modelo de OpenAI desde las variables de entorno
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Directorios para almacenar las conversaciones
OPENAI_CHATS_DIR = Path("app/chats-openai")
FRONTEND_CHATS_DIR = Path("app/chats-frontend")
OPENAI_CHATS_DIR.mkdir(exist_ok=True)
FRONTEND_CHATS_DIR.mkdir(exist_ok=True)

# Ruta al archivo de system prompt
SYSTEM_PROMPT_PATH = Path("app/static/system_prompt.txt")


class OpenAIService:
    @staticmethod
    def get_system_prompt():
        """Obtiene el prompt del sistema desde el archivo."""
        try:
            with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            # Prompt predeterminado si el archivo no existe
            return "Eres un asistente médico de HealthIA, diseñado para proporcionar información médica precisa y útil."

    @staticmethod
    def get_openai_conversation_path(conversation_id: int) -> Path:
        """Obtiene la ruta del archivo para una conversación específica en formato OpenAI."""
        return OPENAI_CHATS_DIR / f"{conversation_id}.json"

    @staticmethod
    def get_frontend_conversation_path(conversation_id: int) -> Path:
        """Obtiene la ruta del archivo para una conversación específica en formato frontend."""
        return FRONTEND_CHATS_DIR / f"{conversation_id}.json"

    @staticmethod
    def conversation_exists(conversation_id: int) -> bool:
        """Verifica si una conversación existe."""
        if conversation_id is None:
            return False
        return (
            OpenAIService.get_openai_conversation_path(conversation_id).exists()
            or OpenAIService.get_frontend_conversation_path(conversation_id).exists()
        )

    @staticmethod
    def create_new_conversation(conversation_id: int) -> int:
        """
        Crea una nueva conversación con el ID proporcionado.
        """
        # Obtener la fecha y hora actual en Perú (UTC-5)
        peru_timezone = pytz.timezone("America/Lima")
        current_time = datetime.now(peru_timezone)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Datos para OpenAI (solo mensajes)
        openai_conversation_data = {"messages": []}

        # Datos para el frontend (estructura completa)
        frontend_conversation_data = {
            "id": conversation_id,
            "title": "",
            "created_at": formatted_time,
            "messages": [],
        }

        # Guardar ambos archivos
        with open(
            OpenAIService.get_openai_conversation_path(conversation_id), "w"
        ) as f:
            json.dump(openai_conversation_data, f)

        with open(
            OpenAIService.get_frontend_conversation_path(conversation_id), "w"
        ) as f:
            json.dump(frontend_conversation_data, f)

        return conversation_id

    @staticmethod
    def get_conversation(conversation_id: int) -> tuple:
        """Obtiene los datos de una conversación existente."""
        openai_data = {"messages": []}
        frontend_data = {
            "id": conversation_id,
            "title": "Chat sin título",
            "created_at": "",
            "messages": [],
        }

        # Intentar cargar datos de OpenAI
        openai_path = OpenAIService.get_openai_conversation_path(conversation_id)
        if openai_path.exists():
            with open(openai_path, "r") as f:
                openai_data = json.load(f)

        # Intentar cargar datos del frontend
        frontend_path = OpenAIService.get_frontend_conversation_path(conversation_id)
        if frontend_path.exists():
            with open(frontend_path, "r") as f:
                frontend_data = json.load(f)

        return openai_data, frontend_data

    @staticmethod
    def save_conversation(
        conversation_id: int, openai_data: dict, frontend_data: dict
    ) -> None:
        """Guarda los datos de una conversación."""
        # Guardar datos de OpenAI
        with open(
            OpenAIService.get_openai_conversation_path(conversation_id), "w"
        ) as f:
            json.dump(openai_data, f)

        # Guardar datos del frontend
        with open(
            OpenAIService.get_frontend_conversation_path(conversation_id), "w"
        ) as f:
            json.dump(frontend_data, f)

    @staticmethod
    def delete_conversation(conversation_id: int) -> bool:
        """
        Elimina una conversación existente.
        Retorna True si se eliminó correctamente, False si no existía.
        """
        openai_path = OpenAIService.get_openai_conversation_path(conversation_id)
        frontend_path = OpenAIService.get_frontend_conversation_path(conversation_id)

        deleted = False

        if openai_path.exists():
            openai_path.unlink()  # Elimina el archivo
            deleted = True

        if frontend_path.exists():
            frontend_path.unlink()  # Elimina el archivo
            deleted = True

        return deleted

    @staticmethod
    def get_all_conversations() -> list:
        """
        Obtiene todas las conversaciones disponibles.
        Retorna una lista de diccionarios, cada uno con el ID, título, fecha de creación y mensajes.
        """
        all_chats = []

        # Buscar todos los archivos JSON en el directorio de frontend
        for file_path in FRONTEND_CHATS_DIR.glob("*.json"):
            try:
                # Extraer el ID de la conversación del nombre del archivo
                conversation_id = int(file_path.stem)

                # Obtener los datos de la conversación
                with open(file_path, "r") as f:
                    conversation_data = json.load(f)

                # Crear un resumen de la conversación
                chat_summary = {
                    "id": conversation_id,
                    "title": conversation_data.get("title", "Chat sin título"),
                    "created_at": conversation_data.get(
                        "created_at", "Fecha desconocida"
                    ),
                    "messages": conversation_data["messages"],
                }

                all_chats.append(chat_summary)
            except (ValueError, json.JSONDecodeError, KeyError) as e:
                # Ignorar archivos con formato incorrecto
                continue

        return all_chats

    @staticmethod
    async def chat_with_openai(
        message: str,
        conversation_id: int,
        input_type: InputType = InputType.TEXT,
        media_content=None,
        original_filename=None,
    ) -> dict:
        """
        Procesa un mensaje con OpenAI y devuelve la respuesta.

        Args:
            message: Mensaje del usuario (texto, imagen en base64 o audio en base64)
            conversation_id: ID de la conversación
            input_type: Tipo de entrada (texto, imagen o audio)
            media_content: Contenido multimedia opcional (para formularios multipart)
            original_filename: Nombre original del archivo (opcional)

        Returns:
            Diccionario con la respuesta, ID de la conversación, título y fecha de creación
        """
        try:
            # Verificar si la conversación existe
            is_new_conversation = not OpenAIService.conversation_exists(conversation_id)

            # Obtener o crear la conversación
            if is_new_conversation:
                # Crear una nueva conversación con la fecha actual en Perú (UTC-5)
                peru_timezone = pytz.timezone("America/Lima")
                current_time = datetime.now(peru_timezone)
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

                openai_data = {"messages": []}

                frontend_data = {
                    "id": conversation_id,
                    "title": "Chat sin título",
                    "created_at": formatted_time,
                    "messages": [],
                }
            else:
                # Obtener la conversación existente
                openai_data, frontend_data = OpenAIService.get_conversation(
                    conversation_id
                )

            # Procesar según el tipo de entrada
            if input_type == InputType.TEXT:
                # Preparar los mensajes para OpenAI en formato nativo
                openai_messages = []

                # Añadir un mensaje de sistema al principio para establecer el contexto
                system_prompt = OpenAIService.get_system_prompt()
                openai_messages.append({"role": "system", "content": system_prompt})

                # Convertir el historial de mensajes al formato nativo de OpenAI
                for m in openai_data["messages"]:
                    # Omitir mensajes de sistema internos que no son relevantes para OpenAI
                    if (
                        m["role"] == "system"
                        and "[El usuario ha compartido una imagen:" in m["content"]
                    ):
                        continue

                    # Si es un mensaje de usuario con URL de imagen, convertirlo a formato multimodal
                    if (
                        m["role"] == "user"
                        and isinstance(m["content"], str)
                        and m["content"].startswith("http")
                    ):
                        # Verificar si es una URL de imagen
                        is_image_url = (
                            any(
                                m["content"].lower().endswith(ext)
                                for ext in [".jpg", ".jpeg", ".png", ".gif"]
                            )
                            or "s3.amazonaws.com" in m["content"]
                        )

                        if is_image_url:
                            # Buscar el siguiente mensaje que debería ser la instrucción del usuario
                            idx = openai_data["messages"].index(m)
                            if (
                                idx + 1 < len(openai_data["messages"])
                                and openai_data["messages"][idx + 1]["role"] == "user"
                            ):
                                instruction = openai_data["messages"][idx + 1][
                                    "content"
                                ]

                                # Crear un mensaje multimodal con la imagen y la instrucción
                                openai_messages.append(
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": instruction},
                                            {
                                                "type": "image_url",
                                                "image_url": {"url": m["content"]},
                                            },
                                        ],
                                    }
                                )
                            continue

                    # Si es un mensaje de usuario con instrucción después de una imagen, ya lo procesamos
                    if m["role"] == "user":
                        idx = openai_data["messages"].index(m)
                        if (
                            idx > 0
                            and openai_data["messages"][idx - 1]["role"] == "user"
                        ):
                            prev_msg = openai_data["messages"][idx - 1]["content"]
                            if (
                                isinstance(prev_msg, str)
                                and prev_msg.startswith("http")
                                and (
                                    any(
                                        prev_msg.lower().endswith(ext)
                                        for ext in [".jpg", ".jpeg", ".png", ".gif"]
                                    )
                                    or "s3.amazonaws.com" in prev_msg
                                )
                            ):
                                continue

                    # Para otros mensajes, añadirlos normalmente
                    if m["role"] in ["assistant", "user"]:
                        openai_messages.append(
                            {"role": m["role"], "content": m["content"]}
                        )

                # Añadir el mensaje actual del usuario
                openai_messages.append({"role": "user", "content": message})

                # Procesar el mensaje con OpenAI
                response = client.chat.completions.create(
                    model=OPENAI_MODEL, messages=openai_messages, temperature=0.4
                )

                # Obtener la respuesta
                assistant_message = response.choices[0].message.content

                # Si es el primer mensaje, generar un título corto
                if is_new_conversation or len(openai_data["messages"]) == 0:
                    # Solicitar a OpenAI que genere un título corto
                    title_response = client.chat.completions.create(
                        model=OPENAI_MODEL,
                        messages=[
                            {
                                "role": "system",
                                "content": "Genera un título muy corto (máximo 5 palabras) para esta conversación basado en el primer mensaje del usuario. No uses comillas ni puntuación.",
                            },
                            {"role": "user", "content": message},
                        ],
                        temperature=0.4,
                    )
                    # Guardar el título generado
                    frontend_data["title"] = title_response.choices[
                        0
                    ].message.content.strip()

                # Agregar el mensaje del usuario al historial
                openai_data["messages"].append({"role": "user", "content": message})
                frontend_data["messages"].append({"role": "user", "content": message})

            elif input_type == InputType.IMAGE:
                # Procesar imagen
                try:
                    # Determinar si estamos usando media_content o mensaje en base64
                    image_data = None
                    if media_content:
                        # Usar el archivo de imagen directamente
                        image_data = media_content
                    else:
                        # Intentar decodificar la imagen en base64
                        try:
                            image_data = base64.b64decode(message)
                        except base64.binascii.Error:
                            return {
                                "error": "El formato de la imagen no es válido. Debe ser una cadena base64 válida o un archivo de imagen.",
                                "id": conversation_id,
                                "title": frontend_data.get("title", "Chat sin título"),
                                "created_at": frontend_data.get(
                                    "created_at", "Fecha desconocida"
                                ),
                            }

                    # Determinar la extensión del archivo
                    file_extension = "jpg"  # Valor predeterminado
                    if original_filename:
                        # Extraer la extensión del nombre original
                        _, ext = os.path.splitext(original_filename)
                        if ext and ext.startswith("."):
                            file_extension = ext[
                                1:
                            ].lower()  # Eliminar el punto inicial

                    # Guardar la imagen en S3
                    s3_result = S3Service.upload_file_to_s3(
                        file_content=image_data,
                        file_extension=file_extension,
                        conversation_id=conversation_id,
                        original_filename=original_filename,
                    )

                    if not s3_result["success"]:
                        return {
                            "error": f"Error al guardar la imagen en S3: {s3_result.get('error')}",
                            "id": conversation_id,
                            "title": frontend_data.get("title", "Chat sin título"),
                            "created_at": frontend_data.get(
                                "created_at", "Fecha desconocida"
                            ),
                        }

                    # Obtener la URL de la imagen
                    image_url = s3_result["url"]

                    # Obtener la instrucción del usuario (si existe)
                    user_instruction = (
                        message
                        if isinstance(message, str)
                        and not message.startswith("data:image")
                        else "¿Qué puedes ver en esta imagen? Por favor, descríbela detalladamente."
                    )

                    # Crear un archivo temporal para la imagen si es necesario
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=f".{file_extension}"
                    ) as temp_image:
                        temp_image.write(image_data)
                        temp_image_path = temp_image.name

                    # Leer la imagen y convertirla a base64 para enviarla a la API
                    with open(temp_image_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode(
                            "utf-8"
                        )

                    # Preparar los mensajes para OpenAI en formato nativo
                    openai_messages = []

                    # Añadir un mensaje de sistema al principio para establecer el contexto
                    system_prompt = OpenAIService.get_system_prompt()
                    openai_messages.append({"role": "system", "content": system_prompt})

                    # Convertir el historial de mensajes al formato nativo de OpenAI
                    for m in openai_data["messages"]:
                        # Omitir mensajes de sistema internos que no son relevantes para OpenAI
                        if (
                            m["role"] == "system"
                            and "[El usuario ha compartido una imagen:" in m["content"]
                        ):
                            continue

                        # Si es un mensaje de usuario con URL de imagen, convertirlo a formato multimodal
                        if (
                            m["role"] == "user"
                            and isinstance(m["content"], str)
                            and m["content"].startswith("http")
                        ):
                            # Verificar si es una URL de imagen
                            is_image_url = (
                                any(
                                    m["content"].lower().endswith(ext)
                                    for ext in [".jpg", ".jpeg", ".png", ".gif"]
                                )
                                or "s3.amazonaws.com" in m["content"]
                            )

                            if is_image_url:
                                # Buscar el siguiente mensaje que debería ser la instrucción del usuario
                                idx = openai_data["messages"].index(m)
                                if (
                                    idx + 1 < len(openai_data["messages"])
                                    and openai_data["messages"][idx + 1]["role"]
                                    == "user"
                                ):
                                    instruction = openai_data["messages"][idx + 1][
                                        "content"
                                    ]

                                    # Crear un mensaje multimodal con la imagen y la instrucción
                                    openai_messages.append(
                                        {
                                            "role": "user",
                                            "content": [
                                                {"type": "text", "text": instruction},
                                                {
                                                    "type": "image_url",
                                                    "image_url": {"url": m["content"]},
                                                },
                                            ],
                                        }
                                    )
                                continue

                        # Si es un mensaje de usuario con instrucción después de una imagen, ya lo procesamos
                        if m["role"] == "user":
                            idx = openai_data["messages"].index(m)
                            if (
                                idx > 0
                                and openai_data["messages"][idx - 1]["role"] == "user"
                            ):
                                prev_msg = openai_data["messages"][idx - 1]["content"]
                                if (
                                    isinstance(prev_msg, str)
                                    and prev_msg.startswith("http")
                                    and (
                                        any(
                                            prev_msg.lower().endswith(ext)
                                            for ext in [".jpg", ".jpeg", ".png", ".gif"]
                                        )
                                        or "s3.amazonaws.com" in prev_msg
                                    )
                                ):
                                    continue

                        # Para otros mensajes, añadirlos normalmente
                        if m["role"] in ["assistant", "user"]:
                            openai_messages.append(
                                {"role": m["role"], "content": m["content"]}
                            )

                    # Añadir el mensaje actual con la imagen
                    openai_messages.append(
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_instruction},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{file_extension};base64,{base64_image}"
                                    },
                                },
                            ],
                        }
                    )

                    # Enviar la imagen a GPT-4o
                    response = client.chat.completions.create(
                        model="gpt-4o",  # Usar GPT-4o para visión
                        messages=openai_messages,
                        temperature=0.4,
                    )

                    # Obtener la respuesta
                    assistant_message = response.choices[0].message.content

                    # Si es el primer mensaje, generar un título corto
                    if is_new_conversation or len(openai_data["messages"]) == 0:
                        # Solicitar a OpenAI que genere un título corto basado en la descripción
                        title_response = client.chat.completions.create(
                            model=OPENAI_MODEL,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "Genera un título muy corto (máximo 5 palabras) para esta conversación basado en la descripción de una imagen. No uses comillas ni puntuación.",
                                },
                                {"role": "user", "content": assistant_message},
                            ],
                            temperature=0.4,
                        )
                        # Guardar el título generado
                        frontend_data["title"] = title_response.choices[
                            0
                        ].message.content.strip()

                    # Eliminar el archivo temporal
                    os.unlink(temp_image_path)

                    # Guardar la URL de la imagen y la instrucción en el historial
                    # Para OpenAI: formato multimodal
                    openai_data["messages"].append(
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_instruction},
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    )

                    # Para Frontend: formato simple
                    frontend_data["messages"].append(
                        {"role": "user_media", "content": image_url}
                    )

                    frontend_data["messages"].append(
                        {"role": "user", "content": user_instruction}
                    )

                except base64.binascii.Error:
                    return {
                        "error": "El formato de la imagen no es válido. Debe ser una cadena base64 válida o un archivo de imagen.",
                        "id": conversation_id,
                        "title": frontend_data.get("title", "Chat sin título"),
                        "created_at": frontend_data.get(
                            "created_at", "Fecha desconocida"
                        ),
                    }
                except Exception as e:
                    return {
                        "error": f"Error al procesar la imagen: {str(e)}",
                        "id": conversation_id,
                        "title": frontend_data.get("title", "Chat sin título"),
                        "created_at": frontend_data.get(
                            "created_at", "Fecha desconocida"
                        ),
                    }
            elif input_type == InputType.AUDIO:
                # Procesar audio
                try:
                    # Determinar si estamos usando media_content o mensaje en base64
                    audio_data = None
                    if media_content:
                        # Usar el archivo de audio directamente
                        audio_data = media_content
                    else:
                        # Intentar decodificar el audio en base64
                        try:
                            audio_data = base64.b64decode(message)
                        except base64.binascii.Error:
                            return {
                                "error": "El formato del audio no es válido. Debe ser una cadena base64 válida o un archivo de audio.",
                                "id": conversation_id,
                                "title": frontend_data.get("title", "Chat sin título"),
                                "created_at": frontend_data.get(
                                    "created_at", "Fecha desconocida"
                                ),
                            }

                    # Determinar la extensión del archivo
                    file_extension = "mp3"  # Valor predeterminado
                    if original_filename:
                        # Extraer la extensión del nombre original
                        _, ext = os.path.splitext(original_filename)
                        if ext and ext.startswith("."):
                            file_extension = ext[
                                1:
                            ].lower()  # Eliminar el punto inicial

                    # Guardar el audio en S3
                    s3_result = S3Service.upload_file_to_s3(
                        file_content=audio_data,
                        file_extension=file_extension,
                        conversation_id=conversation_id,
                        original_filename=original_filename,
                    )

                    if not s3_result["success"]:
                        return {
                            "error": f"Error al guardar el audio en S3: {s3_result.get('error')}",
                            "id": conversation_id,
                            "title": frontend_data.get("title", "Chat sin título"),
                            "created_at": frontend_data.get(
                                "created_at", "Fecha desconocida"
                            ),
                        }

                    # Obtener la URL del audio
                    audio_url = s3_result["url"]

                    # Obtener la instrucción del usuario (si existe)
                    user_instruction = (
                        message
                        if isinstance(message, str)
                        and not message.startswith("data:audio")
                        else ""
                    )

                    # Crear un archivo temporal para el audio
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=f".{file_extension}"
                    ) as temp_audio:
                        temp_audio.write(audio_data)
                        temp_audio_path = temp_audio.name

                    # Transcribir el audio con Whisper
                    with open(temp_audio_path, "rb") as audio_file:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1", file=audio_file
                        )

                    # Obtener la transcripción
                    transcription = transcript.text

                    # Preparar los mensajes para OpenAI en formato nativo
                    openai_messages = []

                    # Añadir un mensaje de sistema al principio para establecer el contexto
                    system_prompt = OpenAIService.get_system_prompt()
                    openai_messages.append({"role": "system", "content": system_prompt})

                    # Convertir el historial de mensajes al formato nativo de OpenAI
                    for m in openai_data["messages"]:
                        # Para mensajes normales, añadirlos directamente
                        if m["role"] in ["assistant", "user"]:
                            openai_messages.append(
                                {"role": m["role"], "content": m["content"]}
                            )

                    # Añadir la transcripción como mensaje del usuario
                    message_content = transcription
                    if user_instruction:
                        message_content = f"{transcription}\n\nInstrucción adicional: {user_instruction}"

                    openai_messages.append({"role": "user", "content": message_content})

                    # Enviar la transcripción a GPT para obtener una respuesta
                    response = client.chat.completions.create(
                        model=OPENAI_MODEL, messages=openai_messages, temperature=0.4
                    )

                    # Obtener la respuesta
                    assistant_message = response.choices[0].message.content

                    # Si es el primer mensaje, generar un título corto
                    if is_new_conversation or len(openai_data["messages"]) == 0:
                        # Solicitar a OpenAI que genere un título corto basado en la transcripción
                        title_response = client.chat.completions.create(
                            model=OPENAI_MODEL,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "Genera un título muy corto (máximo 5 palabras) para esta conversación basado en la transcripción de un audio. No uses comillas ni puntuación.",
                                },
                                {"role": "user", "content": transcription},
                            ],
                            temperature=0.4,
                        )
                        # Guardar el título generado
                        frontend_data["title"] = title_response.choices[
                            0
                        ].message.content.strip()

                    # Eliminar el archivo temporal
                    os.unlink(temp_audio_path)

                    # Guardar la transcripción y la URL del audio en el historial
                    # Para OpenAI
                    openai_data["messages"].append(
                        {
                            "role": "system",
                            "content": f"[Audio transcrito: {audio_url}]",
                        }
                    )

                    openai_data["messages"].append(
                        {"role": "user", "content": message_content}
                    )

                    # Para Frontend
                    frontend_data["messages"].append(
                        {"role": "user", "content": f"URL del audio: {audio_url}"}
                    )

                    if user_instruction:
                        frontend_data["messages"].append(
                            {"role": "user", "content": user_instruction}
                        )

                    frontend_data["messages"].append(
                        {
                            "role": "system",
                            "content": f"Transcripción del audio: {transcription}",
                        }
                    )

                except base64.binascii.Error:
                    return {
                        "error": "El formato del audio no es válido. Debe ser una cadena base64 válida o un archivo de audio.",
                        "id": conversation_id,
                        "title": frontend_data.get("title", "Chat sin título"),
                        "created_at": frontend_data.get(
                            "created_at", "Fecha desconocida"
                        ),
                    }
                except Exception as e:
                    return {
                        "error": f"Error al procesar el audio: {str(e)}",
                        "id": conversation_id,
                        "title": frontend_data.get("title", "Chat sin título"),
                        "created_at": frontend_data.get(
                            "created_at", "Fecha desconocida"
                        ),
                    }
            else:
                return {
                    "error": f"Tipo de entrada no soportado: {input_type}",
                    "id": conversation_id,
                    "title": frontend_data.get("title", "Chat sin título"),
                    "created_at": frontend_data.get("created_at", "Fecha desconocida"),
                }

            # Agregar la respuesta al historial
            openai_data["messages"].append(
                {"role": "assistant", "content": assistant_message}
            )

            frontend_data["messages"].append(
                {"role": "assistant", "content": assistant_message}
            )

            # Guardar la conversación actualizada
            OpenAIService.save_conversation(conversation_id, openai_data, frontend_data)

            # Preparar la respuesta
            response_data = {
                "respuesta": assistant_message,
                "id": conversation_id,
                "title": frontend_data.get("title", "Chat sin título"),
                "created_at": frontend_data.get("created_at", "Fecha desconocida"),
            }

            # Añadir URL de S3 si existe (para imágenes o audio)
            if input_type == InputType.IMAGE:
                # Buscar la URL de la imagen en el último mensaje del usuario
                for m in reversed(frontend_data["messages"]):
                    if (
                        m["role"] == "user"
                        and isinstance(m["content"], str)
                        and m["content"].startswith("http")
                    ):
                        response_data["media_url"] = m["content"]
                        break
            elif input_type == InputType.AUDIO:
                # Buscar la URL del audio en los mensajes del usuario
                for m in reversed(frontend_data["messages"]):
                    if (
                        m["role"] == "user"
                        and isinstance(m["content"], str)
                        and m["content"].startswith("URL del audio:")
                    ):
                        audio_url = m["content"].split("URL del audio: ")[1]
                        response_data["media_url"] = audio_url
                        break

            return response_data

        except Exception as e:
            return {
                "error": str(e),
                "id": conversation_id,
                "title": (
                    frontend_data.get("title", "Chat sin título")
                    if "frontend_data" in locals()
                    else "Chat sin título"
                ),
                "created_at": (
                    frontend_data.get("created_at", "Fecha desconocida")
                    if "frontend_data" in locals()
                    else "Fecha desconocida"
                ),
                "media_url": None,
            }
