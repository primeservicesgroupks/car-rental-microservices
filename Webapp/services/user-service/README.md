# Car Rental User Service

The **User Service** is a FastAPI microservice for the Car Rental Microservices learning project.

It is responsible for:

- User registration
- User persistence
- Password hashing
- User authentication
- JWT access tokens
- Authenticated user identity
- User profile management
- Role-Based Access Control (RBAC)
- Ownership-based authorization
- Local development ADMIN provisioning

This service was developed incrementally through Projects 2, 3, and 4 of the Car Rental Microservices learning path.

---

# 1. Current Project Status

The User Service currently supports:

- FastAPI REST API
- PostgreSQL persistence
- SQLAlchemy ORM
- Alembic database migrations
- Pydantic request/response validation
- Argon2 password hashing
- JWT authentication
- OAuth2 Bearer token extraction
- Authenticated identity with `get_current_user()`
- RENTER, OWNER, and ADMIN roles
- Ownership-based authorization
- ADMIN-only operations
- Automated pytest tests
- Controlled local ADMIN provisioning

The service is currently designed for local development and learning.

---

# 2. Architecture

The User Service follows this general architecture:

```text
Client
  |
  | HTTP
  v
FastAPI
  |
  +----------------------------+
  |                            |
  v                            v
Authentication             User Routes
Router                     /users
/auth
  |                            |
  v                            v
Registration              Authorization
Login                     Dependencies
/auth/me                       |
  |                            |
  +-------------+--------------+
                |
                v
         SQLAlchemy ORM
                |
                v
           PostgreSQL
```

Authentication and authorization are intentionally separated.

Authentication answers:

```text
Who is this user?
```

Authorization answers:

```text
Is this user allowed to perform this operation?
```

---

# 3. Project Structure

```text
user-service/
|
├── app/
│   ├── routers/
│   │   ├── auth.py
│   │   └── users.py
│   │
│   ├── db.py
│   ├── dependencies.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── security.py
│
├── scripts/
│   ├── __init__.py
│   └── provision_admin.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_registration.py
│   ├── test_login.py
│   ├── test_jwt.py
│   └── test_rbac.py
│
├── alembic/
│   └── versions/
│
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── compose.yaml
├── requirements.txt
└── README.md
```

---

# 4. Major Application Files

## `app/main.py`

Creates the FastAPI application and registers the API routers.

It also provides health-check endpoints.

Main responsibilities:

```text
Create FastAPI application
        |
        +--> Register User router
        |
        +--> Register Authentication router
        |
        +--> /health
        |
        +--> /health/db
```

---

## `app/db.py`

Configures SQLAlchemy and PostgreSQL connectivity.

Responsibilities include:

- Reading `DATABASE_URL`
- Creating the SQLAlchemy engine
- Creating `SessionLocal`
- Providing `get_db()`
- Managing database sessions

---

## `app/models.py`

Contains SQLAlchemy database models.

The `User` model stores data such as:

```text
id
first_name
last_name
email
phone
role
password_hash
```

Plaintext passwords are never stored.

---

## `app/schemas.py`

Contains Pydantic request and response models.

Examples include:

```text
UserRegister
LoginRequest
TokenResponse
UserResponse
UserUpdate
UserRole
```

`UserResponse` intentionally excludes:

```text
password
password_hash
```

---

## `app/security.py`

Contains security-related functionality.

Responsibilities include:

- Password hashing
- Password verification
- JWT creation
- JWT configuration

Passwords are hashed using Argon2 through `pwdlib`.

---

## `app/dependencies.py`

Contains reusable FastAPI security and authorization dependencies.

Responsibilities include:

- Extracting Bearer tokens
- Decoding JWTs
- Validating JWTs
- Resolving the authenticated user
- Providing `get_current_user()`
- Providing reusable authorization checks such as `require_role()`

---

## `app/routers/auth.py`

Contains authentication endpoints.

Current endpoints include:

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

---

## `app/routers/users.py`

