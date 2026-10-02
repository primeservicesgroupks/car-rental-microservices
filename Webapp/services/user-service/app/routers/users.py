"""
users.py

API routes for the User Service.

Endpoints:

    POST /users
        Create a new user.

    GET /users
        Retrieve all users.

    GET /users/{user_id}
        Retrieve one user.

    PUT /users/{user_id}
        Update an existing user.

Project 2:
    Data is stored temporarily in app/store.py.

Project 3:
    The temporary store will be replaced with PostgreSQL.
"""

from fastapi import APIRouter, HTTPException, status

from app import store
from app.schemas import UserCreate, UserResponse, UserUpdate


# =========================================================
# ROUTER CONFIGURATION
# =========================================================

# prefix="/users"
#
# means every endpoint in this router starts with:
#
#     /users
#
# tags=["Users"]
#
# groups these endpoints together in Swagger.

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# =========================================================
# CREATE USER
# POST /users
# =========================================================

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: UserCreate):
    """
    Create a new user.

    FastAPI validates the incoming request using
    the UserCreate schema before this function runs.
    """

    # -----------------------------------------------------
    # CHECK FOR DUPLICATE EMAIL
    # -----------------------------------------------------

    # Search existing users before creating a new one.
    #
    # lower() makes the comparison case-insensitive.
    #
    # Example:
    #
    # James@example.com
    #
    # is treated the same as:
    #
    # james@example.com

    for existing_user in store.users_db.values():

        existing_email = str(
            existing_user["email"]
        ).lower()

        requested_email = str(
            user.email
        ).lower()

        if existing_email == requested_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

    # -----------------------------------------------------
    # GENERATE USER ID
    # -----------------------------------------------------

    user_id = store.next_user_id


    # -----------------------------------------------------
    # BUILD USER RECORD
    # -----------------------------------------------------

    # model_dump() converts the Pydantic UserCreate
    # object into a regular Python dictionary.
    #
    # The ** operator unpacks those fields into
    # our new dictionary.

    new_user = {
        "id": user_id,
        **user.model_dump(),
    }


    # -----------------------------------------------------
    # SAVE USER
    # -----------------------------------------------------

    # Store the user using the ID as the dictionary key.

    store.users_db[user_id] = new_user


    # Prepare the next ID.

    store.next_user_id += 1


    return new_user


# =========================================================
# LIST ALL USERS
# GET /users
# =========================================================

@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
def list_users():
    """
    Return every user currently stored.

    GET endpoints retrieve information without
    changing application state.
    """

    # users_db looks like:
    #
    # {
    #     1: {...},
    #     2: {...}
    # }
    #
    # .values() retrieves the user dictionaries.
    #
    # list(...) converts those values into a list
    # that FastAPI can return as JSON.

    return list(store.users_db.values())


# =========================================================
# RETRIEVE ONE USER
# GET /users/{user_id}
# =========================================================

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user(user_id: int):
    """
    Return one user by numeric ID.
    """

    # .get() safely searches the dictionary.
    #
    # If the ID exists:
    #     user contains the user's data.
    #
    # If the ID does not exist:
    #     user becomes None.

    user = store.users_db.get(user_id)


    # -----------------------------------------------------
    # USER NOT FOUND
    # -----------------------------------------------------

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


    return user


# =========================================================
# UPDATE USER
# PUT /users/{user_id}
# =========================================================

@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def update_user(
    user_id: int,
    changes: UserUpdate,
):
    """
    Update an existing user.

    Only fields supplied by the client will be changed.
    """

    # -----------------------------------------------------
    # FIND USER
    # -----------------------------------------------------

    user = store.users_db.get(user_id)


    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


    # -----------------------------------------------------
    # GET REQUESTED CHANGES
    # -----------------------------------------------------

    # exclude_unset=True means:
    #
    # Only fields actually supplied by the client
    # are included.
    #
    # Example request:
    #
    # {
    #     "phone": "9135559999"
    # }
    #
    # becomes:
    #
    # {
    #     "phone": "9135559999"
    # }
    #
    # Other fields remain untouched.

    update_data = changes.model_dump(
        exclude_unset=True,
    )


    # -----------------------------------------------------
    # CHECK EMAIL UNIQUENESS
    # -----------------------------------------------------

    # We only need to perform this check if the client
    # is attempting to change the email address.

    if "email" in update_data:

        new_email = str(
            update_data["email"]
        ).lower()


        for existing_id, existing_user in store.users_db.items():

            # Do not compare the user against themselves.
            if existing_id == user_id:
                continue


            existing_email = str(
                existing_user["email"]
            ).lower()


            if existing_email == new_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists",
                )


    # -----------------------------------------------------
    # APPLY CHANGES
    # -----------------------------------------------------

    user.update(update_data)


    # Save the updated user back into our temporary store.

    store.users_db[user_id] = user


    return user