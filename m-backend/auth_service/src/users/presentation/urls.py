"""URL routes for the users presentation layer."""

from django.urls import path

from .views import LoginView, RegisterView, RefreshTokenView, UserDetailView, TokenVerifyView

urlpatterns = [
    path("login", LoginView.as_view()),
    path("registration", RegisterView.as_view()),
    path("refresh", RefreshTokenView.as_view()),
    path("users/<uuid:user_id>", UserDetailView.as_view()),
    path("verify", TokenVerifyView.as_view()),
]
