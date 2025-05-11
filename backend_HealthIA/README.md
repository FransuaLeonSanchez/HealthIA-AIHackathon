# HealthIA API

API para el chatbot de HealthIA que permite interactuar con modelos de OpenAI.

## Configuración

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Configurar variables de entorno en un archivo `.env`:
```
OPENAI_API_KEY=tu_clave_api_de_openai
OPENAI_MODEL=gpt-4o-mini
```

3. Ejecutar la aplicación:
```bash
uvicorn app.main:app --reload
```

## Endpoints

### Chatbot

**Endpoint:** `PUT /chatbot`

Permite enviar mensajes al chatbot y recibir respuestas. Soporta tres tipos de entrada: texto, imagen y audio. Este endpoint acepta tanto solicitudes JSON como formularios multipart.

#### Opción 1: JSON

##### Parámetros:

- `message`: El mensaje del usuario (texto, imagen en base64 o audio en base64)
- `id`: ID numérico entero de la conversación (obligatorio). Si no existe, se crea una nueva conversación con este ID.
- `type`: Tipo de entrada (`text`, `image`, `audio`). Por defecto es `text`.
- `media_content`: Contenido multimedia opcional (URL o identificador)

##### Ejemplos de uso:

###### 1. Mensaje de texto

```bash
curl -X PUT http://3.89.242.141:8000/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuáles son los síntomas de la diabetes?",
    "id": 1,
    "type": "text"
  }'
```

###### 2. Imagen (base64)

```bash
curl -X PUT http://3.89.242.141:8000/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "message": "BASE64_DE_LA_IMAGEN",
    "id": 2,
    "type": "image"
  }'
```

###### 3. Audio (base64)

```bash
curl -X PUT http://3.89.242.141:8000/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "message": "BASE64_DEL_AUDIO",
    "id": 3,
    "type": "audio"
  }'
```

#### Opción 2: Formulario Multipart

##### Parámetros:

- `message`: El mensaje del usuario (texto)
- `id`: ID numérico entero de la conversación (obligatorio)
- `type`: Tipo de entrada (`text`, `image`, `audio`). Por defecto es `text`.
- `media_file`: Archivo multimedia opcional (imagen o audio)

##### Ejemplos de uso:

###### 1. Mensaje de texto

```bash
curl -X PUT http://3.89.242.141:8000/chatbot \
  -F "message=¿Cuáles son los síntomas de la diabetes?" \
  -F "id=1" \
  -F "type=text"
```

###### 2. Imagen (archivo)

```bash
curl -X PUT http://3.89.242.141:8000/chatbot \
  -F "message=¿Qué puedes ver en esta imagen?" \
  -F "id=2" \
  -F "type=image" \
  -F "media_file=@/ruta/a/la/imagen.jpg"
```

###### 3. Audio (archivo)

```bash
curl -X PUT http://3.89.242.141:8000/chatbot \
  -F "message=Transcribe este audio" \
  -F "id=3" \
  -F "type=audio" \
  -F "media_file=@/ruta/al/audio.mp3"
```

### Obtener todas las conversaciones

**Endpoint:** `GET /show-chats`

Retorna todas las conversaciones disponibles.

```bash
curl -X GET http://3.89.242.141:8000/show-chats
```

### Eliminar una conversación

**Endpoint:** `DELETE /delete-chat/{conversation_id}`

Elimina una conversación específica.

```bash
curl -X DELETE http://3.89.242.141:8000/delete-chat/1
```

## Respuesta

La respuesta del chatbot incluye:

```json
{
  "respuesta": "Respuesta del asistente",
  "id": 1,
  "title": "Título de la conversación",
  "created_at": "2023-07-15 14:30:45"
}
```

En caso de error:

```json
{
  "error": "Mensaje de error",
  "id": 1,
  "title": "Título de la conversación",
  "created_at": "2023-07-15 14:30:45"
}
```

## Integración con React

Para enviar archivos desde un frontend en React, puedes usar FormData:

```javascript
// Ejemplo para enviar una imagen
const handleSubmit = async (message, conversationId, imageFile) => {
  const formData = new FormData();
  formData.append('message', message);
  formData.append('id', conversationId);
  formData.append('type', 'image');
  
  if (imageFile) {
    formData.append('media_file', imageFile);
  }
  
  try {
    const response = await fetch('http://3.89.242.141:8000/chatbot', {
      method: 'PUT',
      body: formData,
    });
    
    const data = await response.json();
    // Procesar la respuesta
    console.log(data);
  } catch (error) {
    console.error('Error:', error);
  }
};
```

## Notas

- Para las imágenes y audios, puedes enviarlos directamente como archivos usando un formulario multipart o codificarlos en base64 y enviarlos a través de JSON.
- El título de la conversación se genera automáticamente basado en el primer mensaje.
- La fecha de creación se guarda en formato "YYYY-MM-DD HH:MM:SS" en la zona horaria de Perú (UTC-5).

## Estructura del proyecto

- `main.py`: Archivo principal de la aplicación
- `app/`: Directorio principal del código
  - `routers/`: Contiene los routers de la API
  - `models/`: Contiene los modelos de datos
  - `services/`: Contiene los servicios de la aplicación
  - `data/`: Directorio donde se almacenan las conversaciones 