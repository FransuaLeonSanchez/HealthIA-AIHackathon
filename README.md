# 🤖 HealthIA

> Your intelligent personal assistant for a healthier life — powered by Azure, OpenAI, Python, and LangGraph.

<img src="https://github.com/user-attachments/assets/6a6dfcd8-726a-41e1-bc6d-92ec5ad27f16" alt="HealthIA Demo"/>

<p align="center">
  <b>Personalized nutrition, workouts, and health guidance — developed with Python, Azure, OpenAI, and LangGraph for the Microsoft Hackathon.</b>
</p>

<p align="center">
  <a href="https://sergioyupanqui.com" target="_blank">
    <img src="https://img.shields.io/badge/Live-Demo-blue?style=for-the-badge" alt="Live Demo"/>
  </a>
</p>

<p align="center"><strong>👉 To try it now, visit <a href="https://sergioyupanqui.com" target="_blank">www.sergioyupanqui.com</a> from your PC or mobile and analyze your own plate instantly!</strong></p>

---

## 🌟 Overview

**HealthIA** is a multi-agent wellness assistant that combines generative AI with real-time IoT data — such as smartwatches, bands, and biometric sensors — to generate personalized health interventions. It supports both **Spanish** and **English**, adapting to each user's lifestyle, preferences, and cultural habits.

Developed with **Python**, **LangGraph**, and **Azure Cloud**, HealthIA leverages modular AI agents to deliver contextualized advice, using natural language, computer vision, and retrieval-augmented generation (RAG).

---

## ❓ The Problem

- **🩺 Chronic disease epidemic** — Obesity, diabetes, and hypertension driven by poor daily routines.
- **🚪 Low engagement with health apps** — Most users quit within 30 days due to lack of relevance and feedback.
- **📊 Fragmented health data** — Wearables and food logs are siloed and rarely used for real-time personalized feedback.

---

## 💡 The Solution

HealthIA's architecture orchestrates AI-powered modules via **LangGraph** and a **Python backend** (using FastAPI), enabling:

- Smart conversational coaching with **OpenAI (GPT-4o)**
- Real-time food recognition using **OpenAI**
- Custom workout and meal plans via context-aware agents
- Medical constraints (e.g., allergies, conditions) that dynamically restrict or enhance suggestions

All user data, health metrics, and context are stored in **Azure Cosmos DB** with vectorization for advanced similarity search.

---

## ⚙️ Technical Architecture

- **🤖 LangGraph-based multi-agent flow** — A central `SupervisorAgent` routes user requests to the correct worker (MealAgent, MedicalAgent, PlannerAgent, etc.)
- **☁ Azure + OpenAI** — Secure, scalable cloud architecture powered by GPT-4o and Azure services
- **⌚ IoT Integration** — Real-time sync with wearable data for adaptive suggestions
- **🏅 Gamification engine** — Encourages consistent engagement via rewards and nudges
- **📡 REST API with Python FastAPI** — Endpoints like `/api/v1/chatbot` and `/api/v1/meal` offer clear modular access

---

## 💻 Why Python?

- **⚡ FastAPI productivity** — Rapid API development thanks to its modern design, automatic data validation, serialization, and interactive API documentation (Swagger UI / ReDoc).
- **🧠 Supervisor-Agent orchestration** — LangGraph patterns allow modular request classification and delegation, fitting well with Python's flexibility.
- **🔗 Rich AI/ML Ecosystem & Integrations** — Python is the de-facto language for AI/ML, offering extensive libraries and seamless connections to OpenAI, Azure Vision, and storage services.
- **✅ Asynchronous Capabilities & Type Hinting** — FastAPI is built on Starlette and Pydantic, enabling high-performance asynchronous code and robust data validation through Python type hints for better code quality.

---

## 🔍 Core Features

### 1. 🧠 Health Chatbot
Ask questions like:
> "I work remotely and feel back pain."

You'll receive:
- Personalized suggestions
- Activity-based reminders
- Stretching or hydration plans

### 2. 📸 Meal Scanner with Open AI
- Snap a photo of your plate
- Vision API analyzes nutritional balance vs Harvard Plate
- Get custom feedback: "Add more greens" or "Reduce carbs"
<p align="center">
  <img src="https://github.com/user-attachments/assets/8493337e-9a81-43b8-ac3d-600db5138898" alt="HealthIA Demo"/>
</p>

### 3. 🥗 Diet Generator
- Context-aware recipes with macros
- Video tutorials and shareable meal plans
- Dynamically adapts to medical conditions and goals

<p align="center">
  <img src="https://github.com/user-attachments/assets/94fe574f-51e9-4ef6-b57b-98f08a751b96" alt="HealthIA Demo"/>
</p>

### 4. 🏋️ Workout Planner
- Weekly routines personalized to your metrics
- Adjusted using sleep, steps, heart rate
- Animated tutorials and motivational alerts

<p align="center">
  <img src="https://github.com/user-attachments/assets/712efe78-cff1-40c6-aa16-f526736e4739" alt="HealthIA Demo"/>
</p>

### 5. 🩺 Medical Personalization
- Tailor plans by inputting allergies, chronic illnesses
- Ensures safe, effective recommendations
  
<p align="center">
  <img src="https://github.com/user-attachments/assets/a759a9d0-d627-4262-a1e7-2e68e98e117f" alt="HealthIA Demo"/>
</p>

---

## 📊 System Architecture

<img src="https://github.com/user-attachments/assets/8378437f-831f-47f9-82fd-a9bb34a6db81" alt="Azure Architecture" />

Built fully on **Azure Cloud**, it includes:
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

## 🤖 Agentic Framework

<img src="https://github.com/user-attachments/assets/44950f32-f0da-4096-abc9-980f42d74857" alt="Azure MultiAgent" />

---

# 📈 Sequence Diagrams – HealthIA

## 1️⃣ Meal Scanner + AI Feedback
<img src="https://github.com/user-attachments/assets/bbb6732a-99c7-4301-a17d-fa31efb634f7" alt="HealthIA 1"/>

## 2️⃣ Health Chatbot Interaction
<img src="https://github.com/user-attachments/assets/5de7974e-f949-4f0b-982c-3affa87efb0c" alt="HealthIA 2"/>

## 3️⃣ Workout Routine Generator
<img src="https://github.com/user-attachments/assets/d42d17c3-b126-4b8d-a72f-0a5659cfb5c5" alt="HealthIA 3"/>

---

## 👥 Meet the Team

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
  <a href="https://www.linkedin.com/in/andrepachecot/" target="_blank">
    <img src="https://img.shields.io/badge/André%20Pacheco-LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" />
  </a>
</p>
