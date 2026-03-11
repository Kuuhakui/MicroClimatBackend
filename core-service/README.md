# Core Service

Central business logic and system settings for the MicroClimat project.

## Responsibilities
- Central business logic and system settings.
- Management of ML model configurations and threshold values (setpoints).
- Caching of frequently used system data.
- Feature flags management.

## Setup

### Local Development
1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the service:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker
Build and run with:
```bash
docker build -t core-service .
docker run -p 8000:8000 core-service
```
