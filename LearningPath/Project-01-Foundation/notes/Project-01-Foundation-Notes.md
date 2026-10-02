# Project 01 - Architecture & Local Development Foundation

## Project purpose
Project 1 creates the clean local foundation for the car-rental microservices platform before building the real business microservices. The learning material is kept separate from the actual application code.

## What Project 1 teaches
- Difference between a monolithic backend and a microservices architecture.
- How to divide a system into clear service responsibilities.
- Basic HTTP request/response flow.
- Git repository organization and repository protection with `.gitignore`.
- Python virtual environments and dependency isolation.
- FastAPI endpoints and automatic OpenAPI/Swagger documentation.
- Uvicorn as the local ASGI server.
- Health endpoints and why they are useful.
- Basic API testing with a browser, Swagger UI, and `curl`.
- Creating a clean Git checkpoint before starting the next project.

## Repository mental model

```text
car-rental-microservices/
├── README.md
├── .gitignore
├── Images/
├── LearningPath/
│   └── Project-01-Foundation/
│       ├── README.md
│       ├── labs/
│       ├── notes/
│       └── slides/
└── Webapp/
    ├── frontend/
    ├── services/
    ├── infrastructure/
    ├── docker/
    ├── scripts/
    ├── docs/
    └── tests/
```

### Why the main folders exist
- `LearningPath/` - training material organized project by project.
- `LearningPath/Project-01-Foundation/slides/` - Project 1 presentation.
- `LearningPath/Project-01-Foundation/notes/` - explanations and study notes.
- `LearningPath/Project-01-Foundation/labs/` - hands-on exercises and experiments.
- `Webapp/` - the real application that grows throughout the learning series.
- `Webapp/frontend/` - future Next.js/React/TypeScript frontend.
- `Webapp/services/` - backend microservices.
- `Webapp/infrastructure/` - future Terraform, Kubernetes, and cloud infrastructure.
- `Images/` - architecture diagrams and reusable project images.

## Target architecture
The long-term application is a Turo-style car-rental platform. The target architecture includes a frontend, API layer, independent business microservices, and supporting data/event services.

Planned core services:
- User Service
- Vehicle Service
- Search Service
- Booking Service
- Payment Service
- Notification Service

Later projects introduce technologies such as PostgreSQL, Redis, S3, SQS/EventBridge, Docker, Kubernetes, AWS, Terraform, GitHub Actions, and observability tooling.

## Development tools
Project 1 focuses primarily on Git, Python, and VS Code. Other tools are checked because they will be used later.

```powershell
git --version
python --version
pip --version
docker --version
aws --version
terraform --version
kubectl version --client
```

Python 3.11+ is preferred for the learning project.

## Confirm the Git repository
From the existing repository:

```powershell
cd C:\Users\biome\Documents\PrimeServicesGroupKC\car-rental-microservices
git rev-parse --show-toplevel
git status
code .
```

Important: the Git repository already exists at `car-rental-microservices/`. Do not run `git init` again inside `LearningPath` or an individual project folder.

## Protect the repository with .gitignore
The root `.gitignore` prevents generated files, secrets, virtual environments, and other unnecessary files from being committed.

```gitignore
# Python
__pycache__/
*.py[cod]

# Virtual environments
.venv/
venv/
env/

# Secrets / environment variables
.env
.env.*

# Microsoft Office temporary lock files
~$*

# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfvars

# Node / Next.js
node_modules/
.next/

# OS / logs
Thumbs.db
.DS_Store
*.log
```

### Key idea
Git should track source code and useful documentation, not local environments, generated caches, secrets, Terraform state, or temporary files.

## Architecture documentation
Project 1 introduces architecture documentation before the application becomes large.

Recommended documents:
- `LearningPath/Project-01-Foundation/README.md` - Project 1 objectives and progress.
- `Webapp/README.md` - actual application overview and technology stack.
- `Webapp/docs/architecture/architecture.md` - service responsibilities and boundaries.
- `Webapp/docs/architecture/ADR-001-microservices.md` - why microservices were chosen and their tradeoffs.

### ADR mental model
An Architecture Decision Record records an important engineering decision and, more importantly, why that decision was made.

## First working service - platform-health
Project 1 creates a small FastAPI service to prove the local development environment works.

```text
Webapp/
└── services/
    └── platform-health/
        ├── main.py
        └── requirements.txt
```

This is not one of the final business microservices. It is a simple environment validation service.

## Create a Python virtual environment
From the repository root:

```powershell
cd Webapp\services\platform-health
python -m venv .venv
```

Activate it:

```powershell
source .venv/Scripts/activate
```

Then install the required packages:

```powershell
python -m pip install --upgrade pip
pip install fastapi uvicorn
pip list
```

