# Pan-Sea Docker Setup

This guide will help you set up and run the Pan-Sea application using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)

## Project Structure

```
pan-sea/
├── pan-sea-backend/          # FastAPI backend
│   ├── Dockerfile
│   ├── .dockerignore
│   └── ...
├── pan-sea-frontend/         # Next.js frontend
│   ├── Dockerfile
│   ├── .dockerignore
│   └── ...
├── docker-compose.yml        # Docker Compose configuration
└── DOCKER-README.md         # This file
```

## Quick Start

1. **Clone and navigate to the project directory:**
   ```bash
   cd /Users/thun/Desktop/pan-sea
   ```

2. **Set up environment variables:**
   ```bash
   ./setup-env.sh
   ```
   Then edit the created `.env` files with your actual API keys and database URLs.

3. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

4. **Access the applications:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Backend API Documentation: http://localhost:8000/docs

## Available Commands

### Development Commands

```bash
# Build and start services in the background
docker-compose up -d --build

# View logs
docker-compose logs

# View logs for a specific service
docker-compose logs backend
docker-compose logs frontend

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v

# Rebuild specific service
docker-compose build backend
docker-compose build frontend
```

### Production Commands

```bash
# Start in production mode
docker-compose -f docker-compose.yml up -d

# Update services with zero downtime
docker-compose up -d --no-deps backend
docker-compose up -d --no-deps frontend
```

## Environment Configuration

**⚠️ IMPORTANT:** Before running Docker, you must set up environment variables or the backend will fail to start.

### Quick Setup

Run the automated environment setup script:

```bash
./setup-env.sh
```

This script will:
- Create `.env` files from templates
- Generate secure secret keys
- Guide you through required configuration

### Manual Setup

#### Backend Environment Variables

Create a `.env` file in the `pan-sea-backend` directory (copy from `env.template`):

```bash
cp pan-sea-backend/env.template pan-sea-backend/.env
```

Then edit `pan-sea-backend/.env` with your actual values:

```env
# Required - Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Required - Authentication
SECRET_KEY=your_generated_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional - External APIs
OPENAI_API_KEY=your_openai_api_key

# Application Settings
DEBUG=True
ALLOWED_ORIGINS=["http://localhost:3000"]
HOST=0.0.0.0
PORT=8000
```

### Frontend Environment Variables

Create a `.env.local` file in the `pan-sea-frontend` directory:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# External APIs
NEXT_PUBLIC_GOOGLE_API_KEY=your_google_api_key
```

## Service Details

### Backend Service (pan-sea-backend)

- **Port:** 8000
- **Technology:** FastAPI with Python 3.11
- **Health Check:** Available at `/docs`
- **Volumes:** 
  - `./pan-sea-backend/uploads:/app/uploads` (for file uploads)
  - `backend_data:/app/data` (for persistent data)

### Frontend Service (pan-sea-frontend)

- **Port:** 3000
- **Technology:** Next.js 15.4.6 with Node.js 18
- **Health Check:** Available at root path `/`
- **Dependencies:** Depends on backend service

## Troubleshooting

### Common Issues

1. **Module Resolution Issues (e.g., '@google/generative-ai'):**
   ```bash
   # Fix multiple lockfiles issue
   cd pan-sea-frontend
   rm -f package-lock.json
   npm install
   
   # Or if using yarn
   rm -f yarn.lock
   npm install
   
   # Then rebuild the Docker image
   docker-compose build --no-cache frontend
   ```

2. **Port Already in Use:**
   ```bash
   # Check what's using the port
   lsof -i :3000
   lsof -i :8000
   
   # Kill the process or change ports in docker-compose.yml
   ```

3. **Build Failures:**
   ```bash
   # Clean Docker cache
   docker system prune -a
   
   # Rebuild without cache
   docker-compose build --no-cache
   
   # For specific service
   docker-compose build --no-cache frontend
   docker-compose build --no-cache backend
   ```

4. **Permission Issues:**
   ```bash
   # Fix upload directory permissions
   sudo chown -R $(whoami):$(whoami) pan-sea-backend/uploads
   ```

5. **Dependency Installation Issues:**
   ```bash
   # Clear npm cache in frontend directory
   cd pan-sea-frontend
   npm cache clean --force
   
   # Remove node_modules and reinstall
   rm -rf node_modules
   npm install
   
   # Rebuild Docker image
   docker-compose build --no-cache frontend
   ```

### Logs and Debugging

```bash
# View real-time logs
docker-compose logs -f

# Enter container for debugging
docker-compose exec backend bash
docker-compose exec frontend sh

# Check container status
docker-compose ps

# View resource usage
docker stats
```

## Production Deployment

For production deployment, consider:

1. **Use environment-specific configurations:**
   ```bash
   # Create production docker-compose file
   cp docker-compose.yml docker-compose.prod.yml
   ```

2. **Enable SSL/TLS:**
   - Add reverse proxy (nginx/traefik)
   - Configure SSL certificates
   - Update CORS settings

3. **Database setup:**
   - Use external database service
   - Configure database migrations
   - Set up database backups

4. **Monitoring:**
   - Add health checks
   - Configure logging
   - Set up monitoring tools

## Development

### Development Mode with Hot Reloading

For development with hot reloading and file watching:

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Or start specific services
docker-compose -f docker-compose.dev.yml up backend-dev
docker-compose -f docker-compose.dev.yml up frontend-dev
```

Development features:
- Hot reloading for both frontend and backend
- Volume mounting for live code changes
- Development dependencies included
- Detailed logging enabled

### Local Development with Docker

```bash
# Start only backend for frontend development
docker-compose up backend

# Start only database services if available
docker-compose up database redis

# Hybrid development (backend in Docker, frontend local)
docker-compose up backend
cd pan-sea-frontend && npm run dev
```

### Fixing Frontend Build Issues

If you encounter the `@google/generative-ai` module not found error:

```bash
# 1. Stop all containers
docker-compose down

# 2. Clean up frontend dependencies
cd pan-sea-frontend
rm -rf node_modules package-lock.json
npm install

# 3. Rebuild the frontend image
docker-compose build --no-cache frontend

# 4. Start services
docker-compose up
```

### Updating Dependencies

```bash
# Backend: Update requirements.txt and rebuild
docker-compose build backend

# Frontend: Update package.json and rebuild
cd pan-sea-frontend
npm install
docker-compose build frontend
```

## Security Considerations

- Never commit `.env` files
- Use Docker secrets for sensitive data in production
- Regularly update base images
- Scan images for vulnerabilities
- Use non-root users in containers where possible

## Support

For issues and questions:
1. Check the logs: `docker-compose logs`
2. Verify environment variables are set correctly
3. Ensure all required ports are available
4. Check Docker and Docker Compose versions
