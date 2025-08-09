"""
User management API endpoints.

This module contains endpoints for user administration,
including CRUD operations and role management.
"""

import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from src.core.database import get_session
from src.core.exceptions import ValidationError, NotFoundError, ConflictError
from src.core.security import TokenData, require_role_with_fallback
from src.schemas.common import PaginatedResponse, PaginationInfo, SuccessResponse
from src.schemas.users import (
    UserCreateRequest,
    UserListItem,
    UserResponse,
    UserSearchParams,
    UserUpdateRequest,
)
from src.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedResponse[UserListItem])
async def list_users(
    request: Request,
    params: UserSearchParams = Depends(),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    token_data: TokenData = require_role_with_fallback("admin"),
    session: Session = Depends(get_session),
) -> PaginatedResponse[UserListItem]:
    """
    List users with optional search and pagination.

    Args:
        request: FastAPI request object
        params: Search and filter parameters
        page: Page number for pagination
        per_page: Number of items per page
        token_data: Current user token data (admin role required)
        session: Database session

    Returns:
        PaginatedResponse[UserListItem]: Paginated list of users
    """
    user_service = UserService(session)

    users, total_count = await user_service.list_users(
        search_params=params,
        page=page,
        per_page=per_page,
        requesting_user_id=token_data.user_id,
    )

    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

    pagination = PaginationInfo(
        page=page,
        per_page=per_page,
        total=total_count,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )

    return PaginatedResponse(
        success=True,
        data=users,
        pagination=pagination,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_data: UserCreateRequest,
    token_data: TokenData = require_role_with_fallback("sysadmin"),
    session: Session = Depends(get_session),
) -> UserResponse:
    """
    Create a new user.

    Args:
        request: FastAPI request object
        user_data: User creation data
        token_data: Current user token data (sysadmin role required)
        session: Database session

    Returns:
        UserResponse: Created user information

    Raises:
        HTTPException: If user creation fails
    """
    user_service = UserService(session)

    created_user = await user_service.create_user(
        user_data=user_data,
        created_by_user_id=token_data.user_id,
        request=request,
    )

    return UserResponse.model_validate(created_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    token_data: TokenData = require_role_with_fallback("user"),
    session: Session = Depends(get_session),
) -> UserResponse:
    """
    Get user by ID.

    Args:
        user_id: User unique identifier
        token_data: Current user token data (user role required, can view own profile or sysadmin can view all)
        session: Database session

    Returns:
        UserResponse: User information

    Raises:
        HTTPException: If user not found
    """
    user_service = UserService(session)

    try:
        user = await user_service.get_user_by_id(
            user_id=user_id,
            requesting_user_id=token_data.user_id,
        )

        return UserResponse.model_validate(user)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        ) from e
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdateRequest,
    request: Request,
    token_data: TokenData = require_role_with_fallback("user"),
    session: Session = Depends(get_session),
) -> UserResponse:
    """
    Update user information.

    Args:
        user_id: User unique identifier
        user_data: User update data
        request: FastAPI request object
        token_data: Current user token data (user can update own profile, sysadmin can update all)
        session: Database session

    Returns:
        UserResponse: Updated user information

    Raises:
        HTTPException: If user not found or update fails
    """
    user_service = UserService(session)

    try:
        updated_user = await user_service.update_user(
            user_id=user_id,
            user_data=user_data,
            updated_by_user_id=token_data.user_id,
            request=request,
        )

        return UserResponse.model_validate(updated_user)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        ) from e
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        ) from e


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: UUID,
    request: Request,
    token_data: TokenData = require_role_with_fallback("sysadmin"),
    session: Session = Depends(get_session),
) -> SuccessResponse:
    """
    Delete user (soft delete - deactivate).

    Args:
        user_id: User unique identifier
        request: FastAPI request object
        token_data: Current user token data (sysadmin role required)
        session: Database session

    Returns:
        SuccessResponse: Confirmation message

    Raises:
        HTTPException: If user not found or deletion fails
    """
    user_service = UserService(session)

    await user_service.deactivate_user(
        user_id=user_id,
        deactivated_by_user_id=token_data.user_id,
        request=request,
    )

    return SuccessResponse(
        success=True,
        message="User account has been deactivated successfully",
        details={"user_id": str(user_id)},
    )
