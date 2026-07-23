from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import RequiredPermission
from audit.mixins import AuditViewSetMixin
from audit.services import log_activity
from audit.utils import get_client_ip

from .models import (
    TrainingAssessment,
    TrainingAttendance,
    TrainingCategory,
    TrainingCertificate,
    TrainingCourse,
    TrainingEnrollment,
    TrainingRecommendation,
    TrainingSession,
)
from .serializers import (
    TrainingAssessmentCreateSerializer,
    TrainingAssessmentSerializer,
    TrainingAttendanceCreateSerializer,
    TrainingAttendanceSerializer,
    TrainingCategorySerializer,
    TrainingCertificateSerializer,
    TrainingCourseSerializer,
    TrainingEnrollmentCreateSerializer,
    TrainingEnrollmentSerializer,
    TrainingRecommendationCreateSerializer,
    TrainingRecommendationSerializer,
    TrainingSessionSerializer,
)
from .services import (
    accept_training_recommendation,
    approve_training_enrollment,
    create_training_recommendation,
    decline_training_recommendation,
    enroll_employee_in_training,
    record_training_assessment,
    record_training_attendance,
    reject_training_enrollment,
)


class TrainingCategoryViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "TRAINING"

    queryset = TrainingCategory.objects.all()
    serializer_class = TrainingCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingCourseViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "TRAINING"

    queryset = TrainingCourse.objects.select_related(
        "category"
    )

    serializer_class = TrainingCourseSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingSessionViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "TRAINING"

    queryset = TrainingSession.objects.select_related(
        "course",
        "trainer",
    )

    serializer_class = TrainingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingEnrollmentViewSet(
    AuditViewSetMixin,
    viewsets.ReadOnlyModelViewSet,
):
    audit_module = "TRAINING"

    queryset = TrainingEnrollment.objects.select_related(
        "employee",
        "session__course",
    )

    serializer_class = TrainingEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "session__course__title",
        "status",
    ]
    ordering_fields = "__all__"
    ordering = ["-enrolled_at"]
    filterset_fields = [
        "employee",
        "session",
        "session__course",
        "status",
    ]


class TrainingAttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingAttendance.objects.select_related(
        "enrollment__employee",
    )

    serializer_class = TrainingAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingAssessmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingAssessment.objects.select_related(
        "enrollment__employee",
    )

    serializer_class = TrainingAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingCertificateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingCertificate.objects.select_related(
        "enrollment__employee",
    )

    serializer_class = TrainingCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingRecommendation.objects.select_related(
        "employee",
        "recommended_course",
    )

    serializer_class = TrainingRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    request=TrainingEnrollmentCreateSerializer,
    responses={201: TrainingEnrollmentSerializer},
    tags=["Training"],
)
class EnrollEmployeeTrainingView(APIView):
    permission_classes = [
        RequiredPermission("training.enroll")
    ]

    def post(self, request):
        serializer = TrainingEnrollmentCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        enrollment = enroll_employee_in_training(
            employee_id=serializer.validated_data["employee_id"],
            session_id=serializer.validated_data["session_id"],
            enrolled_by=request.user,
        )

        log_activity(
            user=request.user,
            action="ENROLL",
            module="Training",
            description=(
                f"Enrolled employee "
                f"{enrollment.employee.employee_number} "
                f"in training session {enrollment.session_id}."
            ),
            object_id=enrollment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Employee enrolled successfully.",
                "enrollment": TrainingEnrollmentSerializer(
                    enrollment
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ApproveTrainingEnrollmentView(APIView):
    permission_classes = [
        RequiredPermission("training.approve")
    ]

    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(
            TrainingEnrollment.objects.select_related(
                "employee",
                "session",
            ),
            id=enrollment_id,
        )

        enrollment = approve_training_enrollment(
            enrollment=enrollment,
        )

        log_activity(
            user=request.user,
            action="APPROVE",
            module="Training",
            description=f"Approved training enrollment {enrollment.id}.",
            object_id=enrollment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training enrollment approved successfully.",
                "enrollment": TrainingEnrollmentSerializer(
                    enrollment
                ).data,
            }
        )


class RejectTrainingEnrollmentView(APIView):
    permission_classes = [
        RequiredPermission("training.reject")
    ]

    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(
            TrainingEnrollment.objects.select_related(
                "employee",
                "session",
            ),
            id=enrollment_id,
        )

        enrollment = reject_training_enrollment(
            enrollment=enrollment,
        )

        log_activity(
            user=request.user,
            action="REJECT",
            module="Training",
            description=f"Rejected training enrollment {enrollment.id}.",
            object_id=enrollment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training enrollment rejected successfully.",
                "enrollment": TrainingEnrollmentSerializer(
                    enrollment
                ).data,
            }
        )


