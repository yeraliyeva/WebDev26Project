"""Token refresh use case."""

from __future__ import annotations

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


class RefreshTokenUseCase:
    """Issues a new access token from a valid refresh token."""

    def execute(self, refresh_token_str: str) -> str:
        """Validates the refresh token and returns a new access token.

        Args:
            refresh_token_str: The raw refresh token string.

        Returns:
            A new access token string.

        Raises:
            TokenError: If the refresh token is invalid or expired.
        """
        token = RefreshToken(refresh_token_str)
        return str(token.access_token)
