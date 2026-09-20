# HealthIA frontend

React 19 frontend for the HealthIA wellness prototype, with a mobile-first experience for nutrition, activity, conversational guidance, and health-profile flows.

**Live UI:** [healthia-ai.vercel.app](https://healthia-ai.vercel.app) · **API:** [backend README](../backend_HealthIA/README.md)

## Quick start

```bash
npm ci
copy .env.example .env.local  # PowerShell; use cp on macOS/Linux
npm start
```

Open [http://localhost:3000](http://localhost:3000). The default development API URL is `http://localhost:8000`; override it with `REACT_APP_API_URL` when the backend runs elsewhere.

## Production build

```bash
npm run build
```

The project is configured for Vercel as a Create React App. Set the Vercel **Root Directory** to `frontend_HealthIA`. The public UI is available at [healthia-ai.vercel.app](https://healthia-ai.vercel.app). Chat and image-analysis actions require a backend URL in `REACT_APP_API_URL`.

## Feature areas

- Login and onboarding flow
- Nutrition and meal-plan screens
- Meal image analysis client
- Conversational assistant client
- Activity and wearable-device views
- Health profile and emergency-contact views

The AI request paths are intentionally configured through `REACT_APP_API_URL`; credentials belong only in the backend environment, never in this frontend bundle.
