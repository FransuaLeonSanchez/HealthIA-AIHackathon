from fastapi import APIRouter, HTTPException, File, Form, UploadFile, Body, Request
from app.models.chat_models import (
    ImageAnalysisRequest,
    AnalisisPlato,
    DeleteImageAnalysisRequest,
    ImageAnalysisHistoryResponse,
)
from app.services.image_analysis_service import ImageAnalysisService
from typing import Optional
import json
import sys
import logging
import traceback

# Configurar el logger
logger = logging.getLogger("image_analysis_api")
logger.setLevel(logging.INFO)
# Asegurar que los logs se muestren en la consola
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

router = APIRouter()


@router.put("/analyze-image", response_model=AnalisisPlato)
async def analyze_image(
    request: Request,
    analysis_request: Optional[ImageAnalysisRequest] = Body(None),
    message: Optional[str] = Form(None),
    id: Optional[int] = Form(None),
    media_file: Optional[UploadFile] = File(None),
):
    """
    Endpoint para analizar imágenes de platos de comida usando GPT-4 Vision.
    Acepta tanto JSON como formularios multipart.

    Para JSON:
    - **image_base64**: La imagen codificada en base64
    - **conversation_id**: ID de la conversación para mantener contexto (opcional)

    Para formulario multipart:
    - **message**: Mensaje opcional para el análisis
    - **id**: ID del análisis (opcional)
    - **media_file**: Archivo de imagen

    Retorna un análisis detallado del plato incluyendo:
    - Evaluación general (plato saludable o desequilibrado)
    - Detalles de cada alimento (nombre, categoría, área ocupada y coordenadas)
    - URLs de las imágenes original y procesada en S3
    """
    # Registrar nueva solicitud al endpoint
    logger.info(f"NEW REQUEST: /analyze-image [PUT]")

    # Determinar si es una solicitud JSON o un formulario
    content_type = request.headers.get("Content-Type", "")

    try:
        if "application/json" in content_type:
            # Solicitud JSON
            if not analysis_request:
                # Si no se pudo parsear el JSON, intentar leerlo manualmente
                try:
                    body = await request.json()
                    logger.info(f"RAW BODY: {body}")

                    if not isinstance(body, dict):
                        raise HTTPException(
                            status_code=400,
                            detail="El cuerpo de la solicitud debe ser un objeto JSON",
                        )

                    image_base64 = body.get("image_base64")
                    conversation_id = body.get("conversation_id")

                    if not image_base64:
                        raise HTTPException(
                            status_code=400,
                            detail="El campo 'image_base64' es obligatorio",
                        )

                    logger.info("Llamando a analyze_image con image_base64")
                    result = await ImageAnalysisService.analyze_image(
                        image_base64=image_base64, analysis_id=conversation_id
                    )
                    logger.info(f"RESULTADO: {result.dict() if result else 'None'}")
                    return result
                except json.JSONDecodeError:
                    logger.error("Error al decodificar JSON")
                    raise HTTPException(status_code=400, detail="JSON inválido")
            else:
                # Si se pudo parsear el JSON correctamente
                logger.info(f"RAW BODY: {analysis_request.dict()}")
                logger.info("Llamando a analyze_image con analysis_request")
                result = await ImageAnalysisService.analyze_image(
                    image_base64=analysis_request.image_base64,
                    analysis_id=analysis_request.conversation_id,
                )
                logger.info(f"RESULTADO: {result.dict() if result else 'None'}")
                return result
        elif "multipart/form-data" in content_type:
            # Solicitud de formulario
            logger.info(
                f"RAW BODY: {{'id': {id}, 'file': '{media_file.filename if media_file else None}'}}"
            )

            if not media_file:
                raise HTTPException(
                    status_code=400, detail="Se requiere un archivo de imagen"
                )

            # Leer el contenido del archivo
            file_content = await media_file.read()
            logger.info(f"Archivo leído: {len(file_content)} bytes")

            logger.info("Llamando a analyze_image con media_content")
            result = await ImageAnalysisService.analyze_image(
                analysis_id=id,
                media_content=file_content,
                original_filename=media_file.filename,
            )
            logger.info(f"RESULTADO: {result.dict() if result else 'None'}")
            return result
        else:
            raise HTTPException(
                status_code=400,
                detail="Formato de solicitud inválido. El Content-Type debe ser 'application/json' o 'multipart/form-data'.",
            )
    except ValueError as ve:
        logger.error(f"ValueError: {str(ve)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error general: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error al analizar la imagen: {str(e)}"
        )


