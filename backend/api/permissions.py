from rest_framework.permissions import BasePermission


class IsPatient(BasePermission):
    """Allows access only to users with role='patient'."""
    message = 'Only patients are allowed to perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_patient
        )


class IsDoctor(BasePermission):
    """Allows access only to users with role='doctor'."""
    message = 'Only doctors are allowed to perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_doctor
        )
