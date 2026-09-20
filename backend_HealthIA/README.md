# HealthIA API

FastAPI service used by the HealthIA frontend for conversational guidance and meal-image analysis.

## Run locally

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
copy .env.example .env  # PowerShell; use cp on macOS/Linux
uvicorn main:app --reload --port 8000
```

Then open [http://localhost:8000/docs](http://localhost:8000/docs) for the generated OpenAPI documentation.

## Configuration

Required:

```env
OPENAI_API_KEY=replace-me
OPENAI_MODEL=gpt-4o-mini
```

Optional S3 variables enable remote storage for uploaded media:

```env
AWS_ACCESS_KEY_ID=replace-me
AWS_SECRET_ACCESS_KEY=replace-me
AWS_REGION=us-east-1
S3_BUCKET=healthia
S3_FOLDER=chatbot
S3_PLATES_FOLDER=platos_ia
```

Keep all credentials in `.env` or a secret manager. Never commit them or real health records.

## Endpoints

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/` | Service health message. |
| `PUT` | `/chatbot` | Accepts JSON or multipart text, image, and audio input. |
| `GET` | `/show-chats` | Lists locally persisted conversations. |
| `DELETE` | `/delete-chat/{chat_id}` | Deletes one conversation. |
| `PUT` | `/analyze-image` | Analyzes a meal image using OpenAI vision. |
| `GET` | `/list-analyses` | Lists persisted image analyses. |
| `GET` | `/show-analysis/{analysis_id}` | Retrieves one image analysis. |
| `DELETE` | `/delete-analysis` | Deletes one image analysis. |

The prototype stores conversation and analysis history under ignored runtime directories. For production, replace local JSON persistence with an authenticated database and add user-level isolation, retention policies, and audit logging.

## Code map

```text
main.py                 # FastAPI application and CORS setup
app/models/              # Request and response schemas
app/routers/             # Chat and image-analysis HTTP routes
app/services/            # OpenAI, persistence, and optional S3 services
app/static/              # Assistant system prompt
herramientas/            # Domain agents used by chatbot orchestration
```

## Security notes

- CORS is intentionally permissive for the hackathon prototype; restrict it to known frontend origins before production.
- Do not expose API keys in the frontend or commit `.env` files.
- Add authentication and authorization before handling real personal or medical information.
- Treat all AI output as assistive, non-diagnostic content.
