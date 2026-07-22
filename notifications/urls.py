from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    NotificationBroadcastViewSet,
    NotificationPreferenceView,
    NotificationViewSet,
)

router = DefaultRouter()

router.register(
    "notifications",
    NotificationViewSet,
    basename="notifications",
)

router.register(
    "broadcasts",
    NotificationBroadcastViewSet,
)

urlpatterns = [
    path(
        "preferences/",
        NotificationPreferenceView.as_view(),
    ),
    path(
        "",
        include(router.urls),
    ),
]
