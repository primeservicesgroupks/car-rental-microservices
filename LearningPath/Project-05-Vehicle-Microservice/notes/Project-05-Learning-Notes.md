# Project 5 — Learning Notes and Architecture Review

## Executive summary
Project 5 adds an independently deployable FastAPI Vehicle Service to the car rental platform. It owns vehicle data in PostgreSQL, uses Alembic for schema migrations, validates JWTs issued by Project 4, and enforces vehicle role/ownership rules. A live API response showed a created **2012 Toyota Camry** (vehicle ID **3**, owner ID **267**, $45/day, Overland Park KS). That response demonstrates the integration path, but SQL persistence and the final 14-test run still require independent confirmation.

## Component responsibilities
| Component | Responsibility | Boundary |
|---|---|---|
| User Service `:8001` | Registration, Argon2 password verification, JWT issue | User DB only |
| Vehicle Service `:8002` | Vehicle CRUD/listing, availability, JWT verification, RBAC | Vehicle DB only |
| User PostgreSQL | Users, roles, password hashes | No direct Vehicle Service access |
| Vehicle PostgreSQL | Vehicles, owner_id, rates, availability | No direct User Service access |
| Client | Login, attach bearer token, request vehicle operations | Untrusted input |

## Main concepts learned
**Database per service:** Independent schema and migrations reduce coupling. `owner_id` references a User Service identity by value; no cross-service foreign key.

**Authentication vs authorization:** Authentication verifies signed JWT and establishes `CurrentIdentity(id,role)`. Authorization checks whether this identity can create or modify the requested vehicle.

**JWT claims:** `sub` (string user ID), `role` (RENTER/OWNER/ADMIN), `iat` (issue time), `exp` (expiry). Signature and expiry verification are mandatory. Missing role previously caused Vehicle Service 401; the User Service JWT issuer was updated to include the database role.

**Permission examples:** Public discovery is readable; RENTER cannot create vehicles; OWNER may create and modify own records; ADMIN may modify any vehicle according to policy. Verify exact routes and exceptions against the implemented code and tests.

**Persistence:** SQLAlchemy writes records to PostgreSQL; Alembic manages schema. FastAPI restart should not erase records. Avoid destroying Docker volumes while testing persistence.

**Tests:** Four authentication, five authorization, five vehicle API tests were previously collected. Confirm final suite status rather than assuming pass.

## Architecture diagram (text)
```text
                     CLIENT / API CONSUMER
                             |
                 POST /auth/login (email,password)
                             v
               +-----------------------------+
               | User Service FastAPI :8001  |
               | Argon2; signs JWT (HS256)   |
               +-------------+---------------+
                             |
                     User PostgreSQL
                             |
                  JWT: sub,role,iat,exp
                             |
           Authorization: Bearer <signed JWT>
                             v
               +-----------------------------+
               | Vehicle Service :8002       |
               | Verify JWT; role/owner RBAC |
               | Vehicle routes + SQLAlchemy |
               +-------------+---------------+
                             |
                   Vehicle PostgreSQL
                 (vehicles, owner_id, rate)
```

## Architecture decision record
- **ADR-05-01:** Separate service-owned PostgreSQL databases for data ownership.
- **ADR-05-02:** Local HS256 token verification to learn stateless cross-service authentication; production should consider asymmetric signing and key rotation.
- **ADR-05-03:** Use owner ID from verified identity; reject attempts to modify another owner's vehicle.
- **ADR-05-04:** Test at two layers: automated route tests and live cross-service/DB checks.

## Current verified evidence and remaining work
**Observed:** Vehicle API returned vehicle 3 with owner 267, Toyota Camry, `is_available=true`, and creation timestamp. JWT role inclusion was validated in a local encode/decode test.

**Still to record:** direct SQL query for vehicle 3, public GET response, authenticated `/vehicles/mine`, final 14-test output, and Git commit SHA.

## Project 6 handoff: vehicle images
Next, plan S3 object storage for vehicle images, object ownership checks, content type/size validation, presigned uploads, private buckets, IAM least privilege, and cleanup rules. Store image metadata in Vehicle PostgreSQL; store image bytes in object storage.
