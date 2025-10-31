#!/bin/bash
# Quick setup script for GitHub Actions automated deployment

set -e  # Exit on error

echo "🚀 Setting up automated deployment for ISO Medical Docs API"
echo ""

# Set variables
PROJECT_ID="mai-medical"
SA_NAME="github-actions-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Service Account: $SA_NAME"
echo ""

# Check if service account already exists
if gcloud iam service-accounts describe $SA_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo "✅ Service account already exists: $SA_EMAIL"
else
    echo "🔧 Creating service account..."
    gcloud iam service-accounts create $SA_NAME \
      --display-name="GitHub Actions Deployer" \
      --project=$PROJECT_ID
    echo "✅ Service account created"
fi

echo ""
echo "🔐 Granting required permissions..."

# Array of required roles
ROLES=(
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/storage.admin"
    "roles/cloudbuild.builds.editor"
    "roles/artifactregistry.writer"
    "roles/serviceusage.serviceUsageConsumer"
)

for role in "${ROLES[@]}"; do
    echo "   Adding $role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="$role" \
      --quiet &>/dev/null
done

echo "✅ All permissions granted"
echo ""

# Create key
KEY_FILE="github-actions-key.json"
echo "🔑 Creating service account key..."

if [ -f "$KEY_FILE" ]; then
    rm "$KEY_FILE"
fi

gcloud iam service-accounts keys create $KEY_FILE \
  --iam-account=$SA_EMAIL \
  --project=$PROJECT_ID

echo "✅ Key created"
echo ""
echo "=========================================="
echo "📋 COPY THE JSON BELOW TO GITHUB SECRETS"
echo "=========================================="
echo ""
cat $KEY_FILE
echo ""
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Copy the JSON above (entire content)"
echo "2. Go to: https://github.com/xxxrokxxx/iso-medical-docs-api/settings/secrets/actions"
echo "3. Click 'New repository secret'"
echo "4. Name: GCP_SA_KEY"
echo "5. Value: Paste the JSON"
echo "6. Click 'Add secret'"
echo ""
echo "=========================================="
echo ""

read -p "Press Enter after you've added the secret to GitHub..."

# Clean up
rm "$KEY_FILE"
echo ""
echo "✅ Local key file deleted for security"
echo ""
echo "🎉 Setup complete!"
echo ""
echo "Test it by making a change and pushing:"
echo "   cd /Users/rok/Razvoj25/iso-medical-docs-api"
echo "   echo '# Test' >> README.md"
echo "   git add README.md"
echo "   git commit -m 'Test automated deployment'"
echo "   git push origin master"
echo ""
echo "Then watch the deployment at:"
echo "   https://github.com/xxxrokxxx/iso-medical-docs-api/actions"
echo ""
