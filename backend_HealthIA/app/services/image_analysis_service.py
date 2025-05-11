from openai import OpenAI
import os
from typing import Dict, Any, Optional, List
import base64
from dotenv import load_dotenv
from app.models.chat_models import (
    AnalisisPlato,
    ImageDimensions,
    ImageAnalysisHistoryResponse,
    ImageAnalysisSummary,
)
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from app.services.s3_service import S3Service, S3_PLATES_FOLDER
import tempfile
import logging
import sys
import traceback
import json
import time
from pathlib import Path

# Configurar el logger
logger = logging.getLogger("image_analysis_service")
logger.setLevel(logging.INFO)
# Asegurar que los logs se muestren en la consola
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

# Cargar variables de entorno
load_dotenv()

# Validar que existe la API key
if not os.getenv("OPENAI_API_KEY"):
    logger.error("La variable de entorno OPENAI_API_KEY no está configurada")
    raise ValueError("La variable de entorno OPENAI_API_KEY no está configurada")


class ImageAnalysisService:
    _instance = None
    _client = None
    # Almacenamiento en memoria para los análisis
    _analyses: Dict[int, Dict] = {}
    _next_id: int = 1
    # Ruta del archivo JSON para persistencia
    _json_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "analyses.json",
    )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ImageAnalysisService, cls).__new__(cls)
            # Inicializar cliente OpenAI
            try:
                load_dotenv()
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "No se encontró la clave API de OpenAI en las variables de entorno"
                    )

                cls._client = OpenAI(api_key=api_key)
                logger.info("Cliente OpenAI inicializado correctamente")

                # Cargar análisis desde el archivo JSON si existe
                cls._load_analyses_from_json()
            except Exception as e:
                logger.error(f"Error al inicializar el cliente OpenAI: {str(e)}")
                logger.error(traceback.format_exc())
        return cls._instance

    @classmethod
    def _load_analyses_from_json(cls):
        """
        Carga los análisis desde el archivo JSON si existe.
        """
        try:
            # Asegurar que el directorio data existe
            os.makedirs(os.path.dirname(cls._json_file_path), exist_ok=True)

            if os.path.exists(cls._json_file_path):
                logger.info(f"Cargando análisis desde {cls._json_file_path}")
                with open(cls._json_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # Cargar análisis
                    cls._analyses = {}
                    for analysis_id, analysis_data in data.get("analyses", {}).items():
                        # Convertir ID de string a int
                        analysis_id = int(analysis_id)

                        # Convertir fecha de string a datetime
                        if "fecha" in analysis_data and isinstance(
                            analysis_data["fecha"], str
                        ):
                            analysis_data["fecha"] = datetime.fromisoformat(
                                analysis_data["fecha"]
                            )

                        # Convertir analisis de dict a AnalisisPlato si es necesario
                        if "analisis" in analysis_data and isinstance(
                            analysis_data["analisis"], dict
                        ):
                            analysis_data["analisis"] = AnalisisPlato.parse_obj(
                                analysis_data["analisis"]
                            )

                        cls._analyses[analysis_id] = analysis_data

                    # Actualizar next_id para garantizar que sea mayor que cualquier ID existente
                    if cls._analyses:
                        max_id = max(cls._analyses.keys())
                        stored_next_id = data.get("next_id", 1)
                        cls._next_id = max(max_id + 1, stored_next_id)
                        logger.info(
                            f"_next_id actualizado a {cls._next_id} (max_id={max_id}, stored_next_id={stored_next_id})"
                        )
                    else:
                        cls._next_id = data.get("next_id", 1)

                    logger.info(
                        f"Cargados {len(cls._analyses)} análisis. Próximo ID: {cls._next_id}"
                    )
            else:
                logger.info(
                    f"No se encontró archivo de análisis en {cls._json_file_path}. Iniciando con lista vacía."
                )
                cls._next_id = 1
        except Exception as e:
            logger.error(f"Error al cargar análisis desde JSON: {str(e)}")
            logger.error(traceback.format_exc())
            # Si hay error, iniciar con lista vacía
            cls._analyses = {}
            cls._next_id = 1

    @classmethod
    def _save_analyses_to_json(cls):
        """
        Guarda los análisis en el archivo JSON.
        """
        try:
            # Verificar integridad antes de guardar
            cls._verify_analyses_integrity()

            # Asegurar que el directorio data existe
            os.makedirs(os.path.dirname(cls._json_file_path), exist_ok=True)

            # Preparar datos para serialización
            serializable_analyses = {}
            for analysis_id, analysis_data in cls._analyses.items():
                # Crear una copia para no modificar el original
                serializable_analysis = dict(analysis_data)

                # Convertir fecha a string ISO
                if "fecha" in serializable_analysis and isinstance(
                    serializable_analysis["fecha"], datetime
                ):
                    serializable_analysis["fecha"] = serializable_analysis[
                        "fecha"
                    ].isoformat()

                # Convertir AnalisisPlato a dict
                if "analisis" in serializable_analysis and isinstance(
                    serializable_analysis["analisis"], AnalisisPlato
                ):
                    serializable_analysis["analisis"] = serializable_analysis[
                        "analisis"
                    ].dict()

                serializable_analyses[str(analysis_id)] = serializable_analysis

            data = {
                "analyses": serializable_analyses,
                "next_id": cls._next_id,
                "last_updated": datetime.now().isoformat(),
            }

            # Guardar en archivo con formato legible
            with open(cls._json_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(
                f"Guardados {len(cls._analyses)} análisis en {cls._json_file_path}"
            )
        except Exception as e:
            logger.error(f"Error al guardar análisis en JSON: {str(e)}")
            logger.error(traceback.format_exc())

    @classmethod
    def _verify_analyses_integrity(cls):
        """
        Verifica la integridad de los análisis almacenados.
        - Asegura que no haya IDs duplicados
        - Verifica que _next_id sea mayor que cualquier ID existente
        - Comprueba que cada análisis tenga los campos requeridos
        """
        try:
            # Verificar que no haya IDs duplicados
            ids = list(cls._analyses.keys())
            if len(ids) != len(set(ids)):
                logger.warning(
                    "Se detectaron IDs duplicados en los análisis. Esto no debería ocurrir."
                )

            # Verificar que _next_id sea mayor que cualquier ID existente
            if cls._analyses and cls._next_id <= max(cls._analyses.keys()):
                logger.warning(
                    f"_next_id ({cls._next_id}) es menor o igual que el máximo ID existente ({max(cls._analyses.keys())}). Corrigiendo..."
                )
                cls._next_id = max(cls._analyses.keys()) + 1

            # Verificar que cada análisis tenga los campos requeridos
            for analysis_id, analysis_data in cls._analyses.items():
                required_fields = [
                    "id",
                    "fecha",
                    "analisis",
                    "imagen_original_url",
                    "imagen_procesada_url",
                ]
                missing_fields = [
                    field for field in required_fields if field not in analysis_data
                ]
                if missing_fields:
                    logger.warning(
                        f"El análisis con ID {analysis_id} no tiene los campos requeridos: {missing_fields}"
                    )

            logger.info("Verificación de integridad completada")
        except Exception as e:
            logger.error(f"Error al verificar la integridad de los análisis: {str(e)}")
            logger.error(traceback.format_exc())

    @classmethod
    def _get_prompt(cls, dimensions: ImageDimensions) -> str:
        """Genera el prompt incluyendo las dimensiones de la imagen"""
        area_total = dimensions.width * dimensions.height
        logger.info(
            f"Dimensiones de imagen: {dimensions.width}x{dimensions.height} (área: {area_total})"
        )
        return f"""Eres un sistema avanzado de visión por computadora especializado en el análisis nutricional de imágenes. 

INFORMACIÓN DE LA IMAGEN:
- Dimensiones: {dimensions.width}x{dimensions.height} píxeles
- Área total: {area_total} píxeles cuadrados

TAREA:
Analiza la siguiente imagen de un plato de comida y proporciona:

1. Lista de alimentos detectados:
   Identifica cada alimento visible en el plato con la mayor precisión posible.

2. Cálculo de área ocupada:
   Para cada alimento, calcula:
   - Coordenadas precisas (x1, y1, x2, y2) del rectángulo que lo contiene
   - Porcentaje aproximado del área total del plato que ocupa

   Donde:
   - x1, y1: coordenadas exactas de la esquina superior izquierda
   - x2, y2: coordenadas exactas de la esquina inferior derecha
   - Porcentaje de área = (área del alimento / área total de la imagen) * 100

   Validaciones:
   * La suma de porcentajes de todos los alimentos debe ser EXACTAMENTE 100%
   * Las coordenadas deben ser precisas y ajustarse exactamente al contorno del alimento
   * Evita solapamiento significativo entre áreas de diferentes alimentos

3. Clasificación de alimentos según el Plato de Harvard:
   Categoriza cada alimento en una de estas categorías:
   - Verduras/vegetales (objetivo ideal: 50% del plato)
   - Proteínas (objetivo ideal: 25% del plato)
   - Carbohidratos (objetivo ideal: 25% del plato)

   IMPORTANTE:
   * El porcentaje de verduras es la suma de los porcentajes de todos los alimentos clasificados como "Verduras/vegetales"
   * El porcentaje de proteínas es la suma de los porcentajes de todos los alimentos clasificados como "Proteínas"
   * El porcentaje de carbohidratos es la suma de los porcentajes de todos los alimentos clasificados como "Carbohidratos"

4. Evaluación del plato:
   Basado en las proporciones reales detectadas:
   - "Plato saludable": Si las proporciones están dentro de ±10% de los objetivos del Plato de Harvard
   - "Plato desequilibrado": Si alguna proporción se desvía más del 10%

5. Recomendaciones nutricionales personalizadas:
   PRIMERO: Analiza cuidadosamente si la imagen realmente muestra un plato de comida. Si no es comida o no tiene sentido dar recomendaciones nutricionales, proporciona observaciones adecuadas al contexto.
   
   Si ES un plato de comida, proporciona hasta 3 recomendaciones altamente personalizadas:
   
   - Observa el tipo específico de comida (por ejemplo, desayuno, almuerzo, cena, snack, plato típico específico)
   - Identifica el estilo culinario (mediterráneo, asiático, latinoamericano, etc.) y adapta tus recomendaciones
   - Analiza el equilibrio del plato según lo que realmente se ve, no te inventes alimentos que no estén visibles
   - Si el plato ya está bien equilibrado, no fuerces recomendaciones negativas; puedes reforzar lo positivo
   
   EJEMPLOS de recomendaciones personalizadas:
   - "El arroz integral que has elegido es excelente, pero ocupa el 45% del plato. Reduce la porción a 1/4 e incrementa las verduras para mejor equilibrio."
   - "Tu plato de pasta contiene buena proteína, pero añade más vegetales de colores variados (50g de espinacas y 30g de pimientos) para aumentar nutrientes."
   - "Este desayuno tiene buena proteína del huevo, añade 1/2 aguacate y cambia el pan blanco por integral para mejorar grasas saludables y fibra."
   
   Las recomendaciones deben:
   - Ser ultrapersonalizadas, específicas para ESTA imagen concreta, no genéricas
   - Mencionar ingredientes exactos que se ven en la imagen
   - Sugerir mejoras con cantidades concretas
   - Adaptarse al tipo de comida/plato específico
   - Si el plato está bien equilibrado, reconócelo y refuerza los aspectos positivos
   - Cada recomendación debe tener MÁXIMO 200 caracteres
   - NO dar recomendaciones si no es comida o no tiene sentido nutricional

FORMATO DE RESPUESTA:
Responde ÚNICAMENTE en formato JSON con esta estructura exacta:
{{
  "evaluacion_general": "Plato saludable" o "Plato desequilibrado" o "No aplicable" (si no es comida),
  "porcentaje_verduras": número entre 0 y 100 (suma de todos los alimentos en esta categoría),
  "porcentaje_proteinas": número entre 0 y 100 (suma de todos los alimentos en esta categoría),
  "porcentaje_carbohidratos": número entre 0 y 100 (suma de todos los alimentos en esta categoría),
  "detalle_alimentos": [
    {{
      "nombre": "nombre del alimento",
      "categoria": "Verduras/vegetales|Proteínas|Carbohidratos",
      "porcentaje_area": número entre 0.1 y 100.0,
      "coordenadas": {{
        "x1": entero entre 0 y {dimensions.width - 1},
        "y1": entero entre 0 y {dimensions.height - 1},
        "x2": entero entre x1 y {dimensions.width - 1},
        "y2": entero entre y1 y {dimensions.height - 1}
      }}
    }}
  ],
  "recomendaciones": [
    "Primera recomendación ultrapersonalizada relacionada con los alimentos visibles",
    "Segunda recomendación ultrapersonalizada relacionada con los alimentos visibles",
    "Tercera recomendación ultrapersonalizada relacionada con los alimentos visibles"
  ]
}}

IMPORTANTE:
- Las coordenadas DEBEN ser números enteros precisos dentro de los límites especificados
- Los porcentajes de área de todos los alimentos DEBEN sumar EXACTAMENTE 100% (muy importante)
- Si la imagen NO contiene comida o alimentos reconocibles, marca "No aplicable" en evaluación, 0% en porcentajes y proporciona observaciones adecuadas en recomendaciones
- Cada recomendación debe ser extremadamente específica a la imagen analizada, mencionando exactamente lo que ves
- No sigas un patrón mecánico, adapta tus recomendaciones al tipo de plato específico (desayuno, almuerzo, etc.)
- Si el plato ya tiene buenas proporciones, reconócelo en vez de inventar problemas
- Cada recomendación debe tener un MÁXIMO de 200 caracteres"""

    @classmethod
    def _get_image_dimensions(cls, image_data: bytes) -> ImageDimensions:
        """
        Calcula las dimensiones de una imagen a partir de sus bytes.
        """
        try:
            # Abrir la imagen con PIL
            with Image.open(BytesIO(image_data)) as img:
                width, height = img.size
                logger.info(f"Dimensiones obtenidas: {width}x{height}")
                return ImageDimensions(width=width, height=height)
        except Exception as e:
            error_msg = f"Error al procesar la imagen: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise ValueError(error_msg)

    @staticmethod
    def get_color_for_category(categoria: str) -> tuple:
        """Retorna un color RGB según la categoría del alimento"""
        colors = {
            "Verduras/vegetales": (76, 175, 80),  # Verde
            "Proteínas": (244, 67, 54),  # Rojo
            "Carbohidratos": (255, 193, 7),  # Amarillo
        }
        return colors.get(categoria, (158, 158, 158))  # Gris por defecto

    @staticmethod
    def normalize_coordinates(
        coords: Dict[str, float], image_width: int, image_height: int
    ) -> Dict[str, int]:
        """
        Normaliza las coordenadas para asegurar que estén dentro de los límites de la imagen
        y las convierte a valores enteros.
        """
        try:
            return {
                "x1": max(0, min(int(coords["x1"]), image_width - 1)),
                "y1": max(0, min(int(coords["y1"]), image_height - 1)),
                "x2": max(0, min(int(coords["x2"]), image_width - 1)),
                "y2": max(0, min(int(coords["y2"]), image_height - 1)),
            }
        except Exception as e:
            logger.error(f"Error al normalizar coordenadas: {str(e)}")
            # Devolver valores predeterminados seguros
            return {
                "x1": 0,
                "y1": 0,
                "x2": min(10, image_width - 1),
                "y2": min(10, image_height - 1),
            }

    @classmethod
    def draw_analysis_on_image(cls, image_data: bytes, analysis_result: Dict) -> str:
        """
        Dibuja un área semitransparente sobre cada alimento individual detectado,
        mostrando su categoría y retorna la imagen en base64.
        """
        try:
            logger.info("Dibujando análisis en la imagen...")
            with Image.open(BytesIO(image_data)) as img:
                # Obtener dimensiones de la imagen
                image_width, image_height = img.size
                logger.info(
                    f"Dimensiones de la imagen para dibujo: {image_width}x{image_height}"
                )

                # Convertir a RGB si es necesario
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Crear una capa de overlay para las áreas semitransparentes
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                draw_overlay = ImageDraw.Draw(overlay)

                # Crear objeto para dibujar texto en la imagen principal
                draw = ImageDraw.Draw(img)

                # Intentar cargar una fuente, si no está disponible usar default
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except:
                    font = ImageFont.load_default()

                # Dibujar cada alimento detectado
                logger.info(
                    f"Dibujando {len(analysis_result['detalle_alimentos'])} alimentos..."
                )
                for alimento in analysis_result["detalle_alimentos"]:
                    categoria = alimento["categoria"]
                    logger.info(f"Dibujando: {alimento['nombre']} ({categoria})")

                    # Normalizar coordenadas al tamaño de la imagen
                    coords = cls.normalize_coordinates(
                        alimento["coordenadas"], image_width, image_height
                    )
                    logger.info(f"Coordenadas normalizadas: {coords}")

                    # Verificar si el área es válida
                    if coords["x2"] <= coords["x1"] or coords["y2"] <= coords["y1"]:
                        logger.warning(
                            f"Coordenadas inválidas para {alimento['nombre']}: {coords}"
                        )
                        continue

                    color = cls.get_color_for_category(categoria)

                    # Crear color semitransparente (agregar canal alpha)
                    color_overlay = color + (80,)  # Alpha=80 para mejor visibilidad

                    # Dibujar área semitransparente para este alimento específico
                    draw_overlay.rectangle(
                        [(coords["x1"], coords["y1"]), (coords["x2"], coords["y2"])],
                        fill=color_overlay,
                    )

                    # Calcular posición para la etiqueta
                    text_pos = (coords["x1"] + 2, coords["y1"] + 2)
                    text_alimento = (
                        f"{alimento['nombre']} ({alimento['porcentaje_area']:.1f}%)"
                    )

                    # Agregar fondo semi-transparente para la etiqueta
                    text_bbox = draw.textbbox(text_pos, text_alimento, font=font)
                    # Verificar si hay espacio suficiente para la etiqueta y si está dentro de la imagen
                    if (
                        (text_bbox[2] - text_bbox[0]) <= (coords["x2"] - coords["x1"])
                        and text_bbox[2] <= image_width
                        and text_bbox[3] <= image_height
                    ):
                        draw.rectangle(text_bbox, fill=(0, 0, 0, 160))
                        draw.text(text_pos, text_alimento, fill=color, font=font)

                # Combinar la imagen original con el overlay
                img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

                # Convertir la imagen procesada a base64
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=95)
                buffer.seek(0)

                logger.info("Imagen procesada correctamente")
                return base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:
            error_msg = f"Error al procesar la imagen para dibujo: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise Exception(error_msg)

    @classmethod
    async def analyze_image(
        cls,
        image_base64: str = None,
        analysis_id: Optional[int] = None,
        media_content: bytes = None,
        original_filename: str = None,
    ) -> AnalisisPlato:
        """
        Analiza una imagen y guarda el resultado en el historial.
        Soporta tanto imágenes en base64 como archivos binarios.
        """
        logger.info(f"Iniciando análisis de imagen - ID solicitado: {analysis_id}")

        # Si no se proporciona ID o el ID ya existe, generar uno nuevo
        if analysis_id is None:
            analysis_id = cls._next_id
            cls._next_id += 1
            logger.info(f"ID generado automáticamente: {analysis_id}")
        elif analysis_id in cls._analyses:
            # Si el ID ya existe, generar uno nuevo para evitar sobrescribir
            logger.warning(
                f"El ID {analysis_id} ya existe. Generando un nuevo ID para evitar sobrescribir."
            )
            analysis_id = cls._next_id
            cls._next_id += 1
            logger.info(f"Nuevo ID generado: {analysis_id}")
        elif analysis_id >= cls._next_id:
            # Si el ID proporcionado es mayor que _next_id, actualizar _next_id
            cls._next_id = analysis_id + 1
            logger.info(
                f"Actualizando _next_id a {cls._next_id} basado en el ID proporcionado"
            )

        image_url = None
        temp_image_path = None

        try:
            # Asegurarse de que el cliente existe
            if not cls._client:
                logger.info("Cliente OpenAI no inicializado, creando instancia...")
                cls()

            # Determinar la fuente de la imagen
            image_data = None
            if media_content:
                logger.info(f"Usando media_content ({len(media_content)} bytes)")
                image_data = media_content
            elif image_base64:
                try:
                    logger.info("Decodificando imagen base64...")
                    image_data = base64.b64decode(image_base64)
                    logger.info(f"Imagen decodificada ({len(image_data)} bytes)")
                except Exception as e:
                    error_msg = (
                        f"La imagen en base64 proporcionada no es válida: {str(e)}"
                    )
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    raise ValueError(error_msg)
            else:
                error_msg = "Debe proporcionar una imagen en base64 o un archivo"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Validar el tamaño de la imagen
            if len(image_data) > 10 * 1024 * 1024:  # 10MB
                raise ValueError(
                    "La imagen es demasiado grande. El tamaño máximo permitido es 10MB"
                )

            # Obtener dimensiones y validar formato de imagen
            try:
                logger.info("Validando formato y dimensiones de la imagen...")
                with Image.open(BytesIO(image_data)) as img:
                    if img.format.lower() not in ["jpeg", "jpg", "png", "gif"]:
                        raise ValueError(
                            f"Formato de imagen no soportado: {img.format}"
                        )
                    dimensions = ImageDimensions(width=img.width, height=img.height)
                    logger.info(
                        f"Dimensiones obtenidas: {dimensions.width}x{dimensions.height}"
                    )
            except Exception as e:
                error_msg = f"Error al procesar la imagen: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                raise ValueError(error_msg)

            # Determinar la extensión del archivo
            file_extension = "jpg"  # Valor predeterminado
            if original_filename:
                _, ext = os.path.splitext(original_filename)
                if ext and ext.startswith("."):
                    file_extension = ext[1:].lower()
                logger.info(f"Extensión determinada: {file_extension}")
            else:
                logger.info(f"Usando extensión predeterminada: {file_extension}")

            # Subir imagen original a S3
            logger.info("Subiendo imagen original a S3...")
            s3_result = S3Service.upload_file_to_s3(
                file_content=image_data,
                file_extension=file_extension,
                conversation_id=analysis_id,
                original_filename=original_filename,
                folder=S3_PLATES_FOLDER,
            )

            if not s3_result["success"]:
                error_msg = (
                    f"Error al guardar la imagen en S3: {s3_result.get('error')}"
                )
                logger.error(error_msg)
                raise Exception(error_msg)

            image_url = s3_result["url"]
            logger.info(f"Imagen original subida a S3: {image_url}")

            # Crear archivo temporal para OpenAI
            logger.info("Creando archivo temporal...")
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{file_extension}"
            ) as temp_image:
                temp_image.write(image_data)
                temp_image_path = temp_image.name
                logger.info(f"Archivo temporal creado: {temp_image_path}")

            try:
                # Leer la imagen y convertirla a base64 para enviarla a la API
                logger.info("Preparando imagen para enviar a OpenAI...")
                with open(temp_image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                    logger.info(
                        f"Imagen codificada en base64 ({len(base64_image)} caracteres)"
                    )

                # Llamar a la API de OpenAI
                logger.info("Llamando a la API de OpenAI...")
                try:
                    response = cls._client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": cls._get_prompt(dimensions),
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/{file_extension};base64,{base64_image}"
                                        },
                                    },
                                ],
                            }
                        ],
                        max_tokens=1000,
                        response_format={"type": "json_object"},
                    )
                    logger.info("Respuesta recibida de OpenAI")
                except Exception as api_error:
                    error_msg = (
                        f"Error en la llamada a la API de OpenAI: {str(api_error)}"
                    )
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    raise Exception(error_msg)

                # Obtener y procesar la respuesta
                logger.info("Procesando respuesta...")
                analysis = response.choices[0].message.content
                logger.info(f"Contenido de la respuesta: {analysis}")

                try:
                    # Usar json.loads en lugar de eval para mayor seguridad y mejor manejo de errores
                    analysis_dict = json.loads(analysis)

                    # Verificar si las recomendaciones están completas
                    if "recomendaciones" in analysis_dict and isinstance(
                        analysis_dict["recomendaciones"], list
                    ):
                        for i, recomendacion in enumerate(
                            analysis_dict["recomendaciones"]
                        ):
                            if not isinstance(recomendacion, str):
                                logger.warning(
                                    f"Recomendación en índice {i} no es una cadena válida, corrigiendo formato"
                                )
                                analysis_dict["recomendaciones"][i] = str(recomendacion)
                            # Truncar recomendaciones demasiado largas
                            elif len(recomendacion) > 200:
                                logger.warning(
                                    f"Recomendación en índice {i} es demasiado larga ({len(recomendacion)} chars), truncando"
                                )
                                analysis_dict["recomendaciones"][i] = (
                                    recomendacion[:197] + "..."
                                )

                    # Normalizar los porcentajes de los alimentos para que sumen exactamente 100%
                    if (
                        "detalle_alimentos" in analysis_dict
                        and isinstance(analysis_dict["detalle_alimentos"], list)
                        and analysis_dict["detalle_alimentos"]
                    ):
                        # Calcular la suma actual de porcentajes
                        suma_porcentajes = sum(
                            alimento.get("porcentaje_area", 0)
                            for alimento in analysis_dict["detalle_alimentos"]
                        )
                        logger.info(
                            f"Suma de porcentajes antes de normalizar: {suma_porcentajes}%"
                        )

                        # Si la suma no es 100%, normalizar los porcentajes
                        if (
                            abs(suma_porcentajes - 100.0) > 0.1
                        ):  # Permitir un pequeño margen de error (0.1%)
                            logger.warning(
                                f"Los porcentajes no suman 100% (suma actual: {suma_porcentajes}%). Normalizando..."
                            )

                            # Factor de normalización
                            factor = (
                                100.0 / suma_porcentajes if suma_porcentajes > 0 else 0
                            )

                            # Aplicar normalización a cada alimento
                            for alimento in analysis_dict["detalle_alimentos"]:
                                if "porcentaje_area" in alimento:
                                    alimento["porcentaje_area"] = (
                                        alimento["porcentaje_area"] * factor
                                    )

                            # Verificar la nueva suma (para logging)
                            nueva_suma = sum(
                                alimento.get("porcentaje_area", 0)
                                for alimento in analysis_dict["detalle_alimentos"]
                            )
                            logger.info(
                                f"Suma de porcentajes después de normalizar: {nueva_suma}%"
                            )

                            # Ajuste final para asegurar exactamente 100%
                            if (
                                analysis_dict["detalle_alimentos"]
                                and abs(nueva_suma - 100.0) > 0.01
                            ):
                                diferencia = 100.0 - nueva_suma
                                analysis_dict["detalle_alimentos"][0][
                                    "porcentaje_area"
                                ] += diferencia
                                logger.info(
                                    f"Ajuste final aplicado: {diferencia}% al primer alimento"
                                )

                    # Recalcular los porcentajes por categoría después de la normalización
                    if "detalle_alimentos" in analysis_dict and isinstance(
                        analysis_dict["detalle_alimentos"], list
                    ):
                        porcentaje_verduras = sum(
                            alimento.get("porcentaje_area", 0)
                            for alimento in analysis_dict["detalle_alimentos"]
                            if alimento.get("categoria") == "Verduras/vegetales"
                        )
                        porcentaje_proteinas = sum(
                            alimento.get("porcentaje_area", 0)
                            for alimento in analysis_dict["detalle_alimentos"]
                            if alimento.get("categoria") == "Proteínas"
                        )
                        porcentaje_carbohidratos = sum(
                            alimento.get("porcentaje_area", 0)
                            for alimento in analysis_dict["detalle_alimentos"]
                            if alimento.get("categoria") == "Carbohidratos"
                        )

                        analysis_dict["porcentaje_verduras"] = porcentaje_verduras
                        analysis_dict["porcentaje_proteinas"] = porcentaje_proteinas
                        analysis_dict["porcentaje_carbohidratos"] = (
                            porcentaje_carbohidratos
                        )

                        logger.info(
                            f"Porcentajes por categoría recalculados: Verduras={porcentaje_verduras}%, Proteínas={porcentaje_proteinas}%, Carbohidratos={porcentaje_carbohidratos}%"
                        )

                    # Verificar si es una imagen de comida
                    es_comida = True
                    if (
                        "evaluacion_general" in analysis_dict
                        and analysis_dict["evaluacion_general"] == "No aplicable"
                    ):
                        logger.info(
                            "La imagen no contiene un plato de comida reconocible"
                        )
                        es_comida = False

                    # Asegurarse de que hay exactamente 3 recomendaciones si es comida
                    if "recomendaciones" not in analysis_dict or not isinstance(
                        analysis_dict["recomendaciones"], list
                    ):
                        logger.warning(
                            "No se encontraron recomendaciones o no es una lista, creando lista vacía"
                        )
                        analysis_dict["recomendaciones"] = []

                    # Si no es comida, asegurarse de que las recomendaciones son adecuadas
                    if not es_comida:
                        # Para no comida, podemos tener 0-1 recomendaciones/observaciones
                        if len(analysis_dict["recomendaciones"]) == 0:
                            analysis_dict["recomendaciones"].append(
                                "Esta imagen no parece contener un plato de comida que pueda ser analizado nutricionalmente."
                            )
                    else:
                        # Para comida, rellenar hasta tener 3 recomendaciones
                        while len(analysis_dict["recomendaciones"]) < 3:
                            logger.warning(
                                f"Faltan recomendaciones, añadiendo recomendación genérica #{len(analysis_dict['recomendaciones'])+1}"
                            )
                            if len(analysis_dict["recomendaciones"]) == 0:
                                analysis_dict["recomendaciones"].append(
                                    "Aumenta la proporción de verduras en tu plato, deben ocupar aproximadamente la mitad de tu plato para una dieta equilibrada."
                                )
                            elif len(analysis_dict["recomendaciones"]) == 1:
                                analysis_dict["recomendaciones"].append(
                                    "Escoge proteínas magras como pollo, pescado o legumbres y limita a un cuarto de tu plato."
                                )
                            else:
                                analysis_dict["recomendaciones"].append(
                                    "Opta por carbohidratos complejos como granos enteros y limita a un cuarto de tu plato para un mejor control glicémico."
                                )

                    analisis = AnalisisPlato.parse_obj(analysis_dict)
                    logger.info(f"Análisis parseado correctamente: {analisis.dict()}")
                except json.JSONDecodeError as json_error:
                    error_msg = (
                        f"Error al decodificar JSON de la respuesta: {str(json_error)}"
                    )
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    logger.error(f"Respuesta original: {analysis}")
                    raise Exception(error_msg)
                except Exception as parse_error:
                    error_msg = f"Error al parsear la respuesta: {str(parse_error)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    logger.error(f"Respuesta original: {analysis}")
                    raise Exception(error_msg)

                # Procesar la imagen con el análisis
                logger.info("Dibujando análisis en la imagen...")
                try:
                    imagen_procesada_base64 = cls.draw_analysis_on_image(
                        image_data, analysis_dict
                    )
                    logger.info("Imagen procesada correctamente")
                except Exception as draw_error:
                    error_msg = f"Error al dibujar el análisis: {str(draw_error)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    raise Exception(error_msg)

                # Subir imagen procesada a S3
                logger.info("Subiendo imagen procesada a S3 en carpeta platos_ia...")
                try:
                    processed_s3_result = S3Service.upload_file_to_s3(
                        file_content=base64.b64decode(imagen_procesada_base64),
                        file_extension=file_extension,
                        conversation_id=analysis_id,
                        original_filename=f"processed_{original_filename if original_filename else 'image'}",
                        folder=S3_PLATES_FOLDER,
                    )

                    if not processed_s3_result["success"]:
                        error_msg = f"Error al guardar la imagen procesada en S3: {processed_s3_result.get('error')}"
                        logger.error(error_msg)
                        raise Exception(error_msg)

                    logger.info(
                        f"Imagen procesada subida a S3: {processed_s3_result['url']}"
                    )
                except Exception as e:
                    error_msg = (
                        f"Error durante la subida de la imagen procesada a S3: {str(e)}"
                    )
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    raise Exception(error_msg)

                # Agregar URLs al análisis
                analisis.imagen_original_url = image_url
                analisis.imagen_procesada_url = processed_s3_result["url"]

                # Guardar el análisis en el historial
                logger.info(f"Guardando análisis ID {analysis_id} en el historial...")
                cls._analyses[analysis_id] = {
                    "id": analysis_id,
                    "fecha": datetime.now(),
                    "analisis": analisis,
                    "imagen_original_url": image_url,
                    "imagen_procesada_url": processed_s3_result["url"],
                }

                # Guardar análisis en JSON
                cls._save_analyses_to_json()

                logger.info(f"Análisis completado exitosamente para ID {analysis_id}")
                return analisis

            finally:
                # Limpiar archivo temporal
                if temp_image_path and os.path.exists(temp_image_path):
                    logger.info(f"Eliminando archivo temporal: {temp_image_path}")
                    os.unlink(temp_image_path)

        except Exception as e:
            # Limpiar recursos en caso de error
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.unlink(temp_image_path)
                    logger.info(f"Archivo temporal eliminado: {temp_image_path}")
                except Exception as cleanup_error:
                    logger.error(
                        f"Error al eliminar archivo temporal: {str(cleanup_error)}"
                    )

            if image_url:
                try:
                    logger.info(
                        f"Intentando eliminar imagen de S3 debido a error: {image_url}"
                    )
                    S3Service.delete_file_from_s3(image_url)
                except Exception as cleanup_error:
                    logger.error(
                        f"Error al eliminar imagen de S3: {str(cleanup_error)}"
                    )

            error_msg = f"Error al analizar la imagen: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise Exception(error_msg)

    @classmethod
    def analysis_exists(cls, analysis_id: int) -> bool:
        """
        Verifica si existe un análisis con el ID especificado leyendo directamente del JSON.
        """
        logger.info(f"Verificando si existe análisis ID {analysis_id} en JSON...")

        try:
            if os.path.exists(cls._json_file_path):
                with open(cls._json_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    exists = str(analysis_id) in data.get("analyses", {})
                    logger.info(f"Verificación completada: {exists}")
                    return exists
            else:
                logger.warning(
                    f"No se encontró archivo de análisis en {cls._json_file_path}"
                )
                return False

        except Exception as e:
            logger.error(f"Error al verificar existencia en JSON: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    @classmethod
    def delete_analysis(cls, analysis_id: int) -> bool:
        """
        Elimina un análisis y sus imágenes asociadas de S3.
        Lee directamente del JSON para asegurar que se elimine correctamente.
        También elimina la carpeta completa del ID en S3.
        """
        logger.info(f"Eliminando análisis ID {analysis_id}...")

        try:
            # Leer directamente del JSON
            if os.path.exists(cls._json_file_path):
                with open(cls._json_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # Verificar si el análisis existe en el JSON
                    if str(analysis_id) not in data.get("analyses", {}):
                        logger.warning(
                            f"No se encontró el análisis ID {analysis_id} en el JSON"
                        )
                        return False

                    # Obtener datos del análisis
                    analysis = data["analyses"][str(analysis_id)]

                    # Eliminar imágenes de S3
                    logger.info("Eliminando imágenes y carpeta de S3...")

                    # Eliminar la carpeta completa del ID en S3
                    folder_path = f"{S3_PLATES_FOLDER}/{analysis_id}"
                    logger.info(f"Eliminando carpeta completa: {folder_path}")
                    S3Service.delete_folder_from_s3(folder_path)

                    # Eliminar análisis del JSON
                    logger.info(f"Eliminando análisis ID {analysis_id} del JSON...")
                    del data["analyses"][str(analysis_id)]

                    # Guardar cambios en JSON
                    with open(cls._json_file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    # También eliminar del diccionario en memoria si existe
                    if analysis_id in cls._analyses:
                        del cls._analyses[analysis_id]

                    logger.info(
                        f"Análisis ID {analysis_id} y su carpeta en S3 eliminados correctamente"
                    )
                    return True
            else:
                logger.warning(
                    f"No se encontró archivo de análisis en {cls._json_file_path}"
                )
                return False

        except Exception as e:
            logger.error(f"Error al eliminar análisis: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    @classmethod
    def get_analysis_history(
        cls, analysis_id: int
    ) -> Optional[ImageAnalysisHistoryResponse]:
        """
        Obtiene el historial de un análisis leyendo directamente del JSON.
        """
        logger.info(
            f"Obteniendo historial para análisis ID {analysis_id} desde JSON..."
        )

        try:
            if os.path.exists(cls._json_file_path):
                with open(cls._json_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    analysis_data = data.get("analyses", {}).get(str(analysis_id))

                    if not analysis_data:
                        logger.warning(
                            f"No se encontró el análisis ID {analysis_id} en el JSON"
                        )
                        return None

                    # Convertir fecha de string a datetime
                    if "fecha" in analysis_data and isinstance(
                        analysis_data["fecha"], str
                    ):
                        analysis_data["fecha"] = datetime.fromisoformat(
                            analysis_data["fecha"]
                        )

                    # Convertir analisis de dict a AnalisisPlato si es necesario
                    if "analisis" in analysis_data and isinstance(
                        analysis_data["analisis"], dict
                    ):
                        analysis_data["analisis"] = AnalisisPlato.parse_obj(
                            analysis_data["analisis"]
                        )

                    logger.info(f"Historial encontrado para análisis ID {analysis_id}")
                    return ImageAnalysisHistoryResponse(
                        id=int(analysis_id),
                        fecha=analysis_data["fecha"],
                        analisis=analysis_data["analisis"],
                        imagen_original_url=analysis_data["imagen_original_url"],
                        imagen_procesada_url=analysis_data["imagen_procesada_url"],
                    )
            else:
                logger.warning(
                    f"No se encontró archivo de análisis en {cls._json_file_path}"
                )
                return None

        except Exception as e:
            logger.error(f"Error al leer análisis desde JSON: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    @classmethod
    def get_all_analyses(cls) -> List[ImageAnalysisHistoryResponse]:
        """
        Obtiene una lista completa de todos los análisis leyendo directamente del JSON.
        """
        logger.info("Obteniendo lista completa de análisis desde el archivo JSON...")

        try:
            if os.path.exists(cls._json_file_path):
                with open(cls._json_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    analyses = []

                    for analysis_id, analysis_data in data.get("analyses", {}).items():
                        # Convertir fecha de string a datetime
                        if "fecha" in analysis_data and isinstance(
                            analysis_data["fecha"], str
                        ):
                            analysis_data["fecha"] = datetime.fromisoformat(
                                analysis_data["fecha"]
                            )

                        # Convertir analisis de dict a AnalisisPlato si es necesario
                        if "analisis" in analysis_data and isinstance(
                            analysis_data["analisis"], dict
                        ):
                            analysis_data["analisis"] = AnalisisPlato.parse_obj(
                                analysis_data["analisis"]
                            )

                        analyses.append(
                            ImageAnalysisHistoryResponse(
                                id=int(analysis_id),
                                fecha=analysis_data["fecha"],
                                analisis=analysis_data["analisis"],
                                imagen_original_url=analysis_data[
                                    "imagen_original_url"
                                ],
                                imagen_procesada_url=analysis_data[
                                    "imagen_procesada_url"
                                ],
                            )
                        )

                    logger.info(
                        f"Encontrados {len(analyses)} análisis en el archivo JSON"
                    )
                    return analyses
            else:
                logger.info(
                    f"No se encontró archivo de análisis en {cls._json_file_path}"
                )
                return []

        except Exception as e:
            logger.error(f"Error al leer análisis desde JSON: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    @classmethod
    def debug_analyses_state(cls) -> Dict:
        """
        Devuelve información de depuración sobre el estado actual de los análisis.
        """
        try:
            # Verificar integridad
            cls._verify_analyses_integrity()

            # Recopilar información de depuración
            debug_info = {
                "total_analyses": len(cls._analyses),
                "next_id": cls._next_id,
                "analysis_ids": sorted(list(cls._analyses.keys())),
                "json_file_exists": os.path.exists(cls._json_file_path),
                "json_file_path": cls._json_file_path,
                "json_file_size": (
                    os.path.getsize(cls._json_file_path)
                    if os.path.exists(cls._json_file_path)
                    else 0
                ),
                "last_modified": (
                    datetime.fromtimestamp(
                        os.path.getmtime(cls._json_file_path)
                    ).isoformat()
                    if os.path.exists(cls._json_file_path)
                    else None
                ),
            }

            logger.info(f"Estado de depuración: {debug_info}")
            return debug_info
        except Exception as e:
            logger.error(f"Error al obtener información de depuración: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "error": str(e),
                "total_analyses": (
                    len(cls._analyses) if hasattr(cls, "_analyses") else "unknown"
                ),
                "next_id": cls._next_id if hasattr(cls, "_next_id") else "unknown",
            }