Contains protected user-management endpoints.

Current endpoints include:

```text
GET /users
GET /users/{user_id}
PUT /users/{user_id}
```

These endpoints are protected by authentication and authorization rules.

---

# 5. User Roles

The service currently supports three roles:

```text
RENTER
OWNER
ADMIN
```

## RENTER

A RENTER can:

- Register publicly
- Login
- Retrieve their authenticated identity
- View their own user profile
- Update allowed fields on their own profile

A RENTER cannot:

- List all users
- Read another user's profile
- Modify another user's profile
- Create an ADMIN account through public registration
- Promote themselves to ADMIN

---

## OWNER

An OWNER can:

- Register publicly
- Login
- Retrieve their authenticated identity
- View their own user profile
- Update allowed fields on their own profile

An OWNER currently cannot:

- List all users
- Read another user's profile
- Modify another user's profile
- Promote themselves to ADMIN

Future projects will give OWNER accounts vehicle-management capabilities.

---

## ADMIN

An ADMIN can:

- Login normally
- Retrieve their authenticated identity
- List users
- View another user's profile
- Update allowed profile fields for other users

ADMIN accounts cannot be created through public registration.

They must be provisioned through a controlled administrative process.

---

# 6. Authorization Matrix

| Operation                            | RENTER | OWNER | ADMIN |
| ------------------------------------ | -----: | ----: | ----: |
| Register publicly                    |    Yes |   Yes |    No |
| Login                                |    Yes |   Yes |   Yes |
| `GET /auth/me`                       |    Yes |   Yes |   Yes |
| View own profile                     |    Yes |   Yes |   Yes |
| Update own allowed profile fields    |    Yes |   Yes |   Yes |
| View another user's profile          |     No |    No |   Yes |
| Update another user's allowed fields |     No |    No |   Yes |
| `GET /users`                         |     No |    No |   Yes |
| Promote self to ADMIN                |     No |    No |    No |

A role does not identify a user.

For example:

```text
User #4
role = RENTER
JWT sub = 4

User #5
role = RENTER
JWT sub = 5
```

Both users have the same role but represent different authenticated identities.

Therefore:

```text
RENTER #4 --> GET /users/4 --> allowed

RENTER #4 --> GET /users/5 --> forbidden
```

---

# 7. Registration Flow

Registration uses:

```text
POST /auth/register
```

The workflow is:

```text
Registration Request
        |
        v
Pydantic Validation
        |
        v
Normalize Email
        |
        v
Check Requested Role
        |
        +---- ADMIN ----> 403 Forbidden
        |
        v
Hash Password
        |
        v
Argon2 password_hash
        |
        v
Create User
        |
        v
PostgreSQL
        |
        v
UserResponse
```

The API response never includes:

```text
password
password_hash
```

---

# 8. Password Security

Passwords are never stored directly.

Example:

```text
LearningPassword123!
        |
        v
Argon2
        |
        v
$argon2id$v=19$...
```

PostgreSQL stores only the resulting hash.

The application verifies passwords approximately as:

```text
Login Password
      |
      v
verify_password()
      |
      +--> stored Argon2 hash
      |
      v
True / False
```

Argon2 uses salts, so hashing the same password more than once does not necessarily produce identical hash strings.

---

# 9. Login Flow

Login uses:

```text
POST /auth/login
```

The workflow is:

```text
Email + Password
       |
       v
Normalize Email
       |
       v
Find User
       |
       v
Verify Password
       |
       +---- invalid ----> 401 Unauthorized
       |
       v
Create JWT
       |
       v
Return Access Token
```

Successful response:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

# 10. JWT Authentication

After login, clients send the JWT using the HTTP Authorization header:

```text
Authorization: Bearer <JWT>
```

The application processes it approximately as:

```text
Authorization Header
        |
        v
OAuth2 Bearer Dependency
        |
        v
JWT
        |
        v
Decode Token
        |
        +--> Validate Signature
        |
        +--> Validate Expiration
        |
        +--> Read Subject (sub)
        |
        v
User ID
        |
        v
PostgreSQL
        |
        v
Current User
```

