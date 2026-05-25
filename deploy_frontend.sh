#!/bin/bash
# =============================================================================
# CARD SCOUT: GOOGLE CLOUD RUN FRONTEND UI DEPLOYMENT
# =============================================================================
# This script deploys your React Nginx frontend dashboard to Google Cloud Run
# by swapping the Dockerfile temporarily and triggering a Cloud Build submit.

set -e

PROJECT_ID="simon-main"
SERVICE_NAME="card-scout-ui"
REGION="us-east1"

echo "🚀 CARD SCOUT: Initializing Google Cloud Run Frontend UI Deployment..."
echo "📍 Target GCP Project: $PROJECT_ID"
echo "📍 Region: $REGION"

# 1. Back up backend Dockerfile
echo "📦 Backing up backend Dockerfile..."
cp Dockerfile Dockerfile.backend

# 2. Swap to frontend Dockerfile
echo "📦 Swapping to frontend Dockerfile..."
cp Dockerfile.frontend Dockerfile

# 3. Deploy to Google Cloud Run using Cloud Build source compile
echo "☁️ Deploying Frontend UI container service to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --project=$PROJECT_ID

# 4. Restore original backend Dockerfile
echo "📦 Restoring original backend Dockerfile..."
cp Dockerfile.backend Dockerfile
rm Dockerfile.backend

echo "============================================================================="
echo "🎉 SUCCESS: Card Scout Frontend UI successfully deployed to Google Cloud Run!"
echo "============================================================================="
