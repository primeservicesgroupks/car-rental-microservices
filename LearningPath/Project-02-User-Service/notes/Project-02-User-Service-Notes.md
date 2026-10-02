# Project 2 Notes --- User Microservice with FastAPI

## One-Sentence Summary

Project 2 created the first business microservice for the car-rental
platform: a FastAPI User Service with validated REST endpoints,
temporary in-memory storage, meaningful HTTP status codes, Swagger
documentation, and command-line testing with curl.

------------------------------------------------------------------------

## Why This Project Exists

Project 1 established the repository, Git workflow, development
environment, and microservices foundation.

Project 2 moves from **project setup** to **actual application
behavior**.

The objective was not to build the entire platform at once. The
objective was to understand the API layer first:

``` text
Request
   ↓
Route
   ↓
Validation
   ↓
Business logic
   ↓
Storage
   ↓
Response
```

A database was deliberately postponed until Project 3.

------------------------------------------------------------------------

## Tools Used

### Python

Backend programming language.

### FastAPI

Framework used to create the REST API.

Benefits demonstrated in this project:

-   Route decorators.
-   Type hints.
-   Pydantic integration.
-   Automatic OpenAPI generation.
-   Swagger documentation.

### Uvicorn

ASGI server used to run FastAPI.

Project command:

``` bash
python -m uvicorn app.main:app --reload --port 8001
```

### Pydantic

Defines and validates API data contracts.

Models:

``` text
UserCreate
UserResponse
UserUpdate
```

### EmailStr / email-validator

Validates email input.

### Swagger / OpenAPI

Interactive API documentation at:

``` text
http://127.0.0.1:8001/docs
```

### curl

Command-line HTTP client used to test requests and responses directly.

### VS Code

Editor used for code, interpreter selection, and error checking.

### Python `.venv`

Keeps Project 2 Python packages isolated from global Python
installations.

### Git / GitHub

Tracks and stores source-code history.

------------------------------------------------------------------------

## Final File Responsibilities

### `app/main.py`

Application entry point.

Responsibilities:

-   Create `FastAPI()`.
-   Set title, description, and version.
-   Register `users_router`.
-   Provide `/health`.

### `app/schemas.py`

Defines API data contracts.

`UserCreate`:

-   Required first name.
-   Required last name.
-   Valid email.
-   Optional phone.
-   Default role of `RENTER`.

`UserResponse`:

-   Inherits user fields.
-   Adds server-generated `id`.

`UserUpdate`:

-   Makes fields optional.
-   Allows partial profile updates.

### `app/store.py`

Temporary persistence layer.

``` python
users_db: dict[int, dict] = {}
next_user_id = 1
```

This is intentionally temporary.

### `app/routers/users.py`

Contains user HTTP operations.

``` text
POST /users
GET  /users
GET  /users/{user_id}
PUT  /users/{user_id}
```

------------------------------------------------------------------------

## Important REST Concepts Learned

### POST

Used to create a new resource.

Project example:

``` text
POST /users
```

Successful creation returns:

``` text
201 Created
```

### GET

Used to retrieve resources without intentionally changing application
state.

Examples:

``` text
GET /users
GET /users/1
GET /health
```

### PUT

Used in this project to update an existing user.

``` text
PUT /users/1
```

The current implementation permits partial updates. A future API-design
discussion can compare this behavior with `PATCH`.

------------------------------------------------------------------------

## HTTP Status Codes Learned

### 200 OK

Successful GET or update.

### 201 Created

A user was successfully created.

### 404 Not Found

The requested user ID does not exist.

### 409 Conflict

A user already exists with the requested email address.

### 422 Unprocessable Entity

FastAPI/Pydantic understood the request format but the supplied data
failed validation.

Examples:

-   Invalid email.
-   Empty first name.
-   Invalid role.
-   Missing required field.

------------------------------------------------------------------------

## Why Three User Schemas?

Using one model for every operation would blur different
responsibilities.

### `UserCreate`

Represents client input for creation.

The client does not provide the generated ID.

### `UserResponse`

Represents the resource returned by the API.

It contains:

``` text
id
first_name
last_name
email
phone
role
```

### `UserUpdate`

All fields are optional because a client may update only one field.

Example:

``` json
{
  "phone": "9135559999"
}
```

------------------------------------------------------------------------

## `model_dump()` Explained

Pydantic gives us an object such as:

``` python
user
```

`model_dump()` converts it to a Python dictionary.

Conceptually:

``` python
UserCreate(...)
```

becomes:

``` python
{
    "first_name": "...",
    "last_name": "...",
    "email": "...",
    "phone": "...",
    "role": ...
}
```

This allows the data to be inserted into the temporary store.

------------------------------------------------------------------------

## Why `exclude_unset=True` Matters

For updates:

``` python
changes.model_dump(exclude_unset=True)
```

means:

> Include only fields actually supplied by the client.

If the client sends:

``` json
{
  "phone": "9135559999"
}
```

the update dictionary contains only `phone`.

Without careful update handling, omitted optional fields could
accidentally overwrite existing values.

------------------------------------------------------------------------

## Duplicate Email Logic

Before creating a user, the service checks existing email addresses.

The comparison is case-insensitive:

``` text
ade@example.com
```

and:

``` text
ADE@EXAMPLE.COM
```

