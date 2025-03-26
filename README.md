# FitGPT

A workout search engine built with React, Flask, and Elasticsearch. Generate personalized workout plans based on your fitness level, goals, and available equipment.

## Setup Instructions

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/downloads)

### Required API Keys

Before running the application, you'll need to obtain the following API keys:

1. **Mistral AI API Key** - Used for workout customization and AI coach tips
   - Sign up at [https://mistral.ai/](https://mistral.ai/)
   - Create an API key in your account dashboard

2. **Firebase Project** - Used for authentication and user data storage
   - Use your existing Firebase project OR create a new one on [Firebase Console](https://console.firebase.google.com/)
   - Ensure Authentication is set up (enable Email/Password and Google Sign-In)
   - Generate a service account key (Project Settings → Service Accounts → Generate new private key)

### Environment Setup

The application requires environment variables in both frontend and backend directories:

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd FitGPT
   ```

2. **Backend Environment Setup** (.env file in the `backend` directory):
   ```
   # Required - Your Mistral API key
   MISTRAL_API_KEY=your_mistral_api_key

   # Required - Elasticsearch configuration (don't change this)
   ELASTICSEARCH_URL=http://elasticsearch:9200

   # Required - Flask secret key (for session management)
   # Generate with: python -c "import secrets; print(secrets.token_hex(16))"
   FLASK_SECRET_KEY=generate_a_random_key_here

   # Required for Google OAuth (if using)
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret

   # Required for reCAPTCHA (if using)
   RECAPTCHA_SECRET_KEY=your_recaptcha_secret_key

   # Firebase Configuration (copy values from your service account JSON file)
   FIREBASE_TYPE=service_account
   FIREBASE_PROJECT_ID=your_project_id
   FIREBASE_PRIVATE_KEY_ID=your_private_key_id
   FIREBASE_PRIVATE_KEY="your_private_key_with_newlines_preserved"
   FIREBASE_CLIENT_EMAIL=your_client_email
   FIREBASE_CLIENT_ID=your_client_id
   FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
   FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
   FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
   FIREBASE_CLIENT_X509_CERT_URL=your_cert_url
   FIREBASE_UNIVERSE_DOMAIN=googleapis.com
   ```

3. **Frontend Environment Setup** (.env file in the `frontend` directory):
   ```
   # Required for Google OAuth
   REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id
   REACT_APP_RECAPTCHA_SITE_KEY=your_recaptcha_site_key

   # Firebase Configuration (from Firebase console → Project settings → Web app)
   REACT_APP_FIREBASE_API_KEY=your_firebase_api_key
   REACT_APP_FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
   REACT_APP_FIREBASE_PROJECT_ID=your_project_id
   REACT_APP_FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
   REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   REACT_APP_FIREBASE_APP_ID=your_app_id
   ```

4. **Firebase Service Account Key**:
   - Save your Firebase service account key JSON file as `backend/firebase-service-account-key.json`
   - Ensure the path and filename match what's referenced in your backend code
   - The default expected format is: `backend/fitgpt-XXXX-firebase-adminsdk-XXXX-XXXXXXXX.json`
   - If you use a different filename, update the reference in `backend/app.py`

### Running the Application

1. Start all services with Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. The services will be available at:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5001
   - Elasticsearch: http://localhost:9200