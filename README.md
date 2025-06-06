# YouTube Analyzer

AI-powered YouTube video analysis platform that provides deep insights into video content, audience engagement, and performance metrics using advanced machine learning models.

## 🚀 Features

- **Video Content Analysis**: Extract insights from video content using OpenAI's advanced AI models
- **Audience Engagement Tracking**: Monitor views, likes, comments, and engagement patterns
- **Performance Metrics**: Comprehensive analytics dashboard with real-time data
- **Export Capabilities**: Generate reports in multiple formats (JSON, Markdown, PDF, HTML)
- **Real-time Updates**: WebSocket-powered live updates for analysis progress
- **Scalable Architecture**: Microservices-based design with Docker containerization

## 🏗️ Architecture

This project follows a modern microservices architecture:

- **Backend**: FastAPI with Python 3.11+
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Database**: PostgreSQL for persistent data storage
- **Cache**: Redis for session management and task queuing
- **Task Queue**: Celery for asynchronous video processing
- **Containerization**: Docker and Docker Compose for development and deployment

## 📋 Prerequisites

- **Docker & Docker Compose**: For containerized development
- **Node.js 18+**: For frontend development
- **Python 3.11+**: For backend development
- **Git**: For version control

### Required API Keys

- **OpenAI API Key**: For AI-powered video analysis
- **YouTube Data API v3 Key**: For video metadata retrieval

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/benzdriver/youtubeAnalyze.git
cd youtubeAnalyze
```

### 2. Environment Configuration

Copy the environment template and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` and provide the required values:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/youtube_analyzer

# Security
SECRET_KEY=your_very_long_secret_key_change_this_in_production

# Optional: Redis URL (defaults to redis://localhost:6379)
REDIS_URL=redis://localhost:6379
```

### 3. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (development only)

## 🛠️ Development Setup

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements-dev.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run linting
black . && flake8 .
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Run linting
npm run lint
```

## 📁 Project Structure

```
youtubeAnalyzer/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API route handlers
│   │   ├── core/              # Core configuration and utilities
│   │   ├── models/            # Database models
│   │   ├── services/          # Business logic services
│   │   └── utils/             # Utility functions
│   ├── tests/                 # Backend tests
│   ├── requirements.txt       # Production dependencies
│   ├── requirements-dev.txt   # Development dependencies
│   └── Dockerfile            # Production Docker image
├── frontend/                  # Next.js frontend application
│   ├── src/
│   │   ├── app/              # Next.js app directory
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utility libraries
│   │   ├── store/            # State management
│   │   └── types/            # TypeScript type definitions
│   ├── package.json          # Frontend dependencies
│   └── Dockerfile           # Production Docker image
├── docs/                     # Project documentation
├── docker-compose.yml        # Development environment
└── .env.example             # Environment variables template
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ | - |
| `REDIS_URL` | Redis connection string | ❌ | `redis://localhost:6379` |
| `OPENAI_API_KEY` | OpenAI API key for AI analysis | ✅ | - |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key | ✅ | - |
| `SECRET_KEY` | Secret key for JWT tokens | ✅ | - |
| `ENVIRONMENT` | Application environment | ❌ | `development` |
| `DEBUG` | Enable debug mode | ❌ | `false` |
| `ALLOWED_ORIGINS` | CORS allowed origins | ❌ | `http://localhost:3000` |

### Feature Flags

Configure optional features through environment variables:

```env
# Analytics and tracking
NEXT_PUBLIC_ENABLE_ANALYTICS=false

# Export functionality
NEXT_PUBLIC_ENABLE_EXPORT=true

# Real-time updates
NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES=true

# Debug mode for frontend
NEXT_PUBLIC_ENABLE_DEBUG=false
```

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_config.py
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## 🚀 Deployment

### Production Environment

1. **Configure Environment Variables**: Set production values in your deployment environment
2. **Build Docker Images**: Use production Dockerfiles for optimized builds
3. **Database Setup**: Ensure PostgreSQL is configured with proper security
4. **Redis Setup**: Configure Redis for production workloads
5. **SSL/TLS**: Enable HTTPS for secure communication

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Monitoring and Health Checks

- **Health Endpoint**: `GET /health` - Application health status
- **Metrics**: Built-in performance monitoring
- **Logging**: Structured logging with configurable levels
- **Error Tracking**: Comprehensive error handling and reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the coding standards
4. Run tests: `npm test` and `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Coding Standards

- **Python**: Follow PEP 8, use Black for formatting, Flake8 for linting
- **TypeScript**: Follow ESLint configuration, use Prettier for formatting
- **Commits**: Use Conventional Commits format
- **Documentation**: Update documentation for new features

## 📝 API Documentation

When running in development mode, comprehensive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Security

- **Environment Variables**: Never commit secrets to version control
- **API Keys**: Store securely and rotate regularly
- **CORS**: Configure allowed origins appropriately
- **Authentication**: JWT-based authentication for API access
- **Input Validation**: Comprehensive input validation and sanitization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` directory for detailed guides
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas

## 🙏 Acknowledgments

- OpenAI for providing advanced AI models
- YouTube Data API for video metadata access
- The open-source community for excellent tools and libraries

---

**Built with ❤️ for the YouTube creator community**
