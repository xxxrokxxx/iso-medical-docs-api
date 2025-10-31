# ISO Medical Device Documents Query System

AI-powered chatbot for querying ISO standards and medical device regulations using RAG (Retrieval Augmented Generation).

## 🏗️ Architecture

- **Backend**: FastAPI with Weaviate vector database
- **Frontend**: Gradio chatbot interface
- **Embeddings**: OpenAI text-embedding-3-large
- **LLM**: GPT-4o for answer generation
- **Documents**: 7 ISO standards (4,033 chunks indexed)

## 📋 Available Documents

- ISO 13485:2016 - Quality Management Systems
- ISO 14971:2019 - Risk Management
- ISO 14155:2020 - Clinical Investigation
- ISO 62304:2006 - Medical Device Software
- ISO 15223-1:2021 - Symbols for Medical Devices
- EU MDR 2017/745 - Medical Device Regulation
- MDCG 2020-3 - Clinical Evaluation Guidelines

## 🚀 Local Development

### Prerequisites

- Python 3.13+
- Weaviate Cloud account (or local Weaviate instance)
- OpenAI API key
- VoyageAI API key (optional)

### Setup

1. **Clone and navigate to the ISO directory**:
   ```bash
   cd /path/to/mai_tools3/ISO
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (create `.env` file):
   ```env
   OPENAI_API_KEY=your_openai_api_key
   WEAVIATE_URL=your_weaviate_cloud_url
   WEAVIATE_API_KEY=your_weaviate_api_key
   VOYAGEAI_APIKEY=your_voyage_api_key  # Optional
   PORT=8080
   GRADIO_PORT=7860
   ```

5. **Create the Weaviate collection** (first time only):
   ```bash
   python create_iso_collection.py
   ```
   This will:
   - Convert all PDFs in the `docs/` folder using Docling
   - Perform hierarchical chunking
   - Create the `ISODocuments` collection in Weaviate
   - Insert ~4,033 document chunks with embeddings

### Running the Application

#### Option 1: Run services separately

**Terminal 1 - Start FastAPI backend**:
```bash
python main_api.py
```
Backend will run on: http://localhost:8080

**Terminal 2 - Start Gradio frontend**:
```bash
python gradio_app.py
```
Frontend will run on: http://localhost:7860

#### Option 2: Run with startup script

```bash
chmod +x start.sh
./start.sh
```

### API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /search` - Semantic search
  ```json
  {
    "query": "software validation",
    "limit": 5
  }
  ```
- `POST /ask` - RAG question answering
  ```json
  {
    "question": "What are the requirements for risk management?",
    "limit": 3
  }
  ```

## 🐳 Docker Deployment

### Build Docker image

```bash
docker build -t iso-docs-api .
```

### Run Docker container

```bash
docker run -p 8080:8080 -p 7860:7860 --env-file .env iso-docs-api
```

Access:
- API: http://localhost:8080
- Gradio UI: http://localhost:7860

## ☁️ Google Cloud Run Deployment

### Prerequisites

- Google Cloud SDK installed (`gcloud`)
- Authenticated: `gcloud auth login`
- Project set: `gcloud config set project YOUR_PROJECT_ID`

### Deployment Steps

1. **Enable required APIs**:
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   ```

2. **Create secrets for sensitive data**:
   ```bash
   # Create secrets
   echo -n "your_openai_key" | gcloud secrets create openai-api-key --data-file=-
   echo -n "your_weaviate_url" | gcloud secrets create weaviate-url --data-file=-
   echo -n "your_weaviate_key" | gcloud secrets create weaviate-api-key --data-file=-
   echo -n "your_voyage_key" | gcloud secrets create voyageai-api-key --data-file=-
   ```

3. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy iso-docs-api \
     --source . \
     --region europe-west1 \
     --platform managed \
     --allow-unauthenticated \
     --port 7860 \
     --memory 2Gi \
     --cpu 2 \
     --timeout 300 \
     --set-secrets="OPENAI_API_KEY=openai-api-key:latest,WEAVIATE_URL=weaviate-url:latest,WEAVIATE_API_KEY=weaviate-api-key:latest,VOYAGEAI_APIKEY=voyageai-api-key:latest" \
     --set-env-vars="PORT=8080,GRADIO_PORT=7860,API_URL=http://localhost:8080"
   ```

4. **Get the service URL**:
   ```bash
   gcloud run services describe iso-docs-api --region europe-west1 --format='value(status.url)'
   ```

### Important Notes for Cloud Run

- **Port Configuration**: Cloud Run expects the application to listen on the port specified by the `PORT` environment variable (default 8080). We expose Gradio on 7860 internally but Cloud Run routes traffic to the main port.
  
- **Memory & CPU**: Recommended 2Gi memory and 2 CPU for handling both services and LLM requests.

- **Timeout**: Set to 300 seconds (5 minutes) to handle longer RAG queries.

- **Cold Start**: First request may take 10-15 seconds. Consider using min-instances to avoid cold starts:
  ```bash
  gcloud run services update iso-docs-api \
    --region europe-west1 \
    --min-instances 1
  ```

### Alternative: Separate Services

For production, consider deploying as two separate Cloud Run services:

**Backend service**:
```bash
gcloud run deploy iso-docs-api-backend \
  --source . \
  --region europe-west1 \
  --port 8080 \
  --set-secrets="..." \
  --allow-unauthenticated
```

**Frontend service**:
```bash
gcloud run deploy iso-docs-api-frontend \
  --source . \
  --region europe-west1 \
  --port 7860 \
  --set-env-vars="API_URL=https://iso-docs-api-backend-xxx.run.app" \
  --allow-unauthenticated
```

## 🧪 Testing

### Test API locally

```bash
# Health check
curl http://localhost:8080/health

# Search
curl -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{"query": "risk management", "limit": 3}'

# Ask question
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is ISO 14971?", "limit": 3}'
```

### Test Gradio UI

Open browser: http://localhost:7860

## 📊 Performance

- **Indexing**: ~3.5 minutes for 7 PDFs (using MPS GPU on Mac)
- **Query latency**: 2-5 seconds for RAG responses
- **Embedding generation**: Automatic on insertion
- **Collection size**: 4,033 chunks

## 🔧 Troubleshooting

### Weaviate connection issues
- Verify `WEAVIATE_URL` and `WEAVIATE_API_KEY` in `.env`
- Check Weaviate Cloud instance is running
- Ensure collection `ISODocuments` exists

### OpenAI API errors
- Verify `OPENAI_API_KEY` is valid
- Check API quota and limits
- Monitor rate limits

### Gradio not connecting to API
- Ensure `API_URL` environment variable is set correctly
- Check both services are running
- Verify ports are not blocked

### Cloud Run deployment issues
- Check secrets are created: `gcloud secrets list`
- Verify service has permission to access secrets
- Check logs: `gcloud run logs read iso-docs-api --region europe-west1`

## 📝 License

Internal use only - ISO standards are copyrighted material.

## 🤝 Contributing

This is an internal tool for medical device regulatory compliance research.
