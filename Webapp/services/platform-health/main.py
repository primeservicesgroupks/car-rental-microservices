from fastapi import FastAPI

# Create the FastAPI application object.
# Uvicorn loads this object and exposes it over HTTP.
app = FastAPI(
    title="Car Rental Platform Health Service",
    description="Project 1 development environment test.",
    version="1.0.0",
)

# GET / proves the API itself is responding.
@app.get("/")
def root():
    return {
        "application": "car-rental-microservices",
        "message": "Car Rental Platform API is running",
    }

# GET /health proves the service is alive and responding.
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "platform-health",
    }
