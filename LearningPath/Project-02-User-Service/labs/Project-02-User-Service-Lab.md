# Project 2 Lab --- Build and Test the User Microservice with FastAPI

## Project Goal

Build the first business microservice for the car-rental platform: the
**User Service**.

By the end of this lab, you will have a working REST API that can:

-   Check service health.
-   Create users.
-   List all users.
-   Retrieve one user by ID.
-   Update an existing user.
-   Reject duplicate email addresses.
-   Reject invalid request data.
-   Return meaningful HTTP status codes.
-   Be tested through Swagger and `curl`.

This project intentionally uses an **in-memory Python dictionary**
instead of a database. Project 3 replaces this temporary storage with
PostgreSQL.

------------------------------------------------------------------------

## 1. What You Are Building

``` text
Client / Swagger / curl
          |
          | HTTP + JSON
          v
      FastAPI
      main.py
          |
          v
  routers/users.py
      /        \
     v          v
schemas.py    store.py
Validation    Temporary data
```

### Final endpoints

  Method   Endpoint             Purpose                   Expected success
  -------- -------------------- ------------------------- ------------------
  GET      `/health`            Verify service is alive   200
  POST     `/users`             Create a user             201
  GET      `/users`             List all users            200
  GET      `/users/{user_id}`   Retrieve one user         200
  PUT      `/users/{user_id}`   Update one user           200

Expected error behavior:

  Situation                             Status
  ----------------------------------- --------
  User does not exist                      404
  Duplicate email                          409
  Request fails Pydantic validation        422

------------------------------------------------------------------------

## 2. Prerequisites

Project 1 should already have provided:

-   Git repository: `car-rental-microservices`
-   `Webapp/services/`
-   `LearningPath/`
-   Git/GitHub configuration
-   `.gitignore`
-   Python installed
-   VS Code
-   Git Bash or PowerShell

Work from:

``` text
car-rental-microservices/Webapp/services/user-service
```

------------------------------------------------------------------------

## 3. Create the User Service Structure

Create:

``` text
user-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   ├── store.py
│   └── routers/
│       ├── __init__.py
│       └── users.py
├── .venv/
└── requirements.txt
```

### Why separate these files?

-   `main.py` --- creates and configures the FastAPI application.
-   `schemas.py` --- defines request/response data contracts and
    validation.
-   `store.py` --- temporary in-memory data storage.
-   `routers/users.py` --- contains user-related HTTP routes.
-   `__init__.py` --- allows Python to treat folders as packages.

------------------------------------------------------------------------

## 4. Create and Activate the Virtual Environment

From `Webapp/services/user-service`:

``` bash
python -m venv .venv
```

Git Bash:

``` bash
source .venv/Scripts/activate
```

PowerShell:

``` powershell
.\.venv\Scripts\Activate.ps1
```

Verify:

``` bash
python --version
python -m pip --version
```

Your terminal should normally show `(.venv)`.

### Important

`.venv/` must remain excluded by `.gitignore`. Never commit the virtual
environment.

------------------------------------------------------------------------

## 5. Install Dependencies

``` bash
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn email-validator
```

Freeze the environment:

``` bash
pip freeze > requirements.txt
```

Verify FastAPI:

``` bash
python -c "import fastapi; print(fastapi.__version__)"
```

------------------------------------------------------------------------

## 6. Configure the VS Code Python Interpreter

If VS Code reports:

``` text
Import "fastapi" could not be resolved
```

select the project interpreter:

1.  Press `Ctrl + Shift + P`.
2.  Select **Python: Select Interpreter**.
3.  Choose or enter:

``` text
...\Webapp\services\user-service\.venv\Scripts\python.exe
```

4.  Reload VS Code if necessary.
5.  Check **Problems** with `Ctrl + Shift + M`.

------------------------------------------------------------------------

## 7. Build `schemas.py`

Use:

