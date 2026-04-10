"""Data Transfer Objects crossing application boundaries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class RegisterUserDTO:
    """Input data for the user registration use case."""

    username: str
    email: str
    password: str
    profile_image_id: Optional[uuid.UUID]


@dataclass(frozen=True)
class LoginDTO:
    """Input data for the login use case."""

    login: str
    password: str


@dataclass(frozen=True)
class TokenPairDTO:
    """Pair of access and refresh JWT tokens."""

    user_id: uuid.UUID
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class UserResponseDTO:
    """Public-facing user representation."""

    id: uuid.UUID
    username: str
    email: str
    created_at: datetime
    updated_at: datetime
    profile_image_url: Optional[str]
