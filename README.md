# 🤖 HealthIA

> Tu asistente personal inteligente para una vida más saludable — impulsado por Azure, OpenAI, Python y LangGraph.

<img src="https://github.com/user-attachments/assets/6a6dfcd8-726a-41e1-bc6d-92ec5ad27f16" alt="HealthIA Demo"/>

<p align="center">
  <b>Nutrición personalizada, entrenamientos y orientación de salud — desarrollado con Python, Azure, OpenAI y LangGraph para la Hackathon de Microsoft.</b>
</p>

<p align="center">
  <a href="https://www.sergioyupanqui.com" target="_blank">
    <img src="https://img.shields.io/badge/Live-Demo-blue?style=for-the-badge" alt="Demo En Vivo"/>
  </a>
</p>

<p align="center"><strong>👉 ¡Para probarlo ahora, visita <a href="https://sergioyupanqui.com" target="_blank">www.sergioyupanqui.com</a> desde tu PC o móvil y analiza tu propio plato al instante!</strong></p>

---

## 🌟 Resumen General

**HealthIA** es un asistente de bienestar multiagente que combina IA generativa con datos de IoT en tiempo real — como relojes inteligentes, pulseras y sensores biométricos — para generar intervenciones de salud personalizadas. Soporta tanto **español** como **inglés**, adaptándose al estilo de vida, preferencias y hábitos culturales de cada usuario.

Desarrollado con **Python**, **LangGraph** y **Azure Cloud**, HealthIA utiliza agentes de IA modulares para ofrecer consejos contextualizados, usando lenguaje natural, visión por computadora y generación aumentada por recuperación (RAG).

---

## ❓ El Problema

- **🩺 Epidemia de enfermedades crónicas** — Obesidad, diabetes e hipertensión impulsadas por malas rutinas diarias.
- **🚪 Baja interacción con aplicaciones de salud** — La mayoría de los usuarios abandonan en 30 días debido a la falta de relevancia y retroalimentación.
- **📊 Datos de salud fragmentados** — Los wearables y los registros de alimentos están aislados y rara vez se utilizan para retroalimentación personalizada en tiempo real.

---

## 💡 La Solución

La arquitectura de HealthIA orquesta módulos impulsados por IA a través de **LangGraph** y un **backend de Python** (usando FastAPI), permitiendo:

- Coaching conversacional inteligente con **OpenAI (GPT-4o)**
- Reconocimiento de alimentos en tiempo real usando **OpenAI**
- Planes de entrenamiento y comidas personalizados mediante agentes conscientes del contexto
- Restricciones médicas (por ejemplo, alergias, condiciones) que restringen o mejoran dinámicamente las sugerencias

Todos los datos del usuario, métricas de salud y contexto se almacenan en **Azure Cosmos DB** con vectorización para búsqueda avanzada por similitud.

---

## ⚙️ Arquitectura Técnica

- **🤖 Flujo multiagente basado en LangGraph** — Un `SupervisorAgent` central enruta las solicitudes del usuario al trabajador correcto (MealAgent, MedicalAgent, PlannerAgent, etc.)
- **☁ Azure + OpenAI** — Arquitectura en la nube segura y escalable impulsada por GPT-4o y servicios de Azure
- **⌚ Integración IoT** — Sincronización en tiempo real con datos de wearables para sugerencias adaptativas
- **🏅 Motor de gamificación** — Fomenta la participación constante mediante recompensas y estímulos
- **📡 API REST con Python FastAPI** — Endpoints como `/api/v1/chatbot` y `/api/v1/meal` ofrecen acceso modular claro

---

## 💻 ¿Por qué Python?

- **⚡ Productividad con FastAPI** — Rápido desarrollo de API gracias a su diseño moderno, validación automática de datos, serialización y documentación interactiva de API (Swagger UI / ReDoc).
- **🧠 Orquestación Supervisor-Agent** — Los patrones de LangGraph permiten la clasificación modular de solicitudes y la delegación, encajando bien con la flexibilidad de Python.
- **🔗 Rico Ecosistema AI/ML e Integraciones** — Python es el lenguaje de facto para IA/ML, ofreciendo extensas bibliotecas y conexiones fluidas a OpenAI, Azure Vision y servicios de almacenamiento.
- **✅ Capacidades Asíncronas y Tipado Estático (Type Hinting)** — FastAPI está construido sobre Starlette y Pydantic, permitiendo código asíncrono de alto rendimiento y validación de datos robusta a través de las sugerencias de tipo de Python para una mejor calidad de código.

