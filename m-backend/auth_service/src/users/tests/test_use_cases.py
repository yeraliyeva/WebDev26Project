"""Unit tests for application use cases."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from users.application.dto import LoginDTO, RegisterUserDTO
from users.application.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from users.application.use_cases.get_user import GetUserUseCase
from users.application.use_cases.login import LoginUseCase
from users.application.use_cases.register import RegisterUserUseCase


class TestRegisterUserUseCase:
    """Tests for the RegisterUserUseCase."""

    def _make_use_case(
        self,
        user_repo: MagicMock,
        image_repo: MagicMock | None = None,
        producer: MagicMock | None = None,
    ) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            user_repository=user_repo,
            profile_image_repository=image_repo or MagicMock(),
            event_producer=producer or MagicMock(),
        )

    def test_raises_when_username_taken(self) -> None:
        """Should raise UserAlreadyExistsError when username is already taken."""
        repo = MagicMock()
        repo.exists_by_username.return_value = True

        use_case = self._make_use_case(repo)
        dto = RegisterUserDTO(
            username="taken", email="new@test.com", password="password123", profile_image_id=None
        )

        with pytest.raises(UserAlreadyExistsError):
            use_case.execute(dto)

    def test_raises_when_email_taken(self) -> None:
        """Should raise UserAlreadyExistsError when email is already registered."""
        repo = MagicMock()
        repo.exists_by_username.return_value = False
        repo.exists_by_email.return_value = True

        use_case = self._make_use_case(repo)
        dto = RegisterUserDTO(
            username="newuser", email="taken@test.com", password="password123", profile_image_id=None
        )

        with pytest.raises(UserAlreadyExistsError):
            use_case.execute(dto)

    @pytest.mark.django_db
    def test_publishes_event_on_success(self) -> None:
        """Should publish a user.registered event after successful registration."""
        from users.tests.factories import UserFactory

        repo = MagicMock()
        repo.exists_by_username.return_value = False
        repo.exists_by_email.return_value = False

        saved_entity = MagicMock()
        saved_entity.id = uuid.uuid4()
        saved_entity.username = "newuser"
        saved_entity.email = "newuser@test.com"
        saved_entity.profile_image = None
        repo.save.return_value = saved_entity

        producer = MagicMock()
        use_case = self._make_use_case(repo, producer=producer)

        dto = RegisterUserDTO(
            username="newuser",
            email="newuser@test.com",
            password="password123",
            profile_image_id=None,
        )
        use_case.execute(dto)

        producer.publish_user_registered.assert_called_once_with(
            saved_entity.id, saved_entity.username
        )


class TestGetUserUseCase:
    """Tests for the GetUserUseCase."""

    def test_raises_when_user_not_found(self) -> None:
        """Should raise UserNotFoundError when user does not exist."""
        repo = MagicMock()
        repo.get_by_id.return_value = None

        use_case = GetUserUseCase(user_repository=repo)

        with pytest.raises(UserNotFoundError):
            use_case.execute(uuid.uuid4())
