from django.urls import path

from .views import LoginView, OnboardingView, RefreshView

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("onboarding/", OnboardingView.as_view(), name="tenant-onboarding"),
]
