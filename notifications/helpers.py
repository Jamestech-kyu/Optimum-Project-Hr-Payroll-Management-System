from .services import create_notification


def notify_leave_request(user, leave):
    return create_notification(
        recipient=user,
        title="New Leave Request",
        message=f"Leave request #{leave.id} has been submitted.",
        notification_type="LEAVE",
        related_object=leave,
    )


def notify_leave_approved(user, leave):
    return create_notification(
        recipient=user,
        title="Leave Approved",
        message="Your leave request has been approved.",
        notification_type="LEAVE",
        related_object=leave,
    )


def notify_payroll_generated(user, payroll):
    return create_notification(
        recipient=user,
        title="Payroll Generated",
        message="Your payroll has been processed.",
        notification_type="PAYROLL",
        related_object=payroll,
    )


def notify_payslip_ready(user, payslip):
    return create_notification(
        recipient=user,
        title="Payslip Available",
        message="Your payslip is now available.",
        notification_type="PAYSLIP",
        related_object=payslip,
    )


def notify_contract_expiring(user, contract):
    return create_notification(
        recipient=user,
        title="Contract Expiring",
        message="Your employment contract is nearing expiry.",
        notification_type="CONTRACT",
        priority="HIGH",
        related_object=contract,
    )


def notify_training_assigned(user, recommendation):
    return create_notification(
        recipient=user,
        title="Training Assigned",
        message="A new training course has been recommended for you.",
        notification_type="TRAINING",
        related_object=recommendation,
    )


def notify_certificate_issued(user, certificate):
    return create_notification(
        recipient=user,
        title="Training Certificate",
        message="Congratulations! Your training certificate has been issued.",
        notification_type="TRAINING",
        related_object=certificate,
    )


def notify_performance_review(user, review):
    return create_notification(
        recipient=user,
        title="Performance Review",
        message="A new performance review has been assigned.",
        notification_type="PERFORMANCE",
        related_object=review,
    )
