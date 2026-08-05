from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"branch-tasks", views.BranchTaskViewSet, basename="branch-task")
router.register(r"employee-notes", views.EmployeeNoteViewSet, basename="employee-note")
router.register(r"performance-cycles", views.PerformanceCycleViewSet, basename="performance-cycle")
router.register(r"performance-reviews", views.PerformanceReviewViewSet, basename="performance-review")
router.register(r"performance-goals", views.PerformanceGoalViewSet, basename="performance-goal")
router.register(r"disciplinary-cases", views.DisciplinaryCaseViewSet, basename="disciplinary-case")
router.register(r"announcements", views.AnnouncementViewSet, basename="announcement")
router.register(r"trainings", views.TrainingViewSet, basename="training")
router.register(r"training-enrollments", views.TrainingEnrollmentViewSet, basename="training-enrollment")
router.register(r"offboarding-cases", views.OffboardingCaseViewSet, basename="offboarding-case")
router.register(r"offboarding-checklist-items", views.OffboardingChecklistItemViewSet, basename="offboarding-checklist-item")
router.register(r"offboarding-exit-interviews", views.OffboardingExitInterviewViewSet, basename="offboarding-exit-interview")
router.register(r"offboarding-final-settlements", views.OffboardingFinalSettlementViewSet, basename="offboarding-final-settlement")

urlpatterns = [
    path("", include(router.urls)),
    # Dashboard endpoints
    path('dashboard/executive/', views.executive_dashboard, name='executive-dashboard'),
    path('dashboard/hr/', views.hr_dashboard, name='hr-dashboard'),
    path('dashboard/branch/<str:branch_id>/', views.branch_dashboard, name='branch-dashboard'),
]