``` python
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    RENTER = "RENTER"
    OWNER = "OWNER"
    ADMIN = "ADMIN"


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    phone: str | None = None
    role: UserRole = UserRole.RENTER


class UserResponse(UserCreate):
    id: int


class UserUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    email: EmailStr | None = None
    phone: str | None = None
    role: UserRole | None = None
```

### Learning points

`UserCreate`, `UserResponse`, and `UserUpdate` are deliberately separate
because each operation has a different contract.

`UserCreate` describes what the client can send when creating a user.

`UserResponse` adds the server-generated `id`.

`UserUpdate` makes fields optional so a client can change only selected
values.

`EmailStr` performs email validation.

`UserRole` limits roles to:

``` text
RENTER
OWNER
ADMIN
```

------------------------------------------------------------------------

## 8. Build `store.py`

``` python
users_db: dict[int, dict] = {}

next_user_id = 1
```

### What this means

`users_db` behaves like a tiny temporary database:

``` python
{
    1: {
        "id": 1,
        "first_name": "Ade",
        ...
    }
}
```

`next_user_id` generates sequential IDs.

### Limitation

This data exists only in the Python process. Restarting the application
clears it.

That limitation is intentional and becomes the main problem solved in
Project 3.

------------------------------------------------------------------------

## 9. Build `routers/users.py`

``` python
from fastapi import APIRouter, HTTPException, status

from app import store
from app.schemas import UserCreate, UserResponse, UserUpdate


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: UserCreate):
    for existing_user in store.users_db.values():
        existing_email = str(existing_user["email"]).lower()
        requested_email = str(user.email).lower()

        if existing_email == requested_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

    user_id = store.next_user_id

    new_user = {
        "id": user_id,
        **user.model_dump(),
    }

    store.users_db[user_id] = new_user
    store.next_user_id += 1

    return new_user


@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
def list_users():
    return list(store.users_db.values())


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user(user_id: int):
    user = store.users_db.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def update_user(user_id: int, changes: UserUpdate):
    user = store.users_db.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = changes.model_dump(exclude_unset=True)

    if "email" in update_data:
        new_email = str(update_data["email"]).lower()

        for existing_id, existing_user in store.users_db.items():
            if existing_id == user_id:
                continue

            existing_email = str(existing_user["email"]).lower()

            if existing_email == new_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists",
                )

    user.update(update_data)
    store.users_db[user_id] = user

    return user
```

### Important learning point: `exclude_unset=True`

If the client sends:

``` json
{
  "phone": "9135559999"
}
```

then:

``` python
changes.model_dump(exclude_unset=True)
```

contains only the supplied field. Existing first name, last name, email,
and role remain unchanged.

------------------------------------------------------------------------

## 10. Build `main.py`

``` python
from fastapi import FastAPI

from app.routers.users import router as users_router


app = FastAPI(
    title="Car Rental User Service",
    description="Manages users for the car rental platform.",
    version="1.0.0",
)


app.include_router(users_router)


@app.get(
    "/health",
    tags=["Health"],
)
def health_check():
    return {
        "status": "healthy",
        "service": "user-service",
    }
```

------------------------------------------------------------------------

## 11. Compile Before Running

From the `user-service` directory:

``` bash
python -m py_compile app/schemas.py
python -m py_compile app/store.py
python -m py_compile app/routers/users.py
python -m py_compile app/main.py
```

No output means Python found no syntax errors.

Test imports:

``` bash
python -c "from app.schemas import UserCreate, UserResponse, UserUpdate; print('Schemas OK')"
python -c "from app.routers.users import router; print('Router OK')"
python -c "from app.main import app; print('FastAPI app loaded successfully')"
```

------------------------------------------------------------------------

## 12. Start the Service

``` bash
python -m uvicorn app.main:app --reload --port 8001
```

Expected server address:

``` text
http://127.0.0.1:8001
```

If `/` returns:

``` json
{"detail":"Not Found"}
```