@router.delete("/delete-analysis")
async def delete_analysis(delete_request: DeleteImageAnalysisRequest):
    """
    Elimina un análisis de imagen existente por su ID.

    - **id**: ID numérico entero del análisis a eliminar.

    Retorna un mensaje de éxito o error.
    """
    try:
        logger.info(f"DELETE REQUEST: /delete-analysis - ID: {delete_request.id}")
        # Verificar si el análisis existe
        if not ImageAnalysisService.analysis_exists(delete_request.id):
            logger.warning(f"No se encontró el análisis con ID {delete_request.id}")
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró el análisis con ID {delete_request.id}",
            )

        # Eliminar el análisis
        success = ImageAnalysisService.delete_analysis(delete_request.id)

        if success:
            logger.info(f"Análisis con ID {delete_request.id} eliminado correctamente")
            return {
                "mensaje": f"Análisis con ID {delete_request.id} eliminado correctamente"
            }
        else:
            logger.error(f"No se pudo eliminar el análisis con ID {delete_request.id}")
            raise HTTPException(
                status_code=500,
                detail=f"No se pudo eliminar el análisis con ID {delete_request.id}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar el análisis: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error al eliminar el análisis: {str(e)}"
        )


@router.get("/show-analysis/{analysis_id}", response_model=ImageAnalysisHistoryResponse)
async def show_analysis(analysis_id: int):
    """
    Obtiene el historial completo de un análisis de imagen por su ID.

    - **analysis_id**: ID numérico entero del análisis a mostrar.

    Retorna el ID, fecha, detalles del análisis y URLs de las imágenes.
    """
    try:
        logger.info(f"GET REQUEST: /show-analysis/{analysis_id}")
        # Obtener el historial del análisis
        history = ImageAnalysisService.get_analysis_history(analysis_id)

        if history is None:
            logger.warning(f"No se encontró el análisis con ID {analysis_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró el análisis con ID {analysis_id}",
            )

        logger.info(f"ANÁLISIS: {history.dict()}")
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener el historial del análisis: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el historial del análisis: {str(e)}",
        )


@router.get("/list-analyses")
async def list_analyses():
    """
    Obtiene una lista de todos los análisis de imágenes realizados con información completa.

    Retorna una lista con todos los detalles de cada análisis, incluyendo:
    - ID y fecha del análisis
    - Evaluación general del plato
    - Detalles de cada alimento detectado
    - Porcentajes de verduras, proteínas y carbohidratos
    - Recomendaciones nutricionales personalizadas
    - URLs de las imágenes original y procesada
    """
    try:
        logger.info("GET REQUEST: /list-analyses")
        analyses = ImageAnalysisService.get_all_analyses()
        logger.info(f"Encontrados {len(analyses)} análisis completos")
        for a in analyses:
            logger.info(
                f"Análisis ID: {a.id}, Fecha: {a.fecha}, Evaluación: {a.analisis.evaluacion_general}"
            )
        return {"analyses": analyses}
    except Exception as e:
        logger.error(f"Error al obtener la lista de análisis: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error al obtener la lista de análisis: {str(e)}"
        )


@router.get("/debug-analyses")
async def debug_analyses():
    """
    Endpoint de depuración para obtener información sobre el estado actual de los análisis.

    Retorna información detallada sobre:
    - Número total de análisis
    - Próximo ID a utilizar
    - Lista de IDs existentes
    - Información sobre el archivo JSON de persistencia
    """
    try:
        logger.info("GET REQUEST: /debug-analyses")
        debug_info = ImageAnalysisService.debug_analyses_state()
        logger.info(f"Información de depuración obtenida: {debug_info}")
        return debug_info
    except Exception as e:
        logger.error(f"Error al obtener información de depuración: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener información de depuración: {str(e)}",
        )