The JWT identifies a specific user.

It is not merely a role token.

---

# 11. Authenticated Identity

The authenticated identity endpoint is:

```text
GET /auth/me
```

A request must contain:

```text
Authorization: Bearer <JWT>
```

The endpoint uses `get_current_user()` to resolve the token into the corresponding database user.

Example response:

```json
{
  "id": 4,
  "first_name": "Example",
  "last_name": "User",
  "email": "user@example.com",
  "phone": null,
  "role": "RENTER"
}
```

Password information is never returned.

---

# 12. Authentication vs Authorization

A valid JWT does not automatically mean a user can access every endpoint.

For example:

```text
RENTER logs in
      |
      v
Valid JWT
      |
      v
Authenticated
```

But:

```text
RENTER
  |
  +--> GET /users/own-id
  |        |
  |        +--> allowed
  |
  +--> GET /users/another-id
  |        |
  |        +--> 403 Forbidden
  |
  +--> GET /users
           |
           +--> 403 Forbidden
```

Authentication establishes identity.

Authorization determines permissions.

---

# 13. HTTP Status Codes

Important status codes used by the service include:

| Status                     | Meaning                                 |
| -------------------------- | --------------------------------------- |
| `200 OK`                   | Request succeeded                       |
| `201 Created`              | Registration succeeded                  |
| `401 Unauthorized`         | Authentication failed or JWT is invalid |
| `403 Forbidden`            | Authenticated user lacks permission     |
| `404 Not Found`            | Requested resource does not exist       |
| `409 Conflict`             | Conflict such as duplicate email        |
| `422 Unprocessable Entity` | Request/schema validation failed        |

An important distinction is:

```text
401 = Who are you?

403 = I know who you are, but you cannot do this.
```

---

# 14. Environment Configuration

Local configuration is stored in:

```text
.env
```

Example:

```env
DATABASE_URL=postgresql+psycopg://car_app:local_dev_only@127.0.0.1:5433/car_rental

JWT_SECRET_KEY=your-long-local-development-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Never commit `.env`.

The repository should contain:

```text
.env.example
```

with placeholders rather than real secrets.

Example:

```env
DATABASE_URL=postgresql+psycopg://car_app:local_dev_only@127.0.0.1:5433/car_rental

JWT_SECRET_KEY=replace_with_a_long_random_local_dev_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Verify `.env` is ignored:

```bash
git check-ignore -v .env
```

Verify it is not tracked:

```bash
git ls-files .env
```

The second command should produce no output.

---

# 15. Python Virtual Environment

From the `user-service` directory, create a virtual environment if necessary:

```bash
python -m venv .venv
```

Activate it in Git Bash:

```bash
source .venv/Scripts/activate
```

The prompt should begin with:

```text
(.venv)
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

---

# 16. Start PostgreSQL

PostgreSQL is provided through Docker Compose.

From:

```text
Webapp/services/user-service
```

run:

```bash
docker compose up -d
```

Check:

```bash
docker compose ps
```

The PostgreSQL service should be running and healthy.

The current local configuration maps PostgreSQL to:

```text
127.0.0.1:5433
```

---

# 17. Database Migrations

Alembic owns database schema changes.

Check the current migration:

```bash
alembic current
```

Check the latest migration:

```bash
alembic heads
```

Apply outstanding migrations:

```bash
alembic upgrade head
```

Do not use `Base.metadata.create_all()` as a replacement for Alembic migrations in this project.

---

# 18. Start the User Service

From the `user-service` root:

```bash
python -m uvicorn app.main:app --reload --port 8001
```

The API will be available locally at:

```text
http://127.0.0.1:8001
```

---

# 19. Swagger API Documentation

With the service running, open:

```text
http://127.0.0.1:8001/docs
```

Swagger can be used to test:

```text
POST /auth/register
POST /auth/login
GET  /auth/me

