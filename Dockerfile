FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE THIRD_PARTY_NOTICES.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir '.[server]'
RUN useradd --create-home signova
USER signova
EXPOSE 8010
CMD ["signova-ref", "serve", "--bank", "/data/bank", "--policy", "/data/policy.json", "--demo-root", "/data", "--host", "0.0.0.0", "--port", "8010"]
