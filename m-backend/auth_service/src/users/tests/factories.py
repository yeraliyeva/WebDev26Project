"""Factory Boy model factories for test data generation."""

import factory
from factory.django import DjangoModelFactory

from users.infrastructure.models import ProfileImage, User


class ProfileImageFactory(DjangoModelFactory):
    """Generates ProfileImage test instances."""

    image = factory.django.ImageField(filename="avatar.png")

    class Meta:
        model = ProfileImage


class UserFactory(DjangoModelFactory):
    """Generates User test instances."""

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "password123")
    profile = None

    class Meta:
        model = User