GET  /users
GET  /users/{user_id}
PUT  /users/{user_id}

GET  /health
GET  /health/db
```

---

# 20. Health Checks

## Application Health

```text
GET /health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "user-service"
}
```

This confirms FastAPI is running.

---

## Database Health

```text
GET /health/db
```

Expected response:

```json
{
  "status": "healthy",
  "database": "reachable"
}
```

This endpoint performs a lightweight:

```sql
SELECT 1;
```

to verify PostgreSQL connectivity.

---

# 21. Register a RENTER

Example using Git Bash:

```bash
curl -i -X POST http://127.0.0.1:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Example",
    "last_name": "Renter",
    "email": "example-renter@example.com",
    "password": "LearningPassword123!",
    "role": "RENTER"
  }'
```

Expected:

```text
201 Created
```

---

# 22. Register an OWNER

```bash
curl -i -X POST http://127.0.0.1:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Example",
    "last_name": "Owner",
    "email": "example-owner@example.com",
    "password": "LearningPassword123!",
    "role": "OWNER"
  }'
```

Expected:

```text
201 Created
```

---

# 23. Public ADMIN Registration Is Blocked

The following should fail:

```bash
curl -i -X POST http://127.0.0.1:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Public",
    "last_name": "Admin",
    "email": "public-admin@example.com",
    "password": "LearningPassword123!",
    "role": "ADMIN"
  }'
```

Expected:

```text
403 Forbidden
```

Public registration intentionally cannot create ADMIN accounts.

---

# 24. Provision Local Development ADMIN

ADMIN provisioning is intentionally separated from public account registration.

The safe local-development workflow is:

```text
Register Normal Account
        |
        v
RENTER or OWNER
        |
        v
Existing PostgreSQL User
        |
        v
Local Provisioning Script
        |
        v
ADMIN
```

## Step 1 — Register a normal account

Example:

```bash
curl -i -X POST http://127.0.0.1:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Admin",
    "last_name": "Learning",
    "email": "admin-learning@example.com",
    "password": "AdminLearning123!",
    "role": "RENTER"
  }'
```

Expected:

```text
201 Created
```

The account initially has:

```text
role = RENTER
```

---

## Step 2 — Verify the starting role

```bash
docker compose exec db psql -U car_app -d car_rental \
  -c "SELECT id,email,role FROM users WHERE email='admin-learning@example.com';"
```

Expected:

```text
id |            email             | role
---+------------------------------+--------
...| admin-learning@example.com   | RENTER
```

---

## Step 3 — Provision ADMIN

Run the script from the `user-service` root:

```bash
python -m scripts.provision_admin admin-learning@example.com
```

Use the module format:

```bash
python -m scripts.provision_admin user@example.com
```

rather than:

```bash
python scripts/provision_admin.py user@example.com
```

The module form ensures project imports such as `app.db` and `app.models` resolve correctly.

Expected output resembles:

```text
Promoting user to ADMIN:
  admin-learning@example.com

SUCCESS:
  id    = ...
  email = admin-learning@example.com
  role  = ADMIN
```

---

## Step 4 — Verify PostgreSQL

```bash
docker compose exec db psql -U car_app -d car_rental \
  -c "SELECT id,email,role FROM users WHERE email='admin-learning@example.com';"
```

Expected:

```text
id |            email             | role
---+------------------------------+-------
...| admin-learning@example.com   | ADMIN
```

---

## Step 5 — Test idempotency

Run the command again:

```bash
python -m scripts.provision_admin admin-learning@example.com
```

The script should recognize that the account is already ADMIN and make no unnecessary change.

---

## Step 6 — Test nonexistent user protection

```bash
python -m scripts.provision_admin does-not-exist@example.com
```

Expected behavior:

```text
ERROR: User does not exist:
  does-not-exist@example.com
