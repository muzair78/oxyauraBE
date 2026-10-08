from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.model.user import User
from app.schema.userSchema import (
    TokenResponse,
    UserCreate,
    UserResponse,
    UserSignIn,
)
from app.utils.security import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, fullname, and a securely hashed password.",
)
async def signup(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    normalized_email = user_in.email.strip().lower()

    # 1. Check if user already exists
    query = select(User).where(User.email == normalized_email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # 2. Hash password securely
    hashed_password = hash_password(user_in.password)

    # 3. Create new user record
    new_user = User(
        fullname=user_in.fullname.strip(),
        email=normalized_email,
        password=hashed_password,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post(
    "/signin",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in user",
    description="Authenticate user with email and password and return a JWT access token.",
)
async def signin(
    credentials: UserSignIn,
    db: AsyncSession = Depends(get_db),
):
    normalized_email = credentials.email.strip().lower()

    # 1. Fetch user by email
    query = select(User).where(User.email == normalized_email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # 2. Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generate JWT access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
