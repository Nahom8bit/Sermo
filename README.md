# Telegram Bot with LLM Integration

An intelligent Telegram bot that uses Ollama for automated responses, featuring rate limiting, monitoring, and a web-based admin interface.

## Features

- Automated message responses using LLM (Ollama)
- Rate limiting and queue management
- Real-time monitoring and metrics
- Web-based admin dashboard
- Secure authentication and authorization
- Comprehensive logging and error tracking

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL, Redis
- **LLM**: Ollama
- **UI**: Streamlit
- **Monitoring**: Prometheus, Grafana
- **Deployment**: Docker, Docker Compose

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Telegram Bot Token
- Ollama setup

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd telegram_bot
   ```

2. Copy environment file and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the services:
   - API: http://localhost:8000
   - Admin UI: http://localhost:8501
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000

## Development Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

4. Start development server:
   ```bash
   uvicorn src.api.main:app --reload
   ```

## Project Structure

```
telegram_bot/
├── src/
│   ├── api/          # FastAPI application
│   ├── bot/          # Telegram bot logic
│   ├── llm/          # Ollama integration
│   ├── database/     # Database models and migrations
│   ├── utils/        # Utility functions
│   └── config/       # Configuration management
├── tests/            # Test files
├── ui/               # Streamlit dashboard
├── docs/             # Documentation
├── scripts/          # Utility scripts
└── deployment/       # Deployment configurations
```

## Testing

Run tests with:
```bash
pytest
```

## Monitoring

- Prometheus metrics available at `/metrics`
- Grafana dashboards for visualization
- Custom alerts and monitoring

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
