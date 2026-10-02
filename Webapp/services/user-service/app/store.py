"""
store.py

Temporary in-memory storage for the User Service.

For Project 2, this dictionary acts like our database.

IMPORTANT:
All data disappears when the application restarts.

Project 3 will replace this with PostgreSQL.
"""


# =========================================================
# TEMPORARY USER DATABASE
# =========================================================

# Key:
#     Integer user ID
#
# Value:
#     Dictionary containing the user's data.
#
# Example:
#
# users_db = {
#     1: {
#         "id": 1,
#         "first_name": "James",
#         "last_name": "Smith",
#         "email": "james@example.com",
#         "phone": "9135551234",
#         "role": "RENTER",
#     }
# }

users_db: dict[int, dict] = {}


# =========================================================
# NEXT USER ID
# =========================================================

# Tracks the ID that should be assigned to the
# next user that is created.
#
# User 1 -> ID 1
# User 2 -> ID 2
# User 3 -> ID 3
#
# create_user() increments this value after each user.

next_user_id = 1