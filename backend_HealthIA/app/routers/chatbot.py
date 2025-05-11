from fastapi import (
    APIRouter,
    HTTPException,
    File,
    Form,
    UploadFile,
    Body,
    Depends,
    Request,
)
from app.models.chat_models import (
    ChatRequest,
    AllChatsResponse,
    ChatResponse,
    InputType,
)
from app.services.openai_service import OpenAIService
from herramientas.supervisor_agent import SupervisorAgent
from herramientas.nutrition_agent import NutritionAgent
from herramientas.exercise_agent import ExerciseAgent
from herramientas.medical_agent import MedicalAgent
from typing import Optional
import json
import sys
import logging
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Configurar el logger
logger = logging.getLogger("chatbot_api")
logger.setLevel(logging.INFO)
# Asegurar que los logs se muestren en la consola
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

router = APIRouter()

# Inicializar el Supervisor y registrar los agentes especializados
supervisor_agent = SupervisorAgent(api_key=os.environ.get("OPENAI_API_KEY"))

# Registrar los agentes especializados con el supervisor
try:
    # Inicializar agentes especializados
    agente_nutricion = NutritionAgent(api_key=os.environ.get("OPENAI_API_KEY"))
    agente_ejercicio = ExerciseAgent(api_key=os.environ.get("OPENAI_API_KEY"))
    agente_medico = MedicalAgent(api_key=os.environ.get("OPENAI_API_KEY"))

    # Registrar agentes con el supervisor
    supervisor_agent.register_agent("nutricion", agente_nutricion)
    supervisor_agent.register_agent("ejercicio", agente_ejercicio)
    supervisor_agent.register_agent("medico", agente_medico)

    logger.info("Agentes especializados registrados correctamente con el supervisor")
except ImportError as e:
    logger.error(f"Error al importar módulos de agentes: {str(e)}")
    logger.error(
        "Verifique que los archivos de agentes existen y están correctamente implementados"
    )
except Exception as e:
    logger.error(f"Error al registrar agentes especializados: {str(e)}")

# Directorio para almacenar imágenes localmente
IMAGES_DIR = Path("app/static/images")
IMAGES_DIR.mkdir(exist_ok=True, parents=True)


async def process_chatbot_request(
    message: str,
    id: int,
    input_type: InputType,
    media_content=None,
    original_filename=None,
):
    """
    Función auxiliar para procesar solicitudes del chatbot.
    """
    try:
        # Verificar si el mensaje debe procesarse con OpenAI en lugar del supervisor
        if message.startswith("@openai"):
            # Extraer el mensaje real sin el prefijo @openai
            actual_message = message.replace("@openai", "", 1).strip()

            # Proceso normal con OpenAI
            result = await OpenAIService.chat_with_openai(
                message=actual_message,
                conversation_id=id,
                input_type=input_type,
                media_content=media_content,
                original_filename=original_filename,
            )

            return result
        else:
            # Por defecto, procesar con el supervisor_agent
            # Determinar si hay una imagen para procesar
            image_path = None
            media_url = None

            if input_type == InputType.IMAGE and media_content:
                # Extraer la extensión del archivo
                extension = ".jpg"  # Valor por defecto
                if original_filename:
                    _, ext = os.path.splitext(original_filename)
                    extension = ext if ext else ".jpg"

                # Intentar subir a S3 primero
                s3_upload_success = False
                try:
                    from app.services.s3_service import S3Service

                    # Determinar la extensión del archivo
                    file_extension = (
                        extension[1:] if extension.startswith(".") else extension
                    )

                    # Subir la imagen a S3
                    s3_result = S3Service.upload_file_to_s3(
                        file_content=media_content,
                        file_extension=file_extension,
                        conversation_id=id,
                        original_filename=original_filename,
                    )

                    if s3_result["success"]:
                        media_url = s3_result["url"]
                        s3_upload_success = True
                        logger.info(f"Imagen subida a S3: {media_url}")
                except Exception as e:
                    logger.error(f"Error al subir imagen a S3: {str(e)}")
                    # Continuar con guardado local

                # Si falló la subida a S3, guardar localmente
                if not s3_upload_success:
                    try:
                        # Generar nombre único para la imagen
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_filename = (
                            "".join(
                                c
                                for c in original_filename
                                if c.isalnum() or c in "._-"
                            )
                            if original_filename
                            else f"image_{timestamp}{extension}"
                        )
                        local_path = IMAGES_DIR / f"{id}_{timestamp}_{safe_filename}"

                        # Guardar la imagen localmente
                        with open(local_path, "wb") as f:
                            f.write(media_content)

                        # Generar URL relativa para acceder a la imagen
                        media_url = f"/static/images/{local_path.name}"
                        logger.info(f"Imagen guardada localmente: {local_path}")
                    except Exception as e:
                        logger.error(f"Error al guardar imagen localmente: {str(e)}")

                # Guardar temporalmente la imagen para procesarla con el supervisor
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
                temp_file.write(media_content)
                temp_file.close()
                image_path = temp_file.name

            # Procesar con el supervisor_agent
            result_content = supervisor_agent.process_request(message, image_path)

            # Registrar derivación exitosa si se menciona un agente específico
            if "[Agente de Nutricion]" in result_content:
                logger.info(
                    f"Consulta ID {id} derivada exitosamente al agente de nutrición"
                )
            elif "[Agente de Ejercicio]" in result_content:
                logger.info(
                    f"Consulta ID {id} derivada exitosamente al agente de ejercicio"
                )
            elif "[Agente de Medico]" in result_content:
                logger.info(f"Consulta ID {id} derivada exitosamente al agente médico")

            # Eliminar el archivo temporal si se creó
            if image_path:
                try:
                    os.unlink(image_path)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el archivo temporal: {str(e)}")

            # Crear respuesta en el formato esperado por la API (usando la estructura correcta de ChatResponse)
            return {
                "respuesta": result_content,
                "id": id,
                "title": f"Conversación con Supervisor #{id}",
                "created_at": "ahora",
                "media_url": media_url,
                "error": None,
            }
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error al procesar la solicitud: {str(e)}"
        )


