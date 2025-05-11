from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime


class InputType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"


class ImageDimensions(BaseModel):
    width: int
    height: int


class ImageUrl(BaseModel):
    url: str


class ContentItem(BaseModel):
    type: str
    text: Optional[str] = None
    image_url: Optional[ImageUrl] = None


class ChatRequest(BaseModel):
    message: str
    id: int
    type: InputType = InputType.TEXT
    media_content: Optional[str] = None
    original_filename: Optional[str] = None


class ChatResponse(BaseModel):
    respuesta: str
    id: int
    title: str
    created_at: str
    media_url: Optional[str] = None
    error: Optional[str] = None


class AllChatsResponse(BaseModel):
    chats: List[Dict[str, Any]]


class ImageAnalysisRequest(BaseModel):
    image_base64: Optional[str] = None
    conversation_id: Optional[int] = None
    media_content: Optional[bytes] = None
    original_filename: Optional[str] = None


class DeleteImageAnalysisRequest(BaseModel):
    id: int


class Coordenadas(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class DetalleAlimento(BaseModel):
    nombre: str
    categoria: str
    porcentaje_area: float
    coordenadas: Coordenadas


class AnalisisPlato(BaseModel):
    evaluacion_general: str
    detalle_alimentos: List[DetalleAlimento]
    imagen_original_url: Optional[str] = None
    imagen_procesada_url: Optional[str] = None
    porcentaje_verduras: Optional[float] = None
    porcentaje_proteinas: Optional[float] = None
    porcentaje_carbohidratos: Optional[float] = None
    recomendaciones: Optional[List[str]] = None


class ImageAnalysisSummary(BaseModel):
    id: int
    fecha: datetime
    evaluacion_general: str
    imagen_original_url: str
    imagen_procesada_url: str


class ImageAnalysisHistoryResponse(BaseModel):
    id: int
    fecha: datetime
    analisis: AnalisisPlato
    imagen_original_url: str
    imagen_procesada_url: str
