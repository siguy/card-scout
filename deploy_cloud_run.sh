#!/bin/bash
# =============================================================================
# CARD SCOUT: GOOGLE CLOUD RUN AUTOMATIC DEPLOYMENT
# =============================================================================
# This script automates building your container in the cloud using Google Cloud
# Build and deploying it to Cloud Run. It reads your private GEMINI_API_KEY
# directly from your local .env file!

set -e

PROJECT_ID="simon-main"
SERVICE_NAME="card-scout"
REGION="us-east1"

echo "🚀 CARD SCOUT: Initializing Google Cloud Run Deployment..."
echo "📍 Target GCP Project: $PROJECT_ID"
echo "📍 Region: $REGION"

# 1. Read API Key and eBay credentials from local .env file
if [ -f .env ]; then
    API_KEY=$(grep GEMINI_API_KEY .env | head -n 1 | cut -d '=' -f2 | tr -d '\r\n ')
    EBAY_CLIENT_ID=$(grep EBAY_CLIENT_ID .env | head -n 1 | cut -d '=' -f2 | tr -d '\r\n ')
    EBAY_CLIENT_SECRET=$(grep EBAY_CLIENT_SECRET .env | head -n 1 | cut -d '=' -f2 | tr -d '\r\n ')
    EBAY_RU_NAME=$(grep EBAY_RU_NAME .env | head -n 1 | cut -d '=' -f2 | tr -d '\r\n ')
    
    if [ "$API_KEY" = "PASTE_YOUR_GEMINI_API_KEY_HERE" ] || [ -z "$API_KEY" ]; then
        echo "❌ ERROR: Please paste your real GEMINI_API_KEY in your local .env file before deploying!"
        exit 1
    fi
else
    echo "❌ ERROR: Local .env file not found. Please create a .env file with your GEMINI_API_KEY."
    exit 1
fi

# 2. Enable Google Cloud Build & Cloud Run APIs
echo "⚙️ Step 1: Enabling Google APIs (Artifact Registry, Cloud Build, Cloud Run)..."
gcloud services enable \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    --project=$PROJECT_ID

# 3. Build container using Cloud Build (No local Docker engine required!)
echo "📦 Step 2: Compiling container via Google Cloud Build..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project=$PROJECT_ID

# 4. Deploy to Google Cloud Run
echo "☁️ Step 3: Deploying container service to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --project=$PROJECT_ID \
    --set-env-vars="GEMINI_API_KEY=$API_KEY,EBAY_CLIENT_ID=$EBAY_CLIENT_ID,EBAY_CLIENT_SECRET=$EBAY_CLIENT_SECRET,EBAY_RU_NAME=$EBAY_RU_NAME"

echo "============================================================================="
echo "🎉 SUCCESS: Card Scout Cloud Backend successfully deployed to Google Cloud Run!"
echo "============================================================================="