@router.put("/chatbot", response_model=ChatResponse)
async def chatbot(
    request: Request,
    chat_request: Optional[ChatRequest] = Body(None),
    message: Optional[str] = Form(None),
    id: Optional[int] = Form(None),
    type: Optional[str] = Form(None),
    media_file: Optional[UploadFile] = File(None),
):
    """
    Endpoint para chatbot con OpenAI.
    Acepta tanto JSON como formularios multipart.

    Para JSON:
    - **message**: El mensaje del usuario (texto, imagen en base64 o audio en base64)
    - **id**: ID numérico entero de la conversación (obligatorio). Si no existe, se crea una nueva conversación con este ID.
    - **type**: Tipo de entrada (text, image, audio). Por defecto es "text".
    - **media_content**: Contenido multimedia opcional (URL o identificador)

    Para formulario multipart:
    - **message**: El mensaje del usuario
    - **id**: ID numérico entero de la conversación (obligatorio)
    - **type**: Tipo de entrada (text, image, audio). Por defecto es "text".
    - **media_file**: Archivo multimedia opcional (imagen o audio)

    Retorna la respuesta de OpenAI, el ID de la conversación, el título generado y la fecha de creación.
    """
    # Registrar nueva solicitud al endpoint
    logger.info(f"NEW REQUEST: /chatbot [PUT]")

    # Determinar si es una solicitud JSON o un formulario
    content_type = request.headers.get("Content-Type", "")

    if "application/json" in content_type:
        # Solicitud JSON
        if not chat_request:
            # Si no se pudo parsear el JSON, intentar leerlo manualmente
            try:
                body = await request.json()
                logger.info(f"RAW BODY: {body}")

                if not isinstance(body, dict):
                    raise HTTPException(
                        status_code=400,
                        detail="El cuerpo de la solicitud debe ser un objeto JSON",
                    )

                message = body.get("message")
                id = body.get("id")
                type_str = body.get("type", "text")
                media_content = body.get("media_content")
                original_filename = body.get("original_filename")

                if not message or id is None:
                    raise HTTPException(
                        status_code=400,
                        detail="Los campos 'message' e 'id' son obligatorios",
                    )

                try:
                    input_type = InputType(type_str)
                except ValueError:
                    raise HTTPException(
                        status_code=400, detail=f"Tipo de entrada no válido: {type_str}"
                    )

                return await process_chatbot_request(
                    message=message,
                    id=id,
                    input_type=input_type,
                    media_content=media_content,
                    original_filename=original_filename,
                )
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="JSON inválido")
        else:
            # Si se pudo parsear el JSON correctamente
            logger.info(f"RAW BODY: {chat_request.dict()}")
            return await process_chatbot_request(
                message=chat_request.message,
                id=chat_request.id,
                input_type=chat_request.type,
                media_content=chat_request.media_content,
                original_filename=getattr(chat_request, "original_filename", None),
            )
    elif "multipart/form-data" in content_type:
        # Solicitud de formulario
        logger.info(
            f"RAW BODY: {{'message': '{message}', 'id': {id}, 'type': '{type if type else 'text'}', 'file': '{media_file.filename if media_file else None}'}}"
        )

        if message is None or id is None:
            raise HTTPException(
                status_code=400, detail="Los campos 'message' e 'id' son obligatorios"
            )

        input_type = InputType(type) if type else InputType.TEXT

        # Procesar el archivo multimedia si existe
        media_content = None
        original_filename = None
        if media_file:
            # Leer el contenido del archivo
            file_content = await media_file.read()
            media_content = file_content
            original_filename = media_file.filename

        return await process_chatbot_request(
            message=message,
            id=id,
            input_type=input_type,
            media_content=media_content,
            original_filename=original_filename,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Formato de solicitud inválido. El Content-Type debe ser 'application/json' o 'multipart/form-data'.",
        )


@router.delete("/delete-chat/{chat_id}")
async def delete_chat(chat_id: int):
    """
    Elimina una conversación existente por su ID.

    - **chat_id**: ID numérico entero de la conversación a eliminar (en la URL).

    Retorna un mensaje de éxito o error.
    """
    # Registrar nueva solicitud al endpoint
    logger.info(f"NEW REQUEST: /delete-chat/{chat_id} [DELETE]")

    try:
        # Verificar si la conversación existe
        if not OpenAIService.conversation_exists(chat_id):
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró la conversación con ID {chat_id}",
            )

        # Eliminar la conversación
        success = OpenAIService.delete_conversation(chat_id)

        if success:
            return {"mensaje": f"Conversación con ID {chat_id} eliminada correctamente"}
        else:
            raise HTTPException(
                status_code=500,
                detail=f"No se pudo eliminar la conversación con ID {chat_id}",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al eliminar la conversación: {str(e)}"
        )


@router.get("/show-chats", response_model=AllChatsResponse)
async def show_all_chats():
    """
    Obtiene todas las conversaciones disponibles.

    Retorna una lista con todas las conversaciones, cada una con su ID y mensajes.
    """
    # Registrar nueva solicitud al endpoint
    logger.info(f"NEW REQUEST: /show-chats [GET]")

    try:
        # Obtener todas las conversaciones
        all_chats = OpenAIService.get_all_conversations()

        return {"chats": all_chats}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener las conversaciones: {str(e)}"
        )
