# Stage 1: build the React SPA
FROM node:22-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend serving the built SPA as static files
FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-build /frontend/dist ./frontend/dist

ENV STORE_BACKEND=firestore
ENV PORT=8080
EXPOSE 8080

CMD exec gunicorn backend.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT} --timeout 60
