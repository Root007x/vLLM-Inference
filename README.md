# LLM Inference API

A production-ready, self-hosted LLM inference gateway built with **FastAPI** and **vLLM**. Features API key authentication, concurrency control, rate limiting, structured JSON logging, and a full observability stack (metrics + logs) via Prometheus, Loki, and Grafana.

---

## Architecture

```
Client
  │
  ▼
FastAPI Gateway (:9000)
  │  ├── Auth (X-Api-Key)
  │  ├── Rate Limiting (slowapi)
  │  ├── Concurrency Control (asyncio.Semaphore)
  │  └── Prometheus Metrics (/metrics)
  │
  ▼
vLLM OpenAI-compatible Server (:8000)
  │
  ▼
GPU (NVIDIA)
```

```
Observability Stack
  ├── Prometheus (:9090)  ← scrapes API, vLLM, DCGM GPU metrics
  ├── Loki (:3100)        ← stores structured JSON logs
  ├── Alloy               ← collects Docker container logs → Loki
  └── Grafana (:3000)     ← dashboards for metrics + logs
```

---

## Services

| Service    | Port | Description                                   |
|------------|------|-----------------------------------------------|
| `api`      | 9000 | FastAPI inference gateway                     |
| `vllm`     | 8000 | vLLM OpenAI-compatible server                 |
| `prometheus`| 9090| Metrics collection                            |
| `grafana`  | 3000 | Dashboards and alerting                       |
| `loki`     | 3100 | Log aggregation backend                       |
| `alloy`    | —    | Grafana Alloy log collector (Docker → Loki)   |
| `dcgm`     | 9400 | NVIDIA GPU metrics exporter                   |

---

## Prerequisites

- Docker and Docker Compose
- NVIDIA GPU with drivers installed
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) (`nvidia-docker`)
- A [Hugging Face](https://huggingface.co/) account and access token

---

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
HF_TOKEN="hf_your_token_here"
MODEL="meta-llama/Llama-3-8B-Instruct"
API_KEY="your_secret_api_key"
```

### 2. Start all services

```bash
docker compose up -d
```

### 3. Verify the gateway is running

```bash
curl http://localhost:9000/health
# {"status": "ok"}
```

---

## API Reference

All inference endpoints require the `X-Api-Key` header.

### `POST /v1/chat` — Chat Completion

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

**Response:**
```json
{
  "model": "meta-llama/Llama-3-8B-Instruct",
  "output": "Hello! How can I assist you today?"
}
```

### `POST /v1/chat/stream` — Streaming Chat Completion

Returns a `text/event-stream` response with tokens as they are generated.

```bash
curl -X POST http://localhost:9000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_secret_api_key" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 512
  }'
```

### `GET /health` — Health Check

```bash
curl http://localhost:9000/health
# {"status": "ok"}
```

### `GET /metrics` — Prometheus Metrics

```bash
curl http://localhost:9000/metrics
```

---

## Request Schema

| Field         | Type            | Default | Description                        |
|---------------|-----------------|---------|------------------------------------|
| `messages`    | `list[dict]`    | —       | OpenAI-format message list         |
| `temperature` | `float`         | `0.7`   | Sampling temperature               |
| `max_tokens`  | `int`           | `512`   | Maximum tokens to generate         |

---

## Configuration

| Variable                | Required | Default                    | Description                                    |
|-------------------------|----------|----------------------------|------------------------------------------------|
| `HF_TOKEN`              | Yes      | —                          | Hugging Face token for model downloads         |
| `MODEL`                 | Yes      | —                          | Model ID (e.g. `meta-llama/Llama-3-8B-Instruct`) |
| `API_KEY`               | Yes      | —                          | API key for request authentication             |
| `VLLM_URL`              | No       | `http://vllm:8000/v1`      | vLLM backend endpoint                          |
| `MAX_CONCURRENT_REQUESTS` | No     | `10`                       | Max simultaneous in-flight requests (semaphore)|

---

## vLLM Configuration

The vLLM server is configured with the following defaults (see `docker-compose.yml`):

| Parameter                | Value  | Description                              |
|--------------------------|--------|------------------------------------------|
| `--quantization`         | `compressed-tensors` | Model quantization format      |
| `--dtype`                | `auto` | Automatic dtype selection                |
| `--max-model-len`        | `4096` | Maximum context length in tokens         |
| `--gpu-memory-utilization` | `0.90` | Fraction of GPU memory to use          |
| `--max-num-seqs`         | `8`    | Maximum number of concurrent sequences  |
| `--enable-prefix-caching`| —      | KV-cache prefix reuse for repeated prompts |

---

## Observability

### Grafana
- **URL**: http://localhost:3000
- **Default credentials**: `admin` / `admin`
- Pre-provisioned datasources: Prometheus (metrics) and Loki (logs)

### Prometheus
- **URL**: http://localhost:9090
- Scrapes metrics from:
  - `api` — FastAPI request latency, count, errors via `prometheus-fastapi-instrumentator`
  - `vllm` — Inference throughput, queue length, token counts
  - `dcgm` — NVIDIA GPU utilization, memory, temperature

### Loki + Grafana Alloy
- **Alloy** collects structured JSON logs from all Docker containers via the Docker socket
- **Loki** stores and indexes logs for querying in Grafana
- **URL**: http://localhost:3100

---

## Concurrency & Rate Limiting

- **Concurrency**: An `asyncio.Semaphore` limits in-flight requests to `MAX_CONCURRENT_REQUESTS` (default: `10`). Requests exceeding this return `503 Server busy`.
- **Rate Limiting**: Endpoints are rate-limited via `slowapi`. Returns `429 Too Many Requests` when exceeded.

---

## Load Testing

Load tests use [k6](https://k6.io/). The test script is at [`load_testing/test.js`](load_testing/test.js).

**Default config**: 100 virtual users for 30 seconds against `/v1/chat/stream`.

```bash
# Install k6: https://k6.io/docs/get-started/installation/
k6 run load_testing/test.js
```

---

## Local Development

```bash
# Install dependencies
uv sync

# Run the API server (requires a running vLLM instance)
uv run uvicorn api.app.main:app --reload --port 9000
```

Set `VLLM_URL` in `.env` to point at a running vLLM instance or a mock server for local testing.

---

## Project Structure

```
.
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py           # FastAPI app, routes
│       ├── auth.py           # API key authentication
│       ├── config.py         # Pydantic settings
│       ├── llm.py            # vLLM client, generate & stream logic
│       ├── limiter.py        # slowapi rate limiter setup
│       ├── middleware.py     # HTTP request logging middleware
│       ├── logging_config.py # Structured JSON logging setup
│       └── schemas.py        # Pydantic request schemas
├── prometheus/
│   └── prometheus.yml        # Scrape config
├── grafana/
│   └── provisioning/         # Datasource & dashboard provisioning
├── loki/
│   └── loki-config.yml       # Loki storage config
├── alloy/
│   └── alloy-config.river    # Alloy log pipeline (Docker → Loki)
├── load_testing/
│   └── test.js               # k6 load test script
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```