```

The script does not create users.

It only promotes an existing user through a controlled local-development operation.

---

# 25. Inspect Current Users

To inspect users:

```bash
docker compose exec db psql -U car_app -d car_rental \
  -c "SELECT id,email,role FROM users ORDER BY id;"
```

This is useful when testing RENTER, OWNER, and ADMIN permissions.

Do not include `password_hash` in normal application output or screenshots unless specifically debugging password storage.

---

# 26. Login

Example:

```bash
curl -s -X POST http://127.0.0.1:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "example-renter@example.com",
    "password": "LearningPassword123!"
  }'
```

Expected:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

# 27. Capture a JWT in Git Bash

Example:

```bash
RENTER_TOKEN=$(curl -s -X POST http://127.0.0.1:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "example-renter@example.com",
    "password": "LearningPassword123!"
  }' | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
```

Verify:

```bash
echo "$RENTER_TOKEN"
```

A JWT normally begins with something similar to:

```text
eyJ...
```

---

# 28. Test Authenticated Identity

```bash
curl -s http://127.0.0.1:8001/auth/me \
  -H "Authorization: Bearer $RENTER_TOKEN"
```

Expected response includes the authenticated user's information and role.

It must not contain:

```text
password
password_hash
```

---

# 29. Test RBAC

## RENTER Attempting to List All Users

```bash
curl -i http://127.0.0.1:8001/users \
  -H "Authorization: Bearer $RENTER_TOKEN"
```

Expected:

```text
403 Forbidden
```

---

## ADMIN Listing Users

After obtaining an ADMIN JWT:

```bash
curl -i http://127.0.0.1:8001/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Expected:

```text
200 OK
```

---

## User Reading Own Profile

```bash
curl -i http://127.0.0.1:8001/users/<USER_ID> \
  -H "Authorization: Bearer $RENTER_TOKEN"
```

When `<USER_ID>` belongs to the authenticated RENTER:

```text
200 OK
```

---

## User Reading Another Profile

If the authenticated RENTER attempts:

```text
GET /users/<OTHER_USER_ID>
```

expected:

```text
403 Forbidden
```

---

# 30. Automated Testing

Project 4 includes automated tests using `pytest`.

Current test files:

```text
tests/
├── conftest.py
├── test_registration.py
├── test_login.py
├── test_jwt.py
└── test_rbac.py
```

---

# 31. Test Account Convention

Automated test accounts use:

```text
pytest-<name>@example.com
```

Examples:

```text
pytest-renter-registration@example.com
pytest-login-success@example.com
pytest-jwt-valid@example.com
pytest-rbac-admin@example.com
```

This allows pytest to distinguish automated test users from normal development accounts.

The cleanup fixture removes only users whose email begins with:

```text
pytest-
```

Normal development accounts are left untouched.

---

# 32. Run Registration Tests

```bash
pytest tests/test_registration.py -v
```

Registration tests cover:

- Successful RENTER registration
- Successful OWNER registration
- ADMIN registration rejection
- Duplicate email rejection
- Password hashing
- Password hash response protection
- Email normalization

---

# 33. Run Login Tests

```bash
pytest tests/test_login.py -v
```

Login tests cover:

- Successful login
- Wrong password
- Unknown account
- Case-insensitive email login
- JWT response generation

---

# 34. Run JWT Tests

```bash
pytest tests/test_jwt.py -v
```

JWT tests cover:

- Valid JWT
- Authenticated identity
- Missing token
- Invalid token
- Expired token
- Missing JWT subject
- JWT referencing a nonexistent user

---

# 35. Run RBAC Tests

```bash
pytest tests/test_rbac.py -v
```

RBAC tests cover:

- RENTER cannot list users
- OWNER cannot list users
- ADMIN can list users
- RENTER can read own profile
- OWNER can read own profile
- RENTER cannot read another RENTER
- RENTER cannot read OWNER
- OWNER cannot read RENTER
- ADMIN can read another user
- RENTER can update own profile
- OWNER can update own profile
- Cross-user updates are rejected
- ADMIN can update another user
- Self-promotion to ADMIN is rejected
- Protected endpoints require authentication

