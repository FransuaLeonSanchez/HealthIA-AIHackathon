import requests
import sys
import os
import json


def enviar_imagen_para_descripcion(
    imagen_path, mensaje="Describe esta imagen", conversation_id=None
):
    """
    Envía una imagen al chatbot con un mensaje para que la describa.

    Args:
        imagen_path: Ruta al archivo de imagen
        mensaje: Mensaje que acompaña a la imagen
        conversation_id: ID de la conversación (opcional)

    Returns:
        Respuesta del API en formato JSON
    """
    if conversation_id is None:
        conversation_id = 1  # ID por defecto

    # Usar la dirección IP del servidor
    url = "http://0.0.0.0:8000/chatbot"

    # Verificar que el archivo existe
    if not os.path.exists(imagen_path):
        raise FileNotFoundError(f"No se encontró la imagen en {imagen_path}")

    # Preparar los datos del formulario
    payload = {"message": mensaje, "id": conversation_id, "type": "image"}

    # Preparar el archivo
    files = {
        "media_file": (
            os.path.basename(imagen_path),
            open(imagen_path, "rb"),
            "image/jpeg",
        )
    }

    try:
        # Enviar la solicitud
        print(f"Enviando solicitud a {url}...")
        response = requests.put(url, data=payload, files=files)

        # Verificar si la solicitud fue exitosa
        response.raise_for_status()

        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar la solicitud: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Respuesta del servidor: {e.response.text}")
        raise
    finally:
        # Cerrar el archivo
        if "files" in locals() and "media_file" in files:
            files["media_file"][1].close()


def main():
    # Obtener la ruta de la imagen desde los argumentos o usar la predeterminada
    if len(sys.argv) > 1:
        imagen_path = sys.argv[1]
    else:
        # Usar la imagen en el directorio examples
        imagen_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "image.jpg"
        )

    # Obtener el mensaje desde los argumentos o usar el predeterminado
    mensaje = (
        sys.argv[2] if len(sys.argv) > 2 else "Di algun objeto que veas en la imagen"
    )

    # Obtener el ID de conversación desde los argumentos o usar el predeterminado
    conversation_id = int(sys.argv[3]) if len(sys.argv) > 3 else None

    try:
        print(f"Enviando imagen '{imagen_path}' al chatbot...")
        print(f"Mensaje: '{mensaje}'")

        # Enviar la imagen al chatbot
        respuesta = enviar_imagen_para_descripcion(
            imagen_path, mensaje, conversation_id
        )

        # Mostrar la respuesta
        print("\n=== Respuesta del chatbot ===")
        print(f"ID de conversación: {respuesta.get('id')}")
        print(f"Título: {respuesta.get('title')}")
        print(f"Fecha de creación: {respuesta.get('created_at')}")

        # Mostrar la URL de S3 si existe
        if respuesta.get("media_url"):
            print(f"\nURL de la imagen en S3: {respuesta.get('media_url')}")

        print("\nDescripción:")
        print(respuesta.get("respuesta") or respuesta.get("error"))

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
