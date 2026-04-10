"""DRF serializers for request validation and response shaping."""

from __future__ import annotations

import uuid

from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """Validates login request body."""

    login = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.Serializer):
    """Validates registration request body."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    profile_image = serializers.UUIDField(required=False, allow_null=True, default=None)


class RefreshSerializer(serializers.Serializer):
    """Validates token refresh request body."""

    refresh_token = serializers.CharField()


class UserResponseSerializer(serializers.Serializer):
    """Shapes public user profile output."""

    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    profile_image_url = serializers.URLField(allow_null=True)


class TokenPairSerializer(serializers.Serializer):
    """Shapes token pair output."""

    user_id = serializers.UUIDField()
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
