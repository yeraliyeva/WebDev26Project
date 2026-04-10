"""Domain entities — pure Python, no framework dependencies."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ProfileImageEntity:
    """Represents a predefined profile image available for selection."""

    id: uuid.UUID
    image_url: str


@dataclass(frozen=True)
class UserEntity:
    """Core user domain object."""

    id: uuid.UUID
    username: str
    email: str
    password_hash: str
    created_at: datetime
    updated_at: datetime
    profile_image: Optional[ProfileImageEntity] = field(default=None)

    def is_profile_image_set(self) -> bool:
        """Returns whether the user has selected a profile image."""
        return self.profile_image is not None