@extend_schema(
    request=TrainingAttendanceCreateSerializer,
    responses={200: TrainingAttendanceSerializer},
    tags=["Training"],
)
class RecordTrainingAttendanceView(APIView):
    permission_classes = [
        RequiredPermission("training.attendance")
    ]

    def post(self, request):
        serializer = TrainingAttendanceCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        attendance = record_training_attendance(
            enrollment_id=serializer.validated_data["enrollment_id"],
            attendance_status=serializer.validated_data[
                "attendance_status"
            ],
            check_in=serializer.validated_data.get("check_in"),
            check_out=serializer.validated_data.get("check_out"),
        )

        log_activity(
            user=request.user,
            action="ATTENDANCE",
            module="Training",
            description=(
                f"Recorded training attendance "
                f"{attendance.id}."
            ),
            object_id=attendance.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training attendance recorded successfully.",
                "attendance": TrainingAttendanceSerializer(
                    attendance
                ).data,
            }
        )


@extend_schema(
    request=TrainingAssessmentCreateSerializer,
    responses={200: TrainingAssessmentSerializer},
    tags=["Training"],
)
class RecordTrainingAssessmentView(APIView):
    permission_classes = [
        RequiredPermission("training.assessment")
    ]

    def post(self, request):
        serializer = TrainingAssessmentCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        assessment = record_training_assessment(
            enrollment_id=serializer.validated_data["enrollment_id"],
            score=serializer.validated_data["score"],
            remarks=serializer.validated_data.get("remarks", ""),
        )

        log_activity(
            user=request.user,
            action="ASSESSMENT",
            module="Training",
            description=(
                f"Recorded training assessment "
                f"{assessment.id}."
            ),
            object_id=assessment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training assessment recorded successfully.",
                "assessment": TrainingAssessmentSerializer(
                    assessment
                ).data,
            }
        )


@extend_schema(
    request=TrainingRecommendationCreateSerializer,
    responses={201: TrainingRecommendationSerializer},
    tags=["Training"],
)
class RecommendTrainingView(APIView):
    permission_classes = [
        RequiredPermission("training.recommend")
    ]

    def post(self, request):
        serializer = TrainingRecommendationCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        recommendation = create_training_recommendation(
            employee_id=serializer.validated_data["employee_id"],
            performance_review_id=serializer.validated_data[
                "performance_review_id"
            ],
            recommended_course_id=serializer.validated_data[
                "recommended_course_id"
            ],
            reason=serializer.validated_data["reason"],
            recommended_by=request.user,
        )

        log_activity(
            user=request.user,
            action="RECOMMEND",
            module="Training",
            description=(
                f"Recommended training course "
                f"{recommendation.recommended_course_id} "
                f"for employee "
                f"{recommendation.employee.employee_number}."
            ),
            object_id=recommendation.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training recommendation created successfully.",
                "recommendation": TrainingRecommendationSerializer(
                    recommendation
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AcceptTrainingRecommendationView(APIView):
    permission_classes = [
        RequiredPermission("training.view")
    ]

    def post(self, request, recommendation_id):
        recommendation = get_object_or_404(
            TrainingRecommendation.objects.select_related(
                "employee",
                "recommended_course",
            ),
            id=recommendation_id,
        )

        recommendation = accept_training_recommendation(
            recommendation=recommendation,
        )

        log_activity(
            user=request.user,
            action="ACCEPT",
            module="Training",
            description=(
                f"Accepted training recommendation "
                f"{recommendation.id}."
            ),
            object_id=recommendation.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training recommendation accepted successfully.",
                "recommendation": TrainingRecommendationSerializer(
                    recommendation
                ).data,
            }
        )


class DeclineTrainingRecommendationView(APIView):
    permission_classes = [
        RequiredPermission("training.view")
    ]

    def post(self, request, recommendation_id):
        recommendation = get_object_or_404(
            TrainingRecommendation.objects.select_related(
                "employee",
                "recommended_course",
            ),
            id=recommendation_id,
        )

        recommendation = decline_training_recommendation(
            recommendation=recommendation,
        )

        log_activity(
            user=request.user,
            action="DECLINE",
            module="Training",
            description=(
                f"Declined training recommendation "
                f"{recommendation.id}."
            ),
            object_id=recommendation.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training recommendation declined successfully.",
                "recommendation": TrainingRecommendationSerializer(
                    recommendation
                ).data,
            }
        )
