# Cognium

A local-first AI platform

## Features

- Local LLM inference
- Chat history
- Streaming responses
- PostgreSQL support
- Docker integration
- Configurable inference parameters
- Attachments upload support
    - Raw text files
    - PDF (only text)
    - Image (PNG, JPG, JPEG)
    - Video (MP4 only frames)
- Tool calls support
    - Summarize
    - RAG
    - Web search
    - Web fetch
- Agentic capabilities
- Simple LTM (Long-Term Memory)
- Image generation support
- Text To Speech support

## Requirements
- Docker
- Docker-compose
- Python 3.12 >= and < 3.14

## Installation
1. Clone this repository.

2. Install project dependencies:

```bash
    python install.py
```

## Running
Start the application:

```bash
    python start.py
```

Then open your browser at:

http://localhost:8080