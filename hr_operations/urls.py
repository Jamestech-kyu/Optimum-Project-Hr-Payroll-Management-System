from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"performance-reviews", views.PerformanceReviewViewSet, basename="performance-review")
router.register(r"performance-goals", views.PerformanceGoalViewSet, basename="performance-goal")
router.register(r"disciplinary-cases", views.DisciplinaryCaseViewSet, basename="disciplinary-case")
router.register(r"announcements", views.AnnouncementViewSet, basename="announcement")
router.register(r"trainings", views.TrainingViewSet, basename="training")
router.register(r"training-enrollments", views.TrainingEnrollmentViewSet, basename="training-enrollment")

urlpatterns = [
    path("", include(router.urls)),
    # Dashboard endpoints
    path('dashboard/executive/', views.executive_dashboard, name='executive-dashboard'),
    path('dashboard/hr/', views.hr_dashboard, name='hr-dashboard'),
    path('dashboard/branch/<str:branch_id>/', views.branch_dashboard, name='branch-dashboard'),
]