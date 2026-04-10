"""Login use case."""

from __future__ import annotations

from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken

from users.application.dto import LoginDTO, TokenPairDTO
from users.application.exceptions import InvalidCredentialsError
from users.domain.repositories import AbstractUserRepository


class LoginUseCase:
    """Authenticates a user and issues a JWT token pair."""

    def __init__(self, user_repository: AbstractUserRepository) -> None:
        self._user_repository = user_repository

    def execute(self, dto: LoginDTO) -> TokenPairDTO:
        """Validates credentials and returns access + refresh tokens.

        Args:
            dto: Login input containing username/email and password.

        Returns:
            A token pair for the authenticated user.

        Raises:
            InvalidCredentialsError: If no matching user is found or password is wrong.
        """
        user = self._user_repository.get_by_login(dto.login)

        if user is None or not check_password(dto.password, user.password_hash):
            raise InvalidCredentialsError("Invalid credentials.")

        from users.infrastructure.models import User as UserModel

        user_model = UserModel.objects.get(pk=user.id)
        refresh = RefreshToken.for_user(user_model)

        return TokenPairDTO(
            user_id=user.id,
            access_token=str(refresh.access_token),
            refresh_token=str(refresh),
        )