### Mental model
- Python = programming language.
- `.venv` = isolated Python environment for this service.
- FastAPI = framework used to create the API.
- Uvicorn = ASGI server that runs the FastAPI application.

## Build main.py

```python
from fastapi import FastAPI

# Create the FastAPI application object.
# Uvicorn loads this object and exposes it over HTTP.
app = FastAPI(
    title="Car Rental Platform Health Service",
    description="Project 1 development environment test.",
    version="1.0.0",
)

# GET / proves that the API itself is responding.
@app.get("/")
def root():
    return {
        "application": "car-rental-microservices",
        "message": "Car Rental Platform API is running",
    }

# GET /health proves that the service is alive and responding.
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "platform-health",
    }
```

## Start the API

```powershell
uvicorn main:app --reload
```

Meaning:
- `uvicorn` - starts the ASGI server.
- `main` - refers to `main.py`.
- `app` - refers to the FastAPI object named `app`.
- `--reload` - automatically restarts the development server when code changes.

Expected local address:

```text
http://127.0.0.1:8000
```

Keep the terminal running while testing.

## Test the API
Use three testing methods so you understand multiple ways to interact with an API.

### Browser
- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`

Expected `/health` result:

```json
{
  "status": "healthy",
  "service": "platform-health"
}
```

### Swagger UI
Open:

```text
http://127.0.0.1:8000/docs
```

Select `GET /health`, choose **Try it out**, then **Execute**. Expected status is `200 OK`.

### Command line

```powershell
curl.exe http://127.0.0.1:8000/health
```

## Save dependencies

```powershell
pip freeze > requirements.txt
```

`requirements.txt` records the Python packages needed to recreate the environment.

Stop the server with:

```text
CTRL + C
```

Leave the virtual environment with:

```powershell
deactivate
```

## Git checkpoint
Return to the repository root:

```powershell
cd ..\..\..
git rev-parse --show-toplevel
git status
```

Stage intentionally:

```powershell
git add LearningPath\Project-01-Foundation
git add Webapp
git add .gitignore README.md
git status
```

Create the checkpoint:

```powershell
git commit -m "Complete Project 01 - microservices foundation"
git branch -M main
```

## Verify Git before finishing

```powershell
git branch --show-current
git status --ignored
git check-ignore -v Webapp/services/platform-health/.venv/pyvenv.cfg
git diff --cached --name-only
git log --oneline --decorate -5
git status
```

The goal is to confirm that the virtual environment and generated Python files are ignored, the desired Project 1 files are committed, the commit exists on `main`, and the working tree is clean.

## Break/fix exercises
Use these exercises to understand the system instead of only following commands:

1. Visit `/wrong-url` and observe the HTTP 404 response.
2. Stop Uvicorn and try `/health`; observe the connection failure.
3. Restart Uvicorn and verify the API becomes available again.
4. Change the health status from `healthy` to `testing`, save the file, and observe `--reload` restart the server.
5. Run the request again from Swagger.
6. Call `/health` using `curl.exe`.
7. Run `git status` and explain every modified or untracked file shown.

## Project 1 completion checklist
- [ ] Git, Python, and VS Code work.
- [ ] `car-rental-microservices` is confirmed as the Git repository root.
- [ ] `LearningPath/Project-01-Foundation` contains slides, notes, and labs.
- [ ] `Webapp/` is separate from the learning material.
- [ ] `.gitignore` protects virtual environments, secrets, temporary Office files, and generated content.
- [ ] Architecture documentation and the ADR exist.
- [ ] The Python virtual environment activates successfully.
- [ ] FastAPI and Uvicorn install successfully.
- [ ] `/` returns HTTP 200.
- [ ] `/health` returns HTTP 200.
- [ ] `/docs` loads and can execute `GET /health`.
- [ ] `curl.exe` successfully calls the API.
- [ ] `requirements.txt` exists.
- [ ] Project 1 is committed successfully on `main`.

## Commands to remember

```powershell
source .venv/Scripts/activate
uvicorn main:app --reload
curl.exe http://127.0.0.1:8000/health
git status --ignored
git commit -m "Complete Project 01 - microservices foundation"
```

## Project 1 final mental model

```text
ORGANIZE
Git repository + LearningPath + Webapp + .gitignore
        |
        v
BUILD
Python virtual environment + FastAPI + platform-health
        |
        v
TEST
Uvicorn + browser + Swagger + curl
        |
        v
SAVE
requirements.txt + Git staging + commit on main
        |
        v
PROJECT 2
Build the first real business microservice: User Service
```

## What comes next
Project 2 builds the User Service. It introduces FastAPI routers, Pydantic request/response schemas, validation, REST endpoint design, and HTTP status codes. The service is built under `Webapp/services/user-service/`, while the training material remains under `LearningPath/Project-02-User-Service/`.