that is expected because Project 2 does not define a root `/` endpoint.

Use:

``` text
http://127.0.0.1:8001/health
```

and:

``` text
http://127.0.0.1:8001/docs
```

------------------------------------------------------------------------

## 13. Swagger Test Lab

Open:

``` text
http://127.0.0.1:8001/docs
```

### Test 1 --- Health

Execute:

``` text
GET /health
```

Expected:

``` json
{
  "status": "healthy",
  "service": "user-service"
}
```

Status: `200`.

### Test 2 --- Create first user

Execute:

``` text
POST /users
```

Body:

``` json
{
  "first_name": "Ade",
  "last_name": "Adewunmi",
  "email": "ade@example.com",
  "phone": "9135551234",
  "role": "RENTER"
}
```

Expected: `201 Created`.

The response should contain server-generated:

``` json
"id": 1
```

### Test 3 --- Create second user

``` json
{
  "first_name": "Michelle",
  "last_name": "Johnson",
  "email": "michelle@example.com",
  "phone": "9135555678",
  "role": "OWNER"
}
```

Expected ID: `2`.

### Test 4 --- List users

``` text
GET /users
```

Expected: `200` and a JSON array containing both users.

### Test 5 --- Retrieve one user

``` text
GET /users/1
```

Expected: `200` and user 1.

### Test 6 --- Update user

``` text
PUT /users/1
```

Body:

``` json
{
  "phone": "9135559999"
}
```

Expected: `200`.

Verify with:

``` text
GET /users/1
```

Only the phone number should have changed.

------------------------------------------------------------------------

## 14. Validation and Error Lab

Good API testing includes intentional failures.

### Failure A --- Missing user

``` text
GET /users/999
```

Expected:

``` text
404 Not Found
```

``` json
{
  "detail": "User not found"
}
```

### Failure B --- Invalid email

``` json
{
  "first_name": "Test",
  "last_name": "User",
  "email": "not-an-email",
  "role": "RENTER"
}
```

Expected: `422`.

### Failure C --- Empty first name

``` json
{
  "first_name": "",
  "last_name": "User",
  "email": "test@example.com",
  "role": "RENTER"
}
```

Expected: `422`.

### Failure D --- Invalid role

``` json
{
  "first_name": "Test",
  "last_name": "User",
  "email": "test@example.com",
  "role": "SUPERUSER"
}
```

Expected: `422`.

### Failure E --- Missing required email

``` json
{
  "first_name": "Test",
  "last_name": "User"
}
```

Expected: `422`.

### Failure F --- Duplicate email

Attempt another POST with:

``` json
{
  "first_name": "Duplicate",
  "last_name": "User",
  "email": "ade@example.com",
  "role": "RENTER"
}
```

Expected:

``` text
409 Conflict
```

### Failure G --- Case-insensitive duplicate

Try:

``` text
ADE@EXAMPLE.COM
```

Expected: `409`.

### Failure H --- Update nonexistent user

``` text
PUT /users/999
```

Body:

``` json
{
  "first_name": "Nobody"
}
```

Expected: `404`.

------------------------------------------------------------------------

## 15. curl Test Lab

Keep Uvicorn running and open another Git Bash terminal.

### Health

``` bash
curl -i http://127.0.0.1:8001/health
```

### List users

``` bash
curl -i http://127.0.0.1:8001/users
```

### Create user

``` bash
curl -i -X POST \
  http://127.0.0.1:8001/users \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "9135552222",
    "role": "RENTER"
  }'
```

### Retrieve user 1

``` bash
curl -i http://127.0.0.1:8001/users/1
```

### Update user 1

``` bash
curl -i -X PUT \
  http://127.0.0.1:8001/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9135557777"
  }'
```

### Test missing user

``` bash
curl -i http://127.0.0.1:8001/users/999
```

### Test invalid email

