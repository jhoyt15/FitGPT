# FitGPT

A workout search engine built with React, Flask, and Elasticsearch.

## Prerequisites

Before running this project, make sure you have the following installed:
- Docker Desktop: [Get Docker](https://docs.docker.com/get-started/get-docker/)
- Git (for cloning the repository)

## Project Structure
├── backend/
│ ├── app.py # Flask application
│ ├── data/ # Data loading scripts and workout data
│ ├── Dockerfile
│ └── requirements.txt # Python dependencies
├── frontend/
│ ├── src/ # React components and logic
│ ├── public/
│ ├── Dockerfile
│ └── package.json # Node.js dependencies
└── docker-compose.yml # Docker configuration


## Getting Started

1. Clone the repository:
```bash
git clone https://github.com/your-username/fitgpt.git
```

2. Navigate to the project directory:
```bash
cd fitgpt
```

3. Build and start the containers:
```bash
docker-compose up --build
```

4. Access the application:
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:5001](http://localhost:5001)
- Elasticsearch: http://localhost:9200


### Stopping the Application
To stop all containers:
```bash
docker-compose down
```
