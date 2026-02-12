# Hugging Face Spaces Deployment Guide

This guide explains how to deploy the Todo Application backend on Hugging Face Spaces.

## Prerequisites

- Hugging Face account
- Hugging Face Space created (Docker-based)
- Required environment variables configured

## Required Environment Variables

Set these in your Hugging Face Space's **Settings → Repository secrets**:

### Essential Variables
- **`DATABASE_URL`**: PostgreSQL connection string (Neon)
  ```
  postgresql://user:password@host/database
  ```
- **`OPENAI_API_KEY`**: Your OpenAI API key for the chatbot
- **`BETTER_AUTH_SECRET`**: JWT secret (minimum 32 characters)
  ```
  # Generate with: openssl rand -hex 32
  ```

### Optional Variables
- **`HOST`**: Bind address (default: `0.0.0.0`)
- **`PORT`**: Port number (default: `7860` - do not change for HF Spaces)
- **`DEBUG`**: Enable debug mode (default: `false`)
- **`MCP_HOST`**: MCP server host (default: `localhost`)
- **`MCP_PORT`**: MCP server port (default: `8001`)
- **`MCP_DEBUG`**: Enable MCP debug mode (default: `false`)

## Deployment Steps

### 1. Create a Hugging Face Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **Create new Space**
3. Fill in the details:
   - **Space name**: `todo-app-backend`
   - **Space type**: Select **Docker**
   - **Visibility**: Choose Public or Private
4. Click **Create space**

### 2. Configure Your Repository

1. Clone your space repository locally:
   ```bash
   git clone https://huggingface.co/spaces/{username}/todo-app-backend
   cd todo-app-backend
   ```

2. Copy your backend files:
   ```bash
   cp -r /path/to/your/backend/* .
   ```

3. Ensure the directory structure looks like:
   ```
   .
   ├── Dockerfile
   ├── requirements.txt
   ├── src/
   │   ├── main.py
   │   ├── models/
   │   ├── api/
   │   ├── services/
   │   ├── core/
   │   └── middleware/
   └── README.md
   ```

### 3. Set Environment Variables

1. Go to your Space's **Settings**
2. Click **Repository secrets**
3. Add each required environment variable:
   - `DATABASE_URL`
   - `OPENAI_API_KEY`
   - `BETTER_AUTH_SECRET`

### 4. Push to Hugging Face

```bash
git add .
git commit -m "Deploy to Hugging Face Spaces"
git push
```

The space will automatically build the Docker image and start the container.

### 5. Access Your API

Once deployment is complete, your backend will be available at:
```
https://{username}-todo-app-backend.hf.space
```

### API Endpoints

- **Health Check**: `GET /health`
- **API Docs**: `GET /docs` (Swagger UI)
- **Tasks**: `GET/POST /api/tasks`
- **Chat**: `POST /api/chat/message`
- **MCP**: `GET /api/mcp/resources`

## CORS Configuration

The backend is pre-configured to accept requests from:
- `http://localhost:3000` (local development)
- `http://127.0.0.1:3000` (local development)
- `https://my-todo-app-jet-pi.vercel.app` (production frontend)

To add more origins, update `src/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-frontend-domain.com",
        "https://{username}-todo-app-backend.hf.space",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Monitoring

### View Logs

Go to your Space and click the **Logs** tab to view:
- Build logs
- Runtime logs
- Error messages

### Health Checks

The Docker container includes a health check that:
- Runs every 30 seconds
- Waits 40 seconds before first check
- Times out after 10 seconds
- Fails after 3 consecutive failures

Monitor health status in the Space's Settings.

## Troubleshooting

### Container fails to start

**Issue**: "Error: BETTER_AUTH_SECRET environment variable is required"

**Solution**: Ensure all required environment variables are set in Repository secrets.

### Database connection errors

**Issue**: "ERROR: could not translate host name \"...\" to address"

**Solution**: Verify `DATABASE_URL` is correct and the database is accessible from HF Spaces.

### 502 Bad Gateway

**Issue**: Space returns 502 error

**Solution**:
1. Check the **Logs** tab for error messages
2. Verify all environment variables are set
3. Ensure the Docker build completed successfully

### API endpoints return 404

**Issue**: Routes not found

**Solution**: Make sure the Dockerfile copied `src/` directory. Check the build logs.

## Database Setup

If using Neon PostgreSQL:

1. Create a Neon project at [console.neon.tech](https://console.neon.tech)
2. Copy the connection string
3. Set as `DATABASE_URL` secret
4. The app will automatically initialize tables on first run

## Performance Notes

- The Dockerfile uses `--workers 1` to run a single Uvicorn worker (HF Spaces limitation)
- For production with higher traffic, consider upgrading your Space to a **GPU** or **CPU Upgrade** tier
- The health check helps HF Spaces detect and restart failed containers

## Updating the Deployment

To update your backend:

```bash
cd /path/to/hf-space
git pull  # Sync with HF
# Make your changes
git add .
git commit -m "Update backend"
git push
```

The Space will automatically rebuild and redeploy.

## Security Notes

- Never commit `.env` files to the repository
- Use HF Spaces' Repository secrets for all sensitive data
- The API requires JWT tokens from Better Auth for task operations
- Frontend must be served over HTTPS in production

## Support

For issues:
- Check [HF Spaces documentation](https://huggingface.co/docs/hub/spaces)
- Review application logs in the Space's **Logs** tab
- Verify all environment variables are set correctly
