# FitGPT

A workout search engine built with React, Flask, and Elasticsearch. Generate personalized workout plans based on your fitness level, goals, and available equipment.

## Prerequisites

Before running this project, make sure you have the following installed:
- Docker Desktop: [Get Docker](https://docs.docker.com/get-started/get-docker/)
- Git (for cloning the repository)
- Node.js 16+ and npm (for local development)

## Project Structure
```
├── backend/
│   ├── app.py                 # Flask application
│   ├── data/                  # Data loading scripts and workout data
│   │   └── exerciseData.json  # Exercise database
│   ├── Dockerfile            
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/                   # React components and logic
│   ├── public/
│   ├── Dockerfile
│   └── package.json          # Node.js dependencies
└── docker-compose.yml        # Docker configuration
```

## Environment Setup

1. Create a `.env` file in the root directory:
```
ELASTICSEARCH_URL=http://elasticsearch:9200
```

## Getting Started

1. Clone the repository:
```bash
git clone https://github.com/your-username/fitgpt.git
cd fitgpt
```

2. Install dependencies (for local development):
```bash
# Frontend dependencies
cd frontend
npm install
cd ..
```

3. Build and start the containers:
```bash
docker-compose up --build
```

4. Wait for the services to initialize:
- Elasticsearch needs about 30-60 seconds to start
- The backend will automatically load exercise data into Elasticsearch
- The frontend will be compiled and started

5. Access the application:
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:5001](http://localhost:5001)
- Elasticsearch: [http://localhost:9200](http://localhost:9200)

## Development

### Frontend Development
The frontend runs on React and includes:
- Form-based workout generation
- Real-time updates
- Responsive design
- Exercise search capabilities

### Backend Development
The backend uses:
- Flask for API endpoints
- Elasticsearch for exercise data storage
- Workout generation based on user input

## Troubleshooting

### Common Issues

1. **Elasticsearch fails to start:**
```bash
# Increase virtual memory for Elasticsearch
sudo sysctl -w vm.max_map_count=262144
```

2. **Frontend can't connect to backend:**
- Ensure all containers are running: `docker-compose ps`
- Check backend logs: `docker-compose logs flask-app`
- Verify the proxy setting in frontend/package.json

3. **Docker volume issues:**
```bash
# Remove all containers and volumes
docker-compose down -v
# Rebuild from scratch
docker-compose up --build
```

### Viewing Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs frontend
docker-compose logs flask-app
docker-compose logs elasticsearch
```

## Stopping the Application

1. Stop all containers:
```bash
docker-compose down
```

2. To also remove volumes (clean slate):
```bash
docker-compose down -v
```

## Local Development Setup

If you want to develop locally without Docker:

1. Start Elasticsearch using Docker:
```bash
docker-compose up elasticsearch
```

2. Start the backend:
```bash
cd backend
pip install -r requirements.txt
python -m flask run --port=5001
```

3. Start the frontend:
```bash
cd frontend
npm install
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend: http://localhost:5001
- Elasticsearch: http://localhost:9200

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request