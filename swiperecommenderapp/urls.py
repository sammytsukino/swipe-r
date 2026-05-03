from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, reverse_lazy

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("swipe", views.SwipeCandidate.as_view(), name="swipe"),
    path("recommendations", views.RecommendationList.as_view(), name="recommendations"),
    path("history", views.SwipeHistory.as_view(), name="history"),
    path(
        "login",
        LoginView.as_view(
            template_name="swiperecommenderapp/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout",
        LogoutView.as_view(next_page=reverse_lazy("index")),
        name="logout",
    ),
]
