"""
provision_admin.py

Controlled local-development utility for promoting an
existing user to ADMIN.

Usage:

    python scripts/provision_admin.py \
        local-admin@example.com

Important:

    - The user must already exist.
    - This script does NOT create users.
    - Public POST /auth/register continues to block ADMIN.
    - This is intended for local development/testing.
"""

import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User


def provision_admin(
    email: str,
) -> int:
    """
    Promote an existing local-development user to ADMIN.
    """

    normalized_email = (
        email.strip().lower()
    )

    with SessionLocal() as db:

        user = db.scalar(
            select(User).where(
                User.email == normalized_email
            )
        )

        if user is None:
            print(
                "ERROR: User does not exist:"
            )
            print(
                f"  {normalized_email}"
            )
            return 1

        if user.role == "ADMIN":
            print(
                "User is already ADMIN:"
            )
            print(
                f"  {normalized_email}"
            )
            return 0

        print(
            "Promoting user to ADMIN:"
        )
        print(
            f"  {normalized_email}"
        )

        user.role = "ADMIN"

        db.commit()
        db.refresh(user)

        print(
            "SUCCESS:"
        )
        print(
            f"  id   = {user.id}"
        )
        print(
            f"  email = {user.email}"
        )
        print(
            f"  role  = {user.role}"
        )

        return 0


def main() -> int:

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "  python scripts/provision_admin.py "
            "<existing-user-email>"
        )

        return 2

    return provision_admin(
        sys.argv[1]
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )