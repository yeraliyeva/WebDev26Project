"""Django ORM models — infrastructure concern only."""

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class ProfileImage(models.Model):
    """Predefined avatar images managed by admins."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to="profile_images/")

    class Meta:
        db_table = "profile_images"

    def __str__(self) -> str:
        return str(self.id)

    @property
    def image_url(self) -> str:
        """Returns the absolute URL for the stored image."""
        if self.image:
             return self.image.url
        return ""


class UserManager(BaseUserManager):
    """Custom manager for the User model."""

    def create_user(self, username: str, email: str, password: str, **extra) -> "User":
        """Creates and saves a standard user."""
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username: str, email: str, password: str, **extra) -> "User":
        """Creates and saves a superuser."""
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(username, email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Application user account."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    profile = models.ForeignKey(
        ProfileImage,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "users"

    def __str__(self) -> str:
        return self.username