are treated as the same email.

The API responds:

``` text
409 Conflict
```

when a duplicate is detected.

### Future improvement

When PostgreSQL is introduced, email uniqueness should also be enforced
at the database level. Application-only checks are not enough for a
production system with concurrent requests.

------------------------------------------------------------------------

## Why `/` Returned 404

The application defined:

``` text
/health
/users
/users/{user_id}
/docs
```

but did not define:

``` text
/
```

Therefore:

``` text
GET /
```

correctly returns:

``` json
{
  "detail": "Not Found"
}
```

This does **not** mean Uvicorn or FastAPI failed.

------------------------------------------------------------------------

## Swagger vs curl

### Swagger

Best for:

-   Discovering endpoints.
-   Reading schemas.
-   Trying requests interactively.
-   Seeing response examples.

### curl

Best for understanding the HTTP interaction more directly.

Example:

``` bash
curl -i http://127.0.0.1:8001/users/1
```

`-i` displays HTTP response headers and status information in addition
to the body.

------------------------------------------------------------------------

## Important Limitation: In-Memory Storage

Current architecture:

``` text
FastAPI
   ↓
users.py
   ↓
store.py
   ↓
Python RAM
```

If the process stops:

``` text
RAM cleared
   ↓
users_db = {}
```

This was intentional.

The purpose of Project 2 was to isolate and understand:

-   FastAPI.
-   Routing.
-   Request/response schemas.
-   Validation.
-   Status codes.
-   Error handling.
-   API testing.

Project 3 adds persistence only after these concepts work.

------------------------------------------------------------------------

## Common Troubleshooting Notes

### FastAPI import unresolved in VS Code

Likely cause:

VS Code is using the global Python interpreter instead of the project's
`.venv`.

Fix:

Select:

``` text
...\user-service\.venv\Scripts\python.exe
```

### `uvicorn main:app` fails

The file is:

``` text
app/main.py
```

so from `user-service` the correct module path is:

``` bash
python -m uvicorn app.main:app --reload --port 8001
```

### `/` returns Not Found

Expected. Use:

``` text
/health
/docs
/users
```

### Users disappeared

If Uvicorn restarted, the in-memory dictionary was recreated.

Expected in Project 2.

------------------------------------------------------------------------

## Project 2 Testing Matrix

  Test                  Expected result
  --------------------- --------------------
  GET `/health`         200
  POST valid `/users`   201
  GET `/users`          200 + list
  GET `/users/1`        200 + user
  PUT `/users/1`        200 + updated user
  GET `/users/999`      404
  PUT `/users/999`      404
  Duplicate email       409
  Invalid email         422
  Empty first name      422
  Invalid role          422
  Missing email         422

------------------------------------------------------------------------

## Newbie Explanation

Project 2 built a small web service that manages users.

A client sends JSON to FastAPI. FastAPI determines which route should
handle the request. Pydantic checks whether the supplied data is valid.
The route performs the requested operation and stores or retrieves the
data from a temporary Python dictionary. FastAPI then sends a JSON
response and an HTTP status code back to the client.

The service was tested without building a frontend by using Swagger and
curl.

------------------------------------------------------------------------

## Interview Explanation

> I built the first business microservice for a car-rental platform
> using Python and FastAPI. I separated application startup, routing,
> Pydantic schemas, and temporary storage into distinct modules so each
> component had a clear responsibility. The service supports user
> creation, listing, retrieval, and updates, as well as a health
> endpoint. I implemented schema validation, case-insensitive
> duplicate-email detection, partial-update handling with
> `exclude_unset=True`, and meaningful HTTP responses including 201,
> 404, 409, and 422. I tested both successful and failure scenarios
> through Swagger and curl. I intentionally started with an in-memory
> repository to isolate the API layer before introducing database
> complexity; the next project replaces that storage layer with
> PostgreSQL, SQLAlchemy, and Alembic.

------------------------------------------------------------------------

## STAR Interview Version

### Situation

I was building a car-rental platform as a hands-on microservices project
and needed to move from the repository and development foundation into
the first business API.

### Task

I needed to create a User Service that had clear API contracts,
supported basic user operations, validated client input, returned
meaningful HTTP errors, and could later transition to a persistent
database without redesigning the whole API.

### Action

I used FastAPI and Uvicorn to build the service and Pydantic to define
separate create, response, and update schemas. I separated the router,
schemas, temporary store, and application initialization into different
modules. I implemented create, list, retrieve, update, and health
endpoints, added duplicate-email checks, used `exclude_unset=True` for
partial updates, and tested happy and failure paths using Swagger and
curl.

### Result

The result was a working standalone User microservice that could create,
retrieve, and update validated user records and correctly return 201,
404, 409, and 422 responses. The modular structure also made the next
limitation obvious: data disappeared when the process restarted. That
became the requirement for Project 3, where the temporary store is
replaced by PostgreSQL.

------------------------------------------------------------------------

## What Project 3 Changes

Project 2:

``` text
FastAPI
   ↓
Router
   ↓
Python dictionary
```

Project 3:

``` text
FastAPI
   ↓
Router
   ↓
SQLAlchemy
   ↓
PostgreSQL
```

Project 3 introduces persistent storage and database migrations while
retaining the API principles learned in Project 2.
