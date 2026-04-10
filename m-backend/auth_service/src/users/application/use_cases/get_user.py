"""Get user info use case."""

from __future__ import annotations

import uuid

from users.application.dto import UserResponseDTO
from users.application.exceptions import UserNotFoundError
from users.domain.repositories import AbstractUserRepository


class GetUserUseCase:
    """Retrieves public profile information for a given user."""

    def __init__(self, user_repository: AbstractUserRepository) -> None:
        self._user_repository = user_repository

    def execute(self, user_id: uuid.UUID) -> UserResponseDTO:
        """Returns user profile data.

        Args:
            user_id: The UUID of the user to retrieve.

        Returns:
            Public user profile DTO.

        Raises:
            UserNotFoundError: If no user with this id exists.
        """
        user = self._user_repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError(f"User '{user_id}' not found.")

        return UserResponseDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
            profile_image_url=user.profile_image.image_url if user.profile_image else None,
        )