---

# 36. Run the Complete Test Suite

Run:

```bash
pytest -v
```

For concise output:

```bash
pytest -q
```

All tests should pass before creating the final Project 4 Git checkpoint.

---

# 37. Verify Test Cleanup

After pytest completes:

```bash
docker compose exec db psql -U car_app -d car_rental \
  -c "SELECT id,email,role FROM users WHERE email LIKE 'pytest-%' ORDER BY id;"
```

Expected:

```text
(0 rows)
```

This confirms pytest test users were cleaned up.

---

# 38. Security Principles Demonstrated

Project 4 demonstrates several important security concepts.

## Never Store Plaintext Passwords

Store:

```text
password_hash
```

not:

```text
password
```

---

## Never Expose Password Hashes

Even though a hash is not the plaintext password, it is sensitive authentication material.

API responses must never return it.

---

## Normalize Email Addresses

Example:

```text
User@Example.com
```

becomes:

```text
user@example.com
```

This helps enforce consistent identity and duplicate-email protection.

---

## Authentication Is Not Authorization

A valid JWT proves identity.

It does not automatically grant permission to every resource.

---

## Prevent Horizontal Privilege Escalation

Example attack:

```text
RENTER #4
    |
    v
GET /users/5
```

Expected:

```text
403 Forbidden
```

User #4 should not gain access to user #5 simply by changing the URL.

---

## Prevent Vertical Privilege Escalation

Example attack:

```text
RENTER
   |
   v
PUT /users/<own-id>

{
  "role": "ADMIN"
}
```

The normal profile update workflow must not allow the user to promote themselves.

---

## Separate Administrative Provisioning

Public registration:

```text
RENTER --> allowed
OWNER  --> allowed
ADMIN  --> rejected
```

Controlled local provisioning:

```text
Existing User
      |
      v
python -m scripts.provision_admin <email>
      |
      v
ADMIN
```

This keeps administrative privilege creation outside the public registration API.

---

# 39. Development Workflow

A typical local development session is:

```text
1. Navigate to user-service

2. Activate .venv

3. Start PostgreSQL
   docker compose up -d

4. Verify containers
   docker compose ps

5. Apply migrations
   alembic upgrade head

6. Start FastAPI
   python -m uvicorn app.main:app --reload --port 8001

7. Develop/test

8. Run pytest
   pytest -q

9. Review Git changes
   git status
   git diff

10. Commit
```

---

# 40. Stop Local Services

Stop Uvicorn with:

```text
Ctrl+C
```

Stop PostgreSQL:

```bash
docker compose down
```

This stops/removes the container but retains the PostgreSQL Docker volume unless the volume is explicitly removed.

Do not use:

```bash
docker compose down -v
```

unless you intentionally want to delete the local PostgreSQL data volume.

---

# 41. Git Safety Check

Before committing:

```bash
git status --short
```

Verify `.env` is ignored:

```bash
git check-ignore -v .env
```

Verify `.env` is not tracked:

```bash
git ls-files .env
```

Expected:

```text
<no output>
```

Review changes:

```bash
git diff
```

After staging:

```bash
git diff --cached
```

Never commit:

```text
.env
JWT secrets
database passwords intended to remain secret
.venv/
__pycache__/
```

---

# 42. Project 4 Final Verification

Before considering Project 4 complete:

```bash
python -m py_compile \
  app/main.py \
  app/db.py \
  app/models.py \
  app/schemas.py \
  app/security.py \
  app/dependencies.py \
  app/routers/auth.py \
  app/routers/users.py \
  scripts/provision_admin.py
```

Check migrations:

```bash
alembic current
alembic heads
```

Run tests:

```bash
pytest -q
```

Check Git:

```bash
git status
```

---

# 43. Project 4 Completion Checklist

