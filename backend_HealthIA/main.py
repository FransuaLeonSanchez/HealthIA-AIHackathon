from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chatbot, image_analysis
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Crear la aplicación FastAPI
app = FastAPI(
    title="HealthIA Chatbot API",
    description="API para el chatbot de HealthIA utilizando OpenAI",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringe esto a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(chatbot.router, tags=["Chatbot"])
app.include_router(image_analysis.router, tags=["Image Analysis"])


# Ruta de inicio
@app.get("/")
async def root():
    return {"mensaje": "Bienvenido a la API de HealthIA Chatbot"}


# Para ejecutar con uvicorn
if __name__ == "__main__":
    import uvicorn

    # Obtener configuración desde variables de entorno
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "True").lower() == "true"

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
