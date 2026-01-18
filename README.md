[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/)

# ML Learning Hub - An application to analyze and summarize machine learning and data science discussions from Reddit communities

An intelligent web application that **analyzes and summarizes machine learning and data science discussions from Reddit communities**. Built with FastAPI backend and responsive frontend, deployed on AWS with containerized architecture.

## Project Demo

Experience the power of ML community insights:

![Home PageView 1](https://github.com/NateChris14/DATA/blob/main/Screenshot%20(819).png)

![Home PageView 2](https://github.com/NateChris14/DATA/blob/main/Screenshot%20(820).png)

![Smart Search](https://github.com/NateChris14/DATA/blob/main/Screenshot%20(818).png)

![Summary Section](https://github.com/NateChris14/DATA/blob/main/Screenshot%20(821).png)

**Demo Video:** [ML Learning Hub](https://youtu.be/1nwBdm5f_EA)

## Features

### **Smart Search Engine**
- **Intelligent Filtering:** Search through hundreds of ML/DS discussions with advanced relevance ranking
- **Multi-Subreddit Support:** Filter by specific communities (datascience, Python, MachineLearning)

### **Trend Analysis**
- **Emerging Topics:** Identify trending discussions in real-time from active ML communities
- **Community Insights:** Understand what's driving conversations in ML/DS

### **AI-Powered Summaries**
- **Concise Summaries:** Get intelligent summaries of complex technical discussions
- **Topic Extraction:** Automatically identify key themes and insights
- **Quick Understanding:** Save time while staying informed about important developments

### **Beginner-Friendly Insights**
- **Learning Paths:** Discover what beginners are asking about most frequently
- **Personalized Recommendations:** Get tailored learning suggestions based on community trends
- **Skill Development:** Track progression from beginner to advanced topics

### **System Monitoring**
- **Real-time Dashboard:** Track pipeline health and system performance
- **Data Coverage:** Monitor data completeness and quality metrics
- **Performance Analytics:** System uptime, response times, and error tracking

## Architecture

### **System Design**
This application follows a modular monolithic architecture with clear separation of concerns:

### **Data Flow**
1. **Reddit API Integration** → Fetch discussions from ML/DS subreddits
2. **Processing Pipeline** → Clean, analyze, and summarize content
3. **PostgreSQL Database** → Store processed data and insights
4. **FastAPI Backend** → Serve REST endpoints for frontend
5. **Responsive Frontend** → Interactive dashboard and user interface

### **Technology Stack**
- **Backend:** Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy
- **Frontend:** JavaScript, HTML5, CSS3, responsive design
- **Database:** PostgreSQL with optimized indexing
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions with automated testing
- **Cloud Infrastructure:** AWS EC2, ECR, self-hosted runners

## Database Schema

![Database Conceptual Design](https://github.com/NateChris14/DATA/blob/main/Conceptual%20Design%20Reddit%20summ%20v2.drawio.png)


![Database Logical Design](https://github.com/NateChris14/DATA/blob/main/Logical%20design%20Reddit%20Summ.drawio.png)


## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Docker & Docker Compose
- Astro CLI (for Airflow development)
- Node.js 14+ (optional, for frontend development)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/NateChris14/Reddit_Summarizer.git
cd Reddit_Summarizer

# Start Airflow and local PostgreSQL with Astro
astro dev start

# Build and run backend service
cd api
docker build -t reddit-api .
docker run -d -p 8000:8000 --name=reddit-api reddit-api

# Build and run frontend service
cd ../frontend
docker build -t ml-hub-frontend .
docker run -d -p 80:80 --name=ml-hub-frontend ml-hub-frontend

## Configuration

### Environment Variables

#### API Configuration
```bash
# Database
PGHOST=localhost
PGPORT=5432
PGDATABASE=postgres
PGUSER=postgres
PGPASSWORD=postgres

# Frontend URLs
FRONTEND_URL_1=http://localhost
FRONTEND_URL_2=http://127.0.0.1

# Reddit API (optional)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_user_agent
```

#### Frontend Configuration
```javascript
// API Configuration
const API_BASE_URL = 'http://localhost:8000';  // Update for production
```

## Running Locally

### Airflow and Database Setup
```bash
# Start Airflow and PostgreSQL containers
astro dev start
# This spins up:
# - PostgreSQL (localhost:5432/postgres, user: postgres, password: postgres)
# - Airflow Web UI (http://localhost:8080/)
# - Scheduler, API Server, DAG Processor, Triggerer
```

### Backend Development
```bash
cd api
# Build Docker image
docker build -t reddit-api .

# Run backend container
docker run -d -p 8000:8000 \
  --name=reddit-api \
  -e PGHOST=localhost \
  -e PGPORT=5432 \
  -e PGDATABASE=postgres \
  -e PGUSER=postgres \
  -e PGPASSWORD=postgres \
  reddit-api

# View logs
docker logs -f reddit-api
```

### Frontend Development
```bash
cd frontend
# Build Docker image
docker build -t frontend .

# Run frontend container
docker run -d -p 80:80 --name=frontend frontend

# View logs
docker logs -f frontend
```

### Development Workflow
1. **Airflow**: `astro dev start` → ETL pipeline and database
2. **Backend**: `cd api && docker build && docker run` → API service
3. **Frontend**: `cd frontend && docker build && docker run` → Web interface
4. **Access**: Frontend at `http://localhost`, API at `http://localhost:8000`

### Testing Suite
```bash
# Backend tests
cd api
pytest -m unit  # Run unit tests only
pytest -m integration  # Run integration tests only
pytest tests/ -v  # Run all tests

# Frontend validation
cd frontend
node -c script.js  # JavaScript syntax check
```

## Deployment (AWS)

### Container Deployment
This project uses containerized deployment with separate ECR repositories:

#### Backend Deployment
```bash
# Build and push to ECR
docker build -t reddit-api ./api
docker tag reddit-api:latest {ecr-registry}/{backend-repo}:latest
docker push {ecr-registry}/{backend-repo}:latest

# Deploy to EC2
docker run -d -p 8000:8000 \
  --name=reddit-api \
  -e PGHOST=${PGHOST} \
  -e PGPORT=${PGPORT} \
  -e PGDATABASE=${PGDATABASE} \
  -e PGUSER=${PGUSER} \
  -e PGPASSWORD=${PGPASSWORD} \
  {ecr-registry}/{backend-repo}:latest
```

#### Frontend Deployment
```bash
# Build and push to ECR
docker build -t frontend ./frontend
docker tag frontend:latest {ecr-registry}/{frontend-repo}:latest
docker push {ecr-registry}/{frontend-repo}:latest

# Deploy to EC2
docker run -d -p 80:80 \
  --name=frontend \
  {ecr-registry}/{frontend-repo}:latest
```

### CI/CD Pipeline
- **GitHub Actions** automatically builds, tests, and deploys on push to main
- **Separate ECR repositories** for backend and frontend images
- **Self-hosted runners** for deployment to EC2 instances
- **Automated testing** with pytest and frontend validation

## Project Structure
```
Reddit_Summarizer/
├── api/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py         # Main FastAPI application
│   │   ├── settings.py      # Configuration management
│   │   └── db.py          # Database connection
│   ├── tests/               # Backend test suite
│   ├── requirements.txt       # Python dependencies
│   ├── test-requirements.txt # Test dependencies
│   └── Dockerfile         # Backend container
├── frontend/               # Web frontend
│   ├── index.html          # Main HTML page
│   ├── script.js           # JavaScript logic
│   ├── style.css           # Styling
│   └── Dockerfile         # Frontend container
├── .github/
│   └── workflows/
│       └── api.yaml        # CI/CD pipeline
├── docker-compose.yml        # Local development
└── README.md              # This file
```

## Testing

### Backend Tests
```bash
cd api
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest -m unit        # Unit tests only
pytest -m integration   # Integration tests only
pytest -m api         # API endpoint tests
```

### Frontend Validation
```bash
cd frontend
# JavaScript syntax validation
node -c script.js

# HTML structure check
find . -name "*.html" -exec echo "Checking {}" \;

# File existence validation
ls -la && echo "Frontend files present"
```

### Test Coverage
- **Unit Tests:** Core business logic, database operations
- **Integration Tests:** API endpoints, database connectivity
- **Frontend Tests:** JavaScript syntax, HTML structure, file validation
- **E2E Tests:** User workflows across frontend and backend

## API Endpoints

### Core Endpoints
```http
# Health check
GET /health

# Trending topics
GET /trends

# Smart search
GET /search

# AI summaries
GET /summaries

# Beginner insights
GET /beginner/insights

# System monitoring
GET /monitoring
```

### Response Format
```json
{
  "status": "success",
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150
  },
  "timestamp": "2024-01-18T12:00:00Z"
}
```

## Frontend Components

### Interactive Features
- **Smooth Navigation:** Click-to-scroll section navigation
- **Responsive Design:** Mobile-first responsive layout
- **Real-time Updates:** Dynamic content loading with loading states
- **User Feedback:** Hover effects and visual interactions

### Sections
1. **Home:** Feature overview and getting started guide
2. **Search:** Advanced search with filtering options
3. **Trends:** Visual trend analysis and insights
4. **Summaries:** AI-powered content summaries
5. **Beginner:** Learning paths and beginner resources
6. **Monitoring:** System health and performance metrics

## Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution
- **New Features:** Additional ML communities, enhanced search algorithms
- **UI/UX:** Improved visualizations, better mobile experience
- **Performance:** Database optimization, caching strategies
- **Documentation:** API docs, user guides, tutorials
- **Testing:** Test coverage, edge cases, integration tests

### Code Standards
- **Python:** Follow PEP 8, use type hints, docstrings
- **JavaScript:** ES6+ standards, JSDoc comments
- **CSS:** BEM methodology, responsive design
- **Commits:** Conventional commit messages

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- **FastAPI** for the excellent web framework
- **Reddit** for providing the community data source
- **Font Awesome** for the icon library
- **AWS** for reliable cloud infrastructure
- **Open Source Community** for inspiration and tools

## Support & Contact

- **Issues:** [GitHub Issues](https://github.com/NateChris14/Reddit_Summarizer/issues)
- **Discussions:** [GitHub Discussions](https://github.com/NateChris14/Reddit_Summarizer/discussions)
- **Email:** menonnathan4@gmail.com

---

**If this project helps you learn ML/DS faster, please give it a star!**

