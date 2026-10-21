FROM node:22-bookworm-slim AS web
WORKDIR /app/apps/web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build
FROM python:3.13-slim-bookworm AS app
RUN apt-get update && apt-get install -y --no-install-recommends g++ && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml setup.py ./
COPY core/ core/
COPY meridian/ meridian/
RUN pip install --upgrade pip && pip install --no-cache-dir .
COPY scripts/ scripts/
COPY --from=web /app/apps/web/dist/ /app/apps/web/dist/
# API resolves web assets relative to the installed package.
RUN mkdir -p /usr/local/lib/python3.13/site-packages/apps/web && cp -r apps/web/dist /usr/local/lib/python3.13/site-packages/apps/web/
RUN useradd --uid 10001 --create-home meridian && mkdir -p data && chown meridian:meridian data
USER meridian
EXPOSE 8000
CMD ["sh", "-c", "python scripts/seed.py && uvicorn meridian.api:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]