---

## 🔍 Características Principales

### 1. 🧠 Chatbot de Salud
Haz preguntas como:
> “Trabajo de forma remota y siento dolor de espalda.”

Recibirás:
- Sugerencias personalizadas
- Recordatorios basados en actividad
- Planes de estiramiento o hidratación

### 2. 📸 Escáner de Comidas con Open AI
- Toma una foto de tu plato
- La API de Visión analiza el balance nutricional comparado con el Plato de Harvard
- Obtén retroalimentación personalizada: “Añade más vegetales” o “Reduce los carbohidratos”
<p align="center">
  <img src="https://github.com/user-attachments/assets/8493337e-9a81-43b8-ac3d-600db5138898" alt="HealthIA Demo"/>
</p>

### 3. 🥗 Generador de Dietas
- Recetas conscientes del contexto con macros
- Video tutoriales y planes de comidas compartibles
- Se adapta dinámicamente a condiciones médicas y objetivos

<p align="center">
  <img src="https://github.com/user-attachments/assets/94fe574f-51e9-4ef6-b57b-98f08a751b96" alt="HealthIA Demo"/>
</p>

### 4. 🏋️ Planificador de Entrenamientos
- Rutinas semanales personalizadas según tus métricas
- Ajustadas usando datos de sueño, pasos y ritmo cardíaco
- Tutoriales animados y alertas motivacionales

<p align="center">
  <img src="https://github.com/user-attachments/assets/712efe78-cff1-40c6-aa16-f526736e4739" alt="HealthIA Demo"/>
</p>

### 5. 🩺 Personalización Médica
- Adapta los planes ingresando alergias, enfermedades crónicas
- Asegura recomendaciones seguras y efectivas
  
<p align="center">
  <img src="https://github.com/user-attachments/assets/a759a9d0-d627-4262-a1e7-2e68e98e117f" alt="HealthIA Demo"/>
</p>

---

## 📊 Arquitectura del Sistema

<img src="https://github.com/user-attachments/assets/8378437f-831f-47f9-82fd-a9bb34a6db81" alt="Azure Architecture" />

Construido completamente en **Azure Cloud**, incluye:
- Azure API Management
- Azure Functions
- Azure Blob Storage
- Azure AI Vision
- Azure Cosmos DB
- Azure OpenAI
- Azure MySQL
- Azure Monitor
- Azure FrontDoor + WAF

---

## 🤖 Framework Agéntico

<img src="https://github.com/user-attachments/assets/44950f32-f0da-4096-abc9-980f42d74857" alt="Azure MultiAgent" />

---

# 📈 Diagramas de Secuencia – HealthIA

## 1️⃣ Escáner de Comidas + Retroalimentación IA
<img src="https://github.com/user-attachments/assets/bbb6732a-99c7-4301-a17d-fa31efb634f7" alt="HealthIA 1"/>

## 2️⃣ Interacción del Chatbot de Salud
<img src="https://github.com/user-attachments/assets/5de7974e-f949-4f0b-982c-3affa87efb0c" alt="HealthIA 2"/>

## 3️⃣ Generador de Rutinas de Entrenamiento
<img src="https://github.com/user-attachments/assets/d42d17c3-b126-4b8d-a72f-0a5659cfb5c5" alt="HealthIA 3"/>

---

## 👥 Conoce al Equipo

<p align="center">
  <a href="https://www.linkedin.com/in/fransua-leon/" target="_blank">
    <img src="https://img.shields.io/badge/Fransua%20Leon-LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" />
  </a>
  <a href="https://www.linkedin.com/in/sergioyupanquigomez/" target="_blank">
    <img src="https://img.shields.io/badge/Sergio%20Yupanqui-LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" />
  </a>
  <a href="https://www.linkedin.com/in/luisangelorp/" target="_blank">
    <img src="https://img.shields.io/badge/Luis%20Rodriguez-LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" />
  </a>
  <a href="https://www.linkedin.com/in/diegorojasvera/" target="_blank">
    <img src="https://img.shields.io/badge/Diego%20Rojas-LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" />
  </a>
</p>