```text
PASSWORD SECURITY
[ ] Argon2 password hashing works
[ ] Plaintext passwords are never stored
[ ] Password hashes are never returned through the API

REGISTRATION
[ ] RENTER registration works
[ ] OWNER registration works
[ ] Public ADMIN registration is blocked
[ ] Duplicate email protection works
[ ] Email normalization works

LOGIN
[ ] Correct credentials authenticate
[ ] Wrong password returns 401
[ ] Unknown account returns 401
[ ] JWT access token is returned

JWT
[ ] JWT signature validation works
[ ] JWT expiration validation works
[ ] JWT subject identifies the user
[ ] Missing JWT is rejected
[ ] Invalid JWT is rejected
[ ] Expired JWT is rejected

AUTHENTICATED IDENTITY
[ ] OAuth2 Bearer authentication works
[ ] get_current_user() resolves the user
[ ] GET /auth/me works

AUTHORIZATION
[ ] GET /users is ADMIN-only
[ ] User can view own profile
[ ] User cannot view another user's profile
[ ] User can update own allowed fields
[ ] User cannot modify another user
[ ] ADMIN can access other users
[ ] Self-promotion to ADMIN is blocked

ADMIN PROVISIONING
[ ] Public ADMIN registration is blocked
[ ] Existing account can be provisioned locally
[ ] python -m scripts.provision_admin works
[ ] Already-ADMIN execution is safe
[ ] Nonexistent user is rejected

TESTING
[ ] Registration tests pass
[ ] Login tests pass
[ ] JWT tests pass
[ ] RBAC tests pass
[ ] Complete pytest suite passes
[ ] Test accounts are cleaned up

DOCUMENTATION
[ ] README updated
[ ] Project 4 learning notes updated

GIT
[ ] .env ignored
[ ] Secrets not staged
[ ] Final tests pass
[ ] Project 4 committed
[ ] Project 4 pushed to GitHub
```

---

# 44. Final Project 4 Git Checkpoint

After all tests pass:

```bash
git status --short
```

Review:

```bash
git diff
```

Stage:

```bash
git add .
```

Review staged files:

```bash
git status
```

Run the tests one final time:

```bash
pytest -q
```

Inspect staged changes:

```bash
git diff --cached --stat
```

Commit:

```bash
git commit -m "Complete Project 4 authentication authorization and tests"
```

Push:

```bash
git push
```

Verify:

```bash
git log --oneline -8
```

---

# 45. What Project 4 Accomplished

Project 4 transformed the User Service from a basic PostgreSQL CRUD API into an authenticated and authorized microservice.

Before Project 4:

```text
Client
   |
   v
User CRUD
   |
   v
PostgreSQL
```

After Project 4:

```text
                         PostgreSQL
                             ^
                             |
                         SQLAlchemy
                             ^
                             |
Client --> FastAPI --> Authentication
              |
              +--> Registration
              |
              +--> Password Hashing
              |
              +--> Login
              |
              +--> JWT
              |
              +--> Authenticated Identity
              |
              +--> Ownership Authorization
              |
              +--> RBAC
              |
              +--> Protected User Operations
```

The service now has the security foundation required for the next business microservice.

---

# 46. Next Project

## Project 5 — Vehicle Service

The next project introduces the Vehicle Service.

The planned architecture begins moving toward:

```text
                         +----------------+
                         |  User Service  |
                         |    :8001       |
                         +-------+--------+
                                 |
                                 | authenticated
                                 | user identity
                                 |
Client                           |
  |                              |
  +------------------------------+
  |
  v
+----------------+
| Vehicle Service|
|     :8002      |
+-------+--------+
        |
        v
   PostgreSQL
```

Project 5 will introduce concepts such as:

- Vehicle data modeling
- Vehicle CRUD operations
- OWNER-specific capabilities
- Service boundaries
- Ownership of vehicles
- Authorization across business resources
- Vehicle search/listing endpoints
- Independent microservice configuration
- Independent database design

Project 4 therefore provides the identity and authorization foundation that later services can build upon.
