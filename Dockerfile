FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE THIRD_PARTY_NOTICES.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir '.[server]'
RUN useradd --create-home pose_reference
USER pose_reference
EXPOSE 8010
CMD ["pose-ref", "serve", "--bank", "/data/bank", "--policy", "/data/policy.json", "--demo-root", "/data", "--host", "0.0.0.0", "--port", "8010"]
