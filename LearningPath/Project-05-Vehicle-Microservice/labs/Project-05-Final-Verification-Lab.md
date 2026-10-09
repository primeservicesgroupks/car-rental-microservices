# Project 5 — Final Verification and Git Checkpoint Lab

**Project:** Car Rental Microservices | **Service:** Vehicle Service | **Ports:** User 8001, Vehicle 8002

## Learning objectives
- Explain independent service databases and signed-token trust.
- Confirm vehicle persistence, public discovery, ownership, and RBAC.
- Run 14 automated tests and record evidence.
- Commit reviewed source and learning materials without secrets.

## Prerequisites
- Docker Desktop running; both PostgreSQL containers available.
- User Service and Vehicle Service virtual environments and dependencies installed.
- `.env` files exist locally and are ignored by Git.
- User Service and Vehicle Service use the same HS256 secret **for this local lab only**.
- User and vehicle databases use separate `DATABASE_URL` values.

## Architecture and trust boundary
1. Client posts credentials to `POST :8001/auth/login`.
2. User Service checks the password hash in **User PostgreSQL** and signs a JWT with `sub`, `role`, `iat`, `exp`.
3. Client sends `Authorization: Bearer <JWT>` to Vehicle Service on port 8002.
4. Vehicle Service verifies signature, expiry, user ID, and role without accessing the User database.
5. Vehicle Service checks OWNER/ADMIN permissions and writes to **Vehicle PostgreSQL**.
6. `owner_id` is an external service identifier, not a cross-database foreign key.

## Part A — Start dependencies
From `Webapp/services/user-service`:
```bash
docker compose up -d
docker compose ps
python -m uvicorn app.main:app --reload --port 8001
```
From a second terminal in `Webapp/services/vehicle-service`:
```bash
docker compose up -d
docker compose ps
python -m uvicorn app.main:app --reload --port 8002
```
If the compose service is not called `db`, substitute the actual name from `docker compose config --services`.

## Part B — Verify persistence
From `Webapp/services/vehicle-service` (adapt PostgreSQL username/database to `compose.yaml`):
```bash
docker compose exec db psql -U vehicle_app -d vehicle_rental -c "\dt"
docker compose exec db psql -U vehicle_app -d vehicle_rental -c "SELECT id,owner_id,make,model,year,daily_rate,is_available FROM vehicles WHERE id=3;"
```
Expected from previous live API response: vehicle `3`, owner `267`, Toyota Camry 2012, daily rate 45.00, available. **Database persistence is not confirmed until this query succeeds.** Restart only Uvicorn, then repeat the SQL query. Avoid `docker compose down -v`.

## Part C — Health and public listings
```bash
curl -i http://127.0.0.1:8002/health
curl -i http://127.0.0.1:8002/health/db
curl -sS http://127.0.0.1:8002/vehicles | python -m json.tool
curl -sS 'http://127.0.0.1:8002/vehicles?available_only=true' | python -m json.tool
```
Expected: 200 health responses; public listing includes available vehicle 3 if it matches endpoint filters.

## Part D — Login and owner authorization
Run from a Git Bash terminal with Python available; do not print or commit the token.
```bash
OWNER_TOKEN=$(curl -fsS -X POST http://127.0.0.1:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"vehicle-owner-p5@example.com","password":"LearningPassword123!"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
test -n "$OWNER_TOKEN" && echo 'OWNER token captured'
curl -i http://127.0.0.1:8001/auth/me -H "Authorization: Bearer $OWNER_TOKEN"
curl -i http://127.0.0.1:8002/vehicles/mine -H "Authorization: Bearer $OWNER_TOKEN"
curl -i http://127.0.0.1:8002/vehicles/mine
```
Expected: `/auth/me` 200 with OWNER; `/vehicles/mine` 200 for authenticated owner; no token returns 401. Tokens expire; log in again as needed. Do not hardcode credentials in production scripts.

## Part E — Permission matrix to verify
| Operation | Anonymous | RENTER | OWNER (own) | OWNER (other) | ADMIN |
|---|---|---|---|---|---|
| GET /vehicles | Allow | Allow | Allow | Allow | Allow |
| POST /vehicles | 401 | 403 | Allow | N/A | Allow (per policy) |
| GET /vehicles/mine | 401 | Policy-dependent | Own only | No | Policy-dependent |
| Modify vehicle | 401 | 403 | Allow | 403 | Allow |

Confirm actual implementation matches the intended policy; use tests and API docs as source of truth for precise endpoint methods.

## Part F — Automated tests
From `Webapp/services/vehicle-service`:
```bash
python -m pytest --collect-only -q
python -m pytest tests/test_authentication.py -v --tb=short
python -m pytest tests/test_authorization.py -v --tb=short
python -m pytest tests/test_vehicles.py -v --tb=short
python -m pytest -v --tb=short
```
Previously observed suite: **14 tests** (4 authentication, 5 authorization, 5 vehicle). **Do not mark passed until your terminal reports 14 passed.** Unit tests with overrides/mocks do not replace live database integration tests.

## Part G — Final security review
- Public JWT role must be signed and sourced from authenticated database record.
- No raw passwords, password hashes, JWTs, `.env`, or database volumes in Git.
- Different `DATABASE_URL` for User and Vehicle services.
- HS256 shared secret is a local lab compromise; consider asymmetric verification in production.
- Role changes are not reflected in previously issued JWTs until expiry or revocation.
- Never trust a client-supplied `owner_id` over the verified identity for owner creation.
- Confirm tests use disposable test databases and never erase live development data unintentionally.

## Part H — Git checkpoint (run from repository root)
```bash
cd ~/Documents/PrimeServicesGroupKC/car-rental-microservices
git status --short
git diff --check
git check-ignore Webapp/services/user-service/.env Webapp/services/vehicle-service/.env
git add Webapp/services/user-service/app/security.py Webapp/services/user-service/app/routers/auth.py
git add Webapp/services/vehicle-service
git add LearningPath/Project-05-Vehicle-Microservice
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git commit -m 'Complete Project 5 vehicle service and cross-service JWT integration'
git push origin main
git status
git log -1 --oneline
```
Only stage the two User Service files if you have reviewed those changes. If files were already committed, `git add` is harmless. Check staged files for secrets and `.venv` before committing. If the LearningPath folder uses another exact name, update the path.

## Evidence log (fill after running)
| Check | Result | Evidence |
|---|---|---|
| Vehicle 3 persisted in PostgreSQL | Pending | SQL output |
| Public list and availability filter | Pending | HTTP status/body |
| OWNER `/vehicles/mine` | Pending | HTTP status/body |
| Missing JWT rejected | Pending | HTTP 401 |
| Automated suite | Pending | `__ passed` |
| Commit pushed | Pending | Git SHA and clean status |

## Troubleshooting
- `no configuration file provided`: run Docker Compose in the service directory with `compose.yaml`.
- `401 invalid token`: refresh token; verify shared signing configuration and `sub`/`role`/`exp` claims.
- `403`: check role and ownership; do not bypass authorization.
- `422`: compare payload with Swagger schema.
- `500`: inspect service logs and DB health; do not expose secrets.
- `pytest 404`: verify router decorators and `app.include_router` registration.
