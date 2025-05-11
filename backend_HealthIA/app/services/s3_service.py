import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import uuid
from datetime import datetime
import pytz
import logging
import re
from typing import Optional

# Configurar logger
logger = logging.getLogger("s3_service")
logger.setLevel(logging.INFO)

# Cargar variables de entorno
load_dotenv()

# Configuración de AWS S3
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "healthia")
S3_FOLDER = os.getenv("S3_FOLDER", "chatbot")
S3_PLATES_FOLDER = os.getenv("S3_PLATES_FOLDER", "platos_ia")

# Constantes
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}
MAX_FILENAME_LENGTH = 100


class S3Service:
    @staticmethod
    def get_s3_client():
        """
        Obtiene un cliente de S3 configurado con las credenciales.
        """
        return boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitiza el nombre del archivo para S3.
        - Remueve caracteres especiales
        - Limita la longitud
        - Convierte a minúsculas
        """
        # Remover caracteres especiales
        filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)
        # Convertir a minúsculas
        filename = filename.lower()
        # Limitar longitud
        name, ext = os.path.splitext(filename)
        if len(filename) > MAX_FILENAME_LENGTH:
            return f"{name[:MAX_FILENAME_LENGTH-len(ext)]}{ext}"
        return filename

    @staticmethod
    def validate_file_extension(filename: str) -> str:
        """
        Valida y retorna la extensión del archivo.
        Retorna la extensión por defecto (jpg) si no es válida.
        """
        if not filename:
            return "jpg"

        _, ext = os.path.splitext(filename)
        ext = ext[1:].lower() if ext else "jpg"

        return ext if ext in ALLOWED_EXTENSIONS else "jpg"

    @staticmethod
    def generate_s3_key(folder: str, analysis_id: Optional[int], filename: str) -> str:
        """
        Genera una clave única para S3 con la estructura correcta.
        """
        # Sanitizar el nombre del archivo
        safe_filename = S3Service.sanitize_filename(filename)

        # Generar timestamp
        peru_timezone = pytz.timezone("America/Lima")
        timestamp = datetime.now(peru_timezone).strftime("%Y%m%d_%H%M%S")

        # Generar ID único
        unique_id = str(uuid.uuid4())[:8]

        if analysis_id is not None:
            return f"{folder}/{analysis_id}/{timestamp}_{unique_id}_{safe_filename}"
        else:
            return f"{folder}/{timestamp}_{unique_id}_{safe_filename}"

    @staticmethod
    def upload_file_to_s3(
        file_content: bytes,
        file_extension: str = "jpg",
        conversation_id: Optional[int] = None,
        original_filename: Optional[str] = None,
        folder: Optional[str] = None,
    ) -> dict:
        """
        Sube un archivo a S3 y devuelve la URL.

        Args:
            file_content: Contenido del archivo en bytes
            file_extension: Extensión del archivo (por defecto jpg)
            conversation_id: ID de la conversación (opcional)
            original_filename: Nombre original del archivo (opcional)
            folder: Carpeta personalizada para almacenar el archivo (opcional)

        Returns:
            Dict con success, url y file_name
        """
        try:
            # Validar el contenido del archivo
            if not file_content:
                raise ValueError("El contenido del archivo está vacío")

            # Determinar la carpeta a usar
            s3_folder = folder if folder else S3_FOLDER
            logger.info(f"Usando carpeta S3: {s3_folder}")

            # Validar y corregir la extensión del archivo
            file_extension = S3Service.validate_file_extension(
                original_filename if original_filename else f"file.{file_extension}"
            )

            # Generar nombre de archivo seguro
            filename = (
                original_filename if original_filename else f"image.{file_extension}"
            )

            # Generar clave S3
            file_name = S3Service.generate_s3_key(s3_folder, conversation_id, filename)

            # Obtener el cliente de S3
            s3_client = S3Service.get_s3_client()

            # Subir el archivo a S3
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=file_name,
                Body=file_content,
                ContentType=f"image/{file_extension}",
            )

            # Generar y verificar la URL
            url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{file_name}"

            # Verificar que el archivo se subió correctamente
            try:
                s3_client.head_object(Bucket=S3_BUCKET, Key=file_name)
                logger.info(f"Archivo subido exitosamente: {url}")
            except ClientError:
                raise Exception("No se pudo verificar la subida del archivo")

            return {"success": True, "url": url, "file_name": file_name}

        except ClientError as e:
            logger.error(f"Error de AWS S3: {str(e)}")
            return {"success": False, "error": f"Error de AWS S3: {str(e)}"}
        except Exception as e:
            logger.error(f"Error al subir archivo a S3: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_file_from_s3(file_url: str) -> dict:
        """
        Elimina un archivo de S3 usando su URL.

        Args:
            file_url: URL completa del archivo en S3

        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Extraer el nombre del archivo de la URL
            file_name = file_url.split(f"{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/")[1]

            # Obtener el cliente de S3
            s3_client = S3Service.get_s3_client()

            # Verificar que el archivo existe antes de eliminarlo
            try:
                s3_client.head_object(Bucket=S3_BUCKET, Key=file_name)
            except ClientError:
                logger.warning(f"El archivo {file_name} no existe en S3")
                return {"success": False, "error": "El archivo no existe en S3"}

            # Eliminar el archivo de S3
            s3_client.delete_object(Bucket=S3_BUCKET, Key=file_name)

            # Verificar que el archivo se eliminó
            try:
                s3_client.head_object(Bucket=S3_BUCKET, Key=file_name)
                raise Exception("El archivo no se eliminó correctamente")
            except ClientError:
                logger.info(f"Archivo {file_name} eliminado correctamente")
                return {
                    "success": True,
                    "message": f"Archivo {file_name} eliminado correctamente",
                }

        except ClientError as e:
            logger.error(f"Error de AWS S3: {str(e)}")
            return {"success": False, "error": f"Error de AWS S3: {str(e)}"}
        except Exception as e:
            logger.error(f"Error al eliminar archivo de S3: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_folder_from_s3(folder_path: str) -> dict:
        """
        Elimina una carpeta completa y su contenido de S3.

        Args:
            folder_path: Ruta de la carpeta en S3 a eliminar

        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Obtener el cliente de S3
            s3_client = S3Service.get_s3_client()

            # Listar todos los objetos en la carpeta
            objects_to_delete = s3_client.list_objects_v2(
                Bucket=S3_BUCKET, Prefix=folder_path
            )

            # Si no hay objetos, retornar éxito
            if "Contents" not in objects_to_delete:
                logger.info(f"No se encontraron objetos en la carpeta {folder_path}")
                return {
                    "success": True,
                    "message": f"No se encontraron objetos en la carpeta {folder_path}",
                }

            # Eliminar cada objeto en la carpeta
            for obj in objects_to_delete["Contents"]:
                logger.info(f"Eliminando objeto: {obj['Key']}")
                s3_client.delete_object(Bucket=S3_BUCKET, Key=obj["Key"])

            logger.info(f"Carpeta {folder_path} eliminada correctamente")
            return {
                "success": True,
                "message": f"Carpeta {folder_path} eliminada correctamente",
            }

        except ClientError as e:
            logger.error(f"Error de AWS S3: {str(e)}")
            return {"success": False, "error": f"Error de AWS S3: {str(e)}"}
        except Exception as e:
            logger.error(f"Error al eliminar carpeta de S3: {str(e)}")
            return {"success": False, "error": str(e)}
