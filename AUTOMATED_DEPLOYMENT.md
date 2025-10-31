# Automated Deployment Setup Guide

This guide will help you set up automated deployments to Google Cloud Run using GitHub Actions.

## 🎯 What This Does

Every time you push to the `main` or `master` branch, GitHub Actions will automatically:
1. Build your Docker container
2. Deploy to Cloud Run
3. Update the live service

## 📋 One-Time Setup Steps

### Step 1: Create a Service Account for GitHub Actions

```bash
# Set your project ID
export PROJECT_ID=mai-medical

# Create service account
gcloud iam service-accounts create github-actions-deployer \
  --display-name="GitHub Actions Deployer" \
  --project=$PROJECT_ID

# Get the service account email
export SA_EMAIL=github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com
```

### Step 2: Grant Required Permissions

```bash
# Cloud Run Admin (to deploy services)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

# Service Account User (to deploy as service account)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

# Storage Admin (for Cloud Build)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

# Cloud Build Editor (to build containers)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudbuild.builds.editor"

# Artifact Registry Writer (to push images)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer"
```

### Step 3: Create and Download Service Account Key

```bash
# Create key file
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=$SA_EMAIL \
  --project=$PROJECT_ID

# Display the key (you'll copy this)
cat github-actions-key.json

# IMPORTANT: Delete the local file after copying
rm github-actions-key.json
```

### Step 4: Add Secret to GitHub

1. Go to your GitHub repository: https://github.com/xxxrokxxx/iso-medical-docs-api

2. Click **Settings** → **Secrets and variables** → **Actions**

3. Click **New repository secret**

4. Create secret:
   - **Name**: `GCP_SA_KEY`
   - **Value**: Paste the entire JSON content from the previous step
   
5. Click **Add secret**

---

## 🚀 Quick Setup Script

Run this all at once:

```bash
# Set variables
export PROJECT_ID=mai-medical
export SA_NAME=github-actions-deployer

# Create service account
gcloud iam service-accounts create $SA_NAME \
  --display-name="GitHub Actions Deployer" \
  --project=$PROJECT_ID

# Get service account email
export SA_EMAIL=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

# Grant all required roles
for role in roles/run.admin roles/iam.serviceAccountUser roles/storage.admin roles/cloudbuild.builds.editor roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$role"
done

# Create and display key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=$SA_EMAIL \
  --project=$PROJECT_ID

echo ""
echo "=========================================="
echo "📋 COPY THE JSON BELOW TO GITHUB SECRETS"
echo "=========================================="
echo ""
cat github-actions-key.json
echo ""
echo "=========================================="
echo "⚠️  Add this as GCP_SA_KEY secret in GitHub"
echo "🔗 https://github.com/xxxrokxxx/iso-medical-docs-api/settings/secrets/actions"
echo "=========================================="

# Clean up local file
read -p "Press Enter after you've copied the JSON to delete the local file..."
rm github-actions-key.json
echo "✅ Local key file deleted for security"
```

---

## ✅ Testing the Automation

Once setup is complete:

```bash
# Make a small change
cd /Users/rok/Razvoj25/iso-medical-docs-api
echo "# Test deployment" >> README.md

# Commit and push
git add .
git commit -m "Test automated deployment"
git push origin master

# Watch the deployment
# Go to: https://github.com/xxxrokxxx/iso-medical-docs-api/actions
```

---

## 🔍 Monitoring Deployments

### GitHub Actions Dashboard
https://github.com/xxxrokxxx/iso-medical-docs-api/actions

### Cloud Run Console
https://console.cloud.google.com/run/detail/europe-north1/iso-docs-api

### View Logs
```bash
gcloud run services logs read iso-docs-api \
  --region europe-north1 \
  --project mai-medical
```

---

## 🎮 Manual Deployment Trigger

You can also trigger deployments manually from GitHub:

1. Go to **Actions** tab
2. Select "Deploy to Cloud Run" workflow
3. Click **Run workflow**
4. Select branch and click **Run workflow**

---

## 🔐 Security Best Practices

✅ **Service account has minimal required permissions**
✅ **Key is stored as GitHub encrypted secret**
✅ **Key never committed to repository**
✅ **Local key file deleted after setup**

### Rotating the Key (Recommended annually)

```bash
# List existing keys
gcloud iam service-accounts keys list \
  --iam-account=github-actions-deployer@mai-medical.iam.gserviceaccount.com

# Delete old key
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=github-actions-deployer@mai-medical.iam.gserviceaccount.com

# Create new key (repeat Step 3 above)
```

---

## 🚨 Troubleshooting

### "Permission denied" errors
- Check service account has all required roles
- Verify GCP_SA_KEY secret is set correctly in GitHub

### "Secret not found" errors in Cloud Run
- Ensure secrets exist in Secret Manager
- Check service account has `secretmanager.secretAccessor` role

### Build failures
- Check Cloud Build API is enabled
- Verify Artifact Registry API is enabled
- Check quota limits in GCP

---

## 📊 Deployment Flow

```
Push to GitHub (master branch)
    ↓
GitHub Actions triggered
    ↓
Authenticate with GCP (using GCP_SA_KEY)
    ↓
Build Docker image (Cloud Build)
    ↓
Push to Artifact Registry
    ↓
Deploy to Cloud Run
    ↓
Live at: https://iso-docs-api-682759779184.europe-north1.run.app
```

---

## 🎉 Benefits

✅ **Zero manual deployment** - Push to deploy
✅ **Version control** - Every deployment tracked in git
✅ **Rollback easy** - Revert git commit to rollback
✅ **Consistent** - Same process every time
✅ **Fast** - Typically 2-4 minutes
✅ **Visible** - See deployment status in GitHub

---

## 📝 Next Steps After Setup

1. ✅ Run the quick setup script
2. ✅ Add GCP_SA_KEY to GitHub secrets
3. ✅ Push a test commit
4. ✅ Watch it deploy automatically
5. ✅ Celebrate! 🎉
