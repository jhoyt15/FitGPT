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

1. Create a `.env` file in the `backend/` directory with the following variables:
```env
# Required - Your Mistral API key (get from https://mistral.ai)
MISTRAL_API_KEY=your_mistral_api_key_here

# Required - Elasticsearch configuration
ELASTICSEARCH_URL=http://elasticsearch:9200

# Required - Flask secret key (generate using command below)
FLASK_SECRET_KEY=your_generated_secret_key

# Required for Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

2. Create a `.env` file in the `frontend/` directory:
```env
# Required for Google OAuth (same client ID as backend)
REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id_here
```

3. Generate a Flask secret key using Python:
```bash
python3 -c "import secrets; print(secrets.token_hex(16))"
```

4. Get your API keys:
   - Mistral API key: Sign up at [Mistral AI](https://mistral.ai)
   - Google OAuth credentials: 
     1. Go to [Google Cloud Console](https://console.cloud.google.com)
     2. Create a new project or select existing one
     3. Enable Google OAuth API
     4. Create OAuth 2.0 credentials
     5. Add authorized origins:
        - http://localhost:3000
        - http://localhost:5000
     6. Add authorized redirect URIs:
        - http://localhost:3000/
        - http://localhost:3000/login
        - http://localhost:3000/callback

⚠️ IMPORTANT:
- Never commit your `.env` files to version control
- Keep your API keys and secrets secure
- Each team member needs their own Mistral API key
- Team members can share the same Google OAuth credentials

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

4. **Environment Variables Issues:**
- Check that both `.env` files exist in their correct locations
- Verify Mistral API key is valid
- Ensure Google OAuth credentials are properly configured
- No spaces around `=` signs in `.env` files

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