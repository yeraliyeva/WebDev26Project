"""Registration use case."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from django.contrib.auth.hashers import make_password

from users.application.dto import RegisterUserDTO, UserResponseDTO
from users.application.exceptions import (
    ProfileImageNotFoundError,
    UserAlreadyExistsError,
)
from users.domain.entities import UserEntity
from users.domain.repositories import AbstractProfileImageRepository, AbstractUserRepository
from users.infrastructure.kafka.producer import UserEventProducer


class RegisterUserUseCase:
    """Handles new user registration and triggers the balance-creation event."""

    def __init__(
        self,
        user_repository: AbstractUserRepository,
        profile_image_repository: AbstractProfileImageRepository,
        event_producer: UserEventProducer,
    ) -> None:
        self._user_repository = user_repository
        self._profile_image_repository = profile_image_repository
        self._event_producer = event_producer

    def execute(self, dto: RegisterUserDTO) -> UserResponseDTO:
        """Creates a new user account.

        Args:
            dto: Validated registration input.

        Returns:
            Public representation of the newly created user.

        Raises:
            UserAlreadyExistsError: If username or email is already taken.
            ProfileImageNotFoundError: If the given profile_image_id does not exist.
        """
        if self._user_repository.exists_by_username(dto.username):
            raise UserAlreadyExistsError(f"Username '{dto.username}' is already taken.")

        if self._user_repository.exists_by_email(dto.email):
            raise UserAlreadyExistsError(f"Email '{dto.email}' is already registered.")

        profile_image = None
        if dto.profile_image_id is not None:
            profile_image = self._profile_image_repository.get_by_id(dto.profile_image_id)
            if profile_image is None:
                raise ProfileImageNotFoundError(
                    f"Profile image '{dto.profile_image_id}' not found."
                )

        now = datetime.now(tz=timezone.utc)
        user = UserEntity(
            id=uuid.uuid4(),
            username=dto.username,
            email=dto.email,
            password_hash=make_password(dto.password),
            created_at=now,
            updated_at=now,
            profile_image=profile_image,
        )

        saved = self._user_repository.save(user)
        self._event_producer.publish_user_registered(saved.id, saved.username)

        return UserResponseDTO(
            id=saved.id,
            username=saved.username,
            email=saved.email,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
            profile_image_url=saved.profile_image.image_url if saved.profile_image else None,
        )
