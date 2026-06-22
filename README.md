# LLM Inference API

A self-hosted LLM inference service built with FastAPI and vLLM, featuring API key authentication, rate limiting, and full observability via Prometheus and Grafana.

## Architecture

```
Client → API (FastAPI :9000) → vLLM (:8000) → GPU
                ↓
         Prometheus (:9090) ← Grafana (:3000)
```

| Service      | Port | Description                     |
|-------------|------|---------------------------------|
| api         | 9000 | FastAPI inference gateway       |
| vllm        | 8000 | vLLM OpenAI-compatible server   |
| prometheus  | 9090 | Metrics collection              |
| grafana     | 3000 | Dashboards and alerting         |
| dcgm        | 9400 | NVIDIA GPU metrics exporter     |

## Prerequisites

- Docker and Docker Compose
- NVIDIA GPU with drivers installed
- NVIDIA Container Toolkit (`nvidia-docker`)
- Hugging Face token

## Setup

1. Copy the environment template and fill in your values:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env`:

   ```
   HF_TOKEN="hf_your_token_here"
   MODEL="meta-llama/Llama-3-8B-Instruct"
   API_KEY="your_secret_api_key"
   ```

3. Start all services:

   ```bash
   docker compose up -d
   ```

## API Usage

All endpoints require an `X-Api-Key` header.

### Chat Completion

```bash
curl -X POST http://localhost:9000/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_secret_api_key" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 512
  }'
```

### Streaming

```bash
curl -X POST http://localhost:9000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_secret_api_key" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Health Check

```bash
curl http://localhost:9000/health
```

## Configuration

| Variable   | Required | Description                              |
|-----------|----------|------------------------------------------|
| HF_TOKEN  | Yes      | Hugging Face token for model downloads   |
| MODEL     | Yes      | Model ID (e.g. `meta-llama/Llama-3-8B-Instruct`) |
| API_KEY   | Yes      | API key for authentication               |
| VLLM_URL  | No       | vLLM endpoint (default: `http://vllm:8000/v1`) |

## Monitoring

- **Grafana**: http://localhost:3000 (default admin/admin)
- **Prometheus**: http://localhost:9090

Prometheus scrapes metrics from:
- API (FastAPI instrumentator)
- vLLM inference server
- DCGM GPU exporter

## Rate Limiting

Endpoints are rate-limited to **10 requests per minute** per client IP.

## Local Development

```bash
uv sync
uv run uvicorn api.app.main:app --reload --port 9000
```

Set `VLLM_URL` to a running vLLM instance or mock for local development.