``` bash
curl -i -X POST \
  http://127.0.0.1:8001/users \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Bad",
    "last_name": "Email",
    "email": "not-an-email",
    "role": "RENTER"
  }'
```

### Test duplicate email

``` bash
curl -i -X POST \
  http://127.0.0.1:8001/users \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Duplicate",
    "last_name": "User",
    "email": "ade@example.com",
    "role": "RENTER"
  }'
```

------------------------------------------------------------------------

## 16. Break/Fix Exercises

### Exercise 1 --- Wrong interpreter

**Symptom:** VS Code cannot resolve FastAPI even though installation
succeeded.

**Investigate:**

``` bash
which python
python -c "import fastapi; print(fastapi.__version__)"
```

**Lesson:** Package installation and editor interpreter selection must
point to the same Python environment.

### Exercise 2 --- Wrong Uvicorn module

Run intentionally:

``` bash
uvicorn main:app --reload --port 8001
```

from the `user-service` root.

If `main.py` is under `app/`, this is the wrong module path.

Correct:

``` bash
python -m uvicorn app.main:app --reload --port 8001
```

**Lesson:** `app.main:app` means package `app` → module `main` → FastAPI
object `app`.

### Exercise 3 --- Request `/`

Visit:

``` text
http://127.0.0.1:8001/
```

Observe `404`.

Then visit `/health`.

**Lesson:** A running server does not automatically mean every URL
exists.

### Exercise 4 --- Restart the service

Create users, stop Uvicorn with `Ctrl+C`, restart it, and execute:

``` text
GET /users
```

Expected:

``` json
[]
```

**Lesson:** In-memory storage is temporary.

### Exercise 5 --- Remove `exclude_unset=True`

Temporarily compare update behavior when using:

``` python
changes.model_dump()
```

versus:

``` python
changes.model_dump(exclude_unset=True)
```

Restore the correct implementation afterward.

**Lesson:** Update semantics matter; omitted fields should not
accidentally overwrite existing values.

------------------------------------------------------------------------

## 17. Git Checkpoint

Before committing:

``` bash
git status
```

Confirm `.venv/` does not appear as a file to commit.

From the repository root:

``` bash
git add Webapp/services/user-service
git status
git commit -m "Build Project 2 user service API"
git push
```

Verify the commit on GitHub.

------------------------------------------------------------------------

## 18. Completion Checklist

Project 2 is complete when all of these are true:

-   [ ] Virtual environment works.
-   [ ] FastAPI/Uvicorn dependencies are installed.
-   [ ] VS Code uses the `.venv` interpreter.
-   [ ] `schemas.py` defines `UserCreate`, `UserResponse`, and
    `UserUpdate`.
-   [ ] `store.py` contains temporary user storage.
-   [ ] `users.py` contains POST, GET list, GET one, and PUT.
-   [ ] `main.py` registers the router.
-   [ ] `/health` returns 200.
-   [ ] Swagger loads at `/docs`.
-   [ ] A valid user returns 201.
-   [ ] Users can be listed and retrieved.
-   [ ] A user can be partially updated.
-   [ ] Missing users return 404.
-   [ ] Duplicate emails return 409.
-   [ ] Invalid data returns 422.
-   [ ] curl tests succeed.
-   [ ] Restarting the app demonstrates that in-memory data is lost.
-   [ ] `.venv/` is not committed.
-   [ ] Project 2 code is committed and pushed.

------------------------------------------------------------------------

## 19. What Comes Next

Project 2 has a deliberate weakness:

``` text
FastAPI
   |
   v
Python dictionary
   |
   X
Lost when process restarts
```

Project 3 changes the persistence layer:

``` text
FastAPI
   |
   v
SQLAlchemy
   |
   v
PostgreSQL
   |
   v
Persistent user records
```

Project 3 introduces PostgreSQL, SQLAlchemy, database models, sessions,
connection configuration, and Alembic migrations while preserving the
API concepts learned here.
