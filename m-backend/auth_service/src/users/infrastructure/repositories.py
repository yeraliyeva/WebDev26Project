"""Concrete repository implementations using Django ORM."""

from __future__ import annotations

import uuid
from typing import Optional

from users.domain.entities import ProfileImageEntity, UserEntity
from users.domain.repositories import AbstractProfileImageRepository, AbstractUserRepository
from users.infrastructure.models import ProfileImage, User


class DjangoUserRepository(AbstractUserRepository):
    """ORM-backed implementation of the user repository."""

    def get_by_id(self, user_id: uuid.UUID) -> Optional[UserEntity]:
        """Retrieves a user entity by primary key."""
        try:
            return self._to_entity(User.objects.select_related("profile").get(pk=user_id))
        except User.DoesNotExist:
            return None

    def get_by_login(self, login: str) -> Optional[UserEntity]:
        """Retrieves a user by username or email."""
        try:
            model = User.objects.select_related("profile").get(
                **self._login_lookup(login)
            )
            return self._to_entity(model)
        except User.DoesNotExist:
            return None

    def exists_by_username(self, username: str) -> bool:
        """Returns True if the username is taken."""
        return User.objects.filter(username=username).exists()

    def exists_by_email(self, email: str) -> bool:
        """Returns True if the email is registered."""
        return User.objects.filter(email=email).exists()

    def save(self, user: UserEntity) -> UserEntity:
        """Persists a new user entity."""
        profile = None
        if user.profile_image is not None:
             try:
                profile = ProfileImage.objects.get(pk=user.profile_image.id)
             except ProfileImage.DoesNotExist:
                profile = None

        model = User(
            id=user.id,
            username=user.username,
            email=user.email,
            password=user.password_hash,
            profile=profile,
        )
        model.save()
        return self._to_entity(model)

    def _login_lookup(self, login: str) -> dict:
        if "@" in login:
            return {"email": login}
        return {"username": login}

    def _to_entity(self, model: User) -> UserEntity:
        profile_entity = None
        if model.profile_id is not None:
            profile_entity = ProfileImageEntity(
                id=model.profile.id,
                image_url=model.profile.image_url,
            )
        return UserEntity(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password,
            created_at=model.created_at,
            updated_at=model.updated_at,
            profile_image=profile_entity,
        )


class DjangoProfileImageRepository(AbstractProfileImageRepository):
    """ORM-backed implementation of the profile image repository."""

    def get_by_id(self, image_id: uuid.UUID) -> Optional[ProfileImageEntity]:
        """Retrieves a profile image by id."""
        try:
            model = ProfileImage.objects.get(pk=image_id)
            return ProfileImageEntity(id=model.id, image_url=model.image_url)
        except ProfileImage.DoesNotExist:
            return None
