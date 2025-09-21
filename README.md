# 🎬 Video Processing Service · FastAPI + Celery + FFmpeg

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.x-37814A.svg)](https://docs.celeryq.dev/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.x-FF6600.svg)](https://www.rabbitmq.com/)
[![Postgres](https://img.shields.io/badge/Postgres-16-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docs.docker.com/compose/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-enabled-007808.svg)](https://ffmpeg.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

Processamento **assíncrono** de vídeos: upload autenticado, extração de frames via **FFmpeg**, empacotamento `.zip` e acompanhamento de status — orquestrado com **Celery**, **RabbitMQ** e **Postgres**.

---

## ✨ Recursos

- 🔐 **Autenticação obrigatória** via serviço externo (`CUSTOMER_SERVICE_URL`)
- ⏫ Upload de vídeo → cria **Video** e **Job**
- 🧩 **FFmpeg** extrai frames (`fps` configurável)
- 📦 Geração de **ZIP** com suporte a **Zip64** (arquivos grandes)
- 📊 Acompanhamento em **/api/jobs** e **/api/jobs/{job_id}**
- 🔭 Observabilidade com **Flower** e painel do **RabbitMQ**

---

## 🗺️ Arquitetura (visão rápida)

```mermaid
flowchart LR
  A[Cliente] -- POST /api/videos --> B[FastAPI API]
  B -- Verifica token --> C[(Customer Service)]
  B -- Enfileira job --> D[(RabbitMQ)]
  E[Celery Worker] -- Consome --> D
  E -- FFmpeg --> F[/Frames temporários/]
  E -- ZIP --> G[(Storage de artefatos)]
  E -- Atualiza status --> H[(Postgres)]
  B -- GET /api/jobs* --> H
  I[Flower] --- D

```
## ✨ Recursos

app/
  adapters/
    driver/
      api/         # rotas/controllers e dependências (FastAPI)
      worker/      # celery_app e task process_video_job
    driven/
      db/          # models, repositórios SQLAlchemy, Unit of Work
      gateway/     # cliente HTTP para autenticação externa
  domain/
    entities.py    # Video, VideoJob, JobStatus
    ports/         # portas: repos, storage, video_processor, auth, uow
    services/      # enqueue_video.py, process_video.py
  config/
    container.py   # composição/DI dos serviços
