"""HTTP views — thin adapters between HTTP and use cases."""

from __future__ import annotations

import uuid

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError

from users.application.dto import LoginDTO, RegisterUserDTO
from users.application.exceptions import ApplicationError
from users.application.use_cases.get_user import GetUserUseCase
from users.application.use_cases.login import LoginUseCase
from users.application.use_cases.refresh_token import RefreshTokenUseCase
from users.application.use_cases.register import RegisterUserUseCase
from users.infrastructure.kafka.producer import UserEventProducer
from users.infrastructure.repositories import DjangoProfileImageRepository, DjangoUserRepository
from users.presentation.serializers import (
    LoginSerializer,
    RefreshSerializer,
    RegisterSerializer,
    TokenPairSerializer,
    UserResponseSerializer,
)


def _make_user_repository() -> DjangoUserRepository:
    return DjangoUserRepository()


def _make_profile_image_repository() -> DjangoProfileImageRepository:
    return DjangoProfileImageRepository()


def _make_event_producer() -> UserEventProducer:
    return UserEventProducer()


class LoginView(APIView):
    """POST /login — authenticates a user and returns a token pair."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Handles login requests."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = LoginUseCase(user_repository=_make_user_repository())
        result = use_case.execute(LoginDTO(**serializer.validated_data))

        return Response(TokenPairSerializer(result).data, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """POST /registration — creates a new user account."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Handles registration requests."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = RegisterUserUseCase(
            user_repository=_make_user_repository(),
            profile_image_repository=_make_profile_image_repository(),
            event_producer=_make_event_producer(),
        )
        result = use_case.execute(
            RegisterUserDTO(
                username=data["username"],
                email=data["email"],
                password=data["password"],
                profile_image_id=data.get("profile_image"),
            )
        )

        return Response(UserResponseSerializer(result).data, status=status.HTTP_201_CREATED)


class RefreshTokenView(APIView):
    """POST /refresh — issues a new access token."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Handles token refresh requests."""
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            use_case = RefreshTokenUseCase()
            new_access_token = use_case.execute(serializer.validated_data["refresh_token"])
        except TokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"access_token": new_access_token}, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    """GET /users/{user_id} — retrieves a user's public profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, user_id: uuid.UUID) -> Response:
        """Handles user profile retrieval."""
        use_case = GetUserUseCase(user_repository=_make_user_repository())
        result = use_case.execute(user_id)
        return Response(UserResponseSerializer(result).data, status=status.HTTP_200_OK)


class TokenVerifyView(APIView):
    """GET /verify — used by Traefik ForwardAuth middleware.

    Validates the Bearer token in the Authorization header.
    On success returns 200 with X-User-Id and X-Username headers.
    Traefik injects these into the forwarded request to downstream services.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Validates the JWT and returns identity headers."""
        response = Response(status=status.HTTP_200_OK)
        response["X-User-Id"] = str(request.user.id)
        response["X-Username"] = request.user.username
        return response
