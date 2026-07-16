from django.shortcuts import render

from django.utils import timezone
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    PerformanceReview,
    PerformanceGoal,
    DisciplinaryCase,
    Announcement,
    Training,
    TrainingEnrollment,
)
from .serializers import (
    PerformanceReviewSerializer,
    PerformanceGoalSerializer,
    DisciplinaryCaseSerializer,
    AnnouncementSerializer,
    TrainingSerializer,
    TrainingEnrollmentSerializer,
)


class DjangoFilterBackend:
    def filter_queryset(self, request, queryset, view):
        for field in getattr(view, "filterset_fields", []):
            value = request.query_params.get(field)

            if value not in [None, ""]:
                queryset = queryset.filter(**{field: value})

        return queryset


# =========================================================
# PERFORMANCE API
# =========================================================

class PerformanceReviewViewSet(viewsets.ModelViewSet):
    """
    /api/hr-operations/performance-reviews/               -> list, create
    /api/hr-operations/performance-reviews/{id}/          -> retrieve, update, delete
    /api/hr-operations/performance-reviews/{id}/submit/   -> mark review as SUBMITTED
    Filter with ?employee=<id>&status=DRAFT
    """

    queryset = PerformanceReview.objects.all()
    serializer_class = PerformanceReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["employee", "status"]

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        review = self.get_object()
        review.status = "SUBMITTED"
        review.save()
        return Response(self.get_serializer(review).data)


class PerformanceGoalViewSet(viewsets.ModelViewSet):
    queryset = PerformanceGoal.objects.all()
    serializer_class = PerformanceGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["review", "status"]


# =========================================================
# DISCIPLINARY API
# =========================================================

class DisciplinaryCaseViewSet(viewsets.ModelViewSet):
    """
    Full CRUD as required by the spec.
    Filter with ?employee=<id>&status=OPEN&severity=MAJOR
    """

    queryset = DisciplinaryCase.objects.all()
    serializer_class = DisciplinaryCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["employee", "status", "severity"]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        case = self.get_object()
        case.status = "RESOLVED"
        case.resolution_notes = request.data.get("resolution_notes", case.resolution_notes)
        case.action_taken = request.data.get("action_taken", case.action_taken)
        case.resolved_at = timezone.now()
        case.save()
        return Response(self.get_serializer(case).data)


# =========================================================
# ANNOUNCEMENTS API
# =========================================================

class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    /api/hr-operations/announcements/               -> list, create
    /api/hr-operations/announcements/active/        -> only currently-visible announcements
    """

    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["audience", "is_pinned"]
    search_fields = ["title", "body"]

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)

    @action(detail=False, methods=["get"])
    def active(self, request):
        now = timezone.now()
        qs = self.get_queryset().filter(publish_at__lte=now).exclude(expires_at__lt=now)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


# =========================================================
# TRAINING API
# =========================================================

class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "is_mandatory"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        training = self.get_object()
        employee_id = request.data.get("employee")
        if not employee_id:
            return Response({"employee": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        enrollment, created = TrainingEnrollment.objects.get_or_create(
            training=training, employee_id=employee_id
        )
        return Response(
            TrainingEnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class TrainingEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = TrainingEnrollment.objects.all()
    serializer_class = TrainingEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["training", "employee", "status"]
