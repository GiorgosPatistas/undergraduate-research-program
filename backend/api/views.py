import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Prediction, Appointment, Article, Vote
from .permissions import IsDoctor, IsPatient
from .serializers import (
    PatientDataSerializer,
    PredictionSerializer,
    AppointmentSerializer,
    ArticleSerializer,
    VoteSerializer,
)

User = get_user_model()


# ── Prediction ─────────────────────────────────────────────────────────────────

class PredictView(APIView):
    """
    Receives patient data from Vue, forwards to FastAPI ML service,
    saves the result, and returns it to the frontend.
    Only patients may call this endpoint.
    """
    permission_classes = [IsPatient]

    def post(self, request):
        # ── Validate input before calling FastAPI ──────────────────
        input_serializer = PatientDataSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        patient_data = input_serializer.validated_data

        # ── Forward to FastAPI ──────────────────────────────────────
        try:
            ml_response = requests.post(
                f"{settings.ML_SERVICE_URL}/inference/",
                json=patient_data,
                headers={'X-Internal-Token': settings.ML_SERVICE_SECRET_KEY},
                timeout=30
            )
            ml_response.raise_for_status()
        except requests.exceptions.ConnectionError:
            return Response(
                {'detail': 'ML service is unavailable. Please try again later.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except requests.exceptions.Timeout:
            return Response(
                {'detail': 'ML service timed out. Please try again.'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {'detail': f'ML service error: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        result = ml_response.json()

        # ── Save to database ────────────────────────────────────────
        prediction = Prediction.objects.create(
            user        = request.user,
            input_data  = patient_data,
            prediction  = result.get('prediction', False),
            probability = result.get('probability', 0.0),
            shap_values = result.get('shap_values'),
        )

        serializer = PredictionSerializer(prediction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PredictionListView(APIView):
    """GET /api/predictions/ — returns the logged-in patient's prediction history."""
    permission_classes = [IsPatient]

    def get(self, request):
        predictions = Prediction.objects.filter(user=request.user)
        serializer = PredictionSerializer(predictions, many=True)
        return Response(serializer.data)


# ── Appointments ───────────────────────────────────────────────────────────────

class AppointmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Doctor → sees all appointments where they are the doctor.
        Patient → sees all appointments they have booked.
        """
        if request.user.is_doctor:
            qs = Appointment.objects.filter(doctor=request.user).select_related(
                'patient', 'doctor', 'prediction'
            )
        else:
            qs = Appointment.objects.filter(patient=request.user).select_related(
                'patient', 'doctor', 'prediction'
            )
        serializer = AppointmentSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Patient books a new appointment."""
        self.permission_classes = [IsPatient]
        self.check_permissions(request)
        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentStatusView(APIView):
    """
    PATCH /appointments/<pk>/status/   { "status": "confirmed"|"cancelled" }
    Doctor can confirm or cancel their own appointments.
    Patient can only cancel their own appointments.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response({'detail': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in ('confirmed', 'cancelled'):
            return Response(
                {'detail': 'status must be "confirmed" or "cancelled".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.is_doctor:
            if appointment.doctor != request.user:
                return Response({'detail': 'Not your appointment.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            if appointment.patient != request.user:
                return Response({'detail': 'Not your appointment.'}, status=status.HTTP_403_FORBIDDEN)
            if new_status == 'confirmed':
                return Response(
                    {'detail': 'Patients cannot confirm appointments.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        appointment.status = new_status
        appointment.save()
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data)


# ── Blog ───────────────────────────────────────────────────────────────────────

class ArticleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        articles = (
            Article.objects
            .annotate(
                _upvotes=Count('votes', filter=Q(votes__direction=1)),
                _downvotes=Count('votes', filter=Q(votes__direction=-1)),
            )
            .order_by('-created_at')
        )
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(articles, request)
        serializer = ArticleSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """Only doctors can publish articles."""
        self.permission_classes = [IsDoctor]
        self.check_permissions(request)
        serializer = ArticleSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ArticleVoteView(APIView):
    """
    Manage a patient's vote on an article.

    POST   /blog/<id>/vote/  {"direction": 1|-1}  → cast a new vote (201)
    PATCH  /blog/<id>/vote/  {"direction": 1|-1}  → change existing vote (200)
    DELETE /blog/<id>/vote/                        → remove vote (204)
    """
    permission_classes = [IsPatient]

    def _get_article(self, pk):
        try:
            return Article.objects.get(pk=pk)
        except Article.DoesNotExist:
            return None

    def _validate_direction(self, request):
        direction = request.data.get('direction')
        if direction not in (1, -1):
            return None, Response(
                {'detail': 'direction must be 1 (upvote) or -1 (downvote).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return direction, None

    def post(self, request, pk):
        """Cast a new vote. Returns 409 if the user already voted."""
        article = self._get_article(pk)
        if not article:
            return Response({'detail': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)

        direction, err = self._validate_direction(request)
        if err:
            return err

        _, created = Vote.objects.get_or_create(
            user=request.user,
            article=article,
            defaults={'direction': direction}
        )

        if not created:
            return Response(
                {'detail': 'You have already voted. Use PATCH to change your vote.'},
                status=status.HTTP_409_CONFLICT
            )

        serializer = ArticleSerializer(article, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, pk):
        """Change an existing vote direction. Returns 404 if no vote exists yet."""
        article = self._get_article(pk)
        if not article:
            return Response({'detail': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)

        direction, err = self._validate_direction(request)
        if err:
            return err

        try:
            vote = Vote.objects.get(user=request.user, article=article)
        except Vote.DoesNotExist:
            return Response(
                {'detail': 'No vote found. Use POST to cast a vote first.'},
                status=status.HTTP_404_NOT_FOUND
            )

        vote.direction = direction
        vote.save()

        serializer = ArticleSerializer(article, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, pk):
        """Remove an existing vote. Returns 204 No Content."""
        article = self._get_article(pk)
        if not article:
            return Response({'detail': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = Vote.objects.filter(user=request.user, article=article).delete()
        if not deleted:
            return Response(
                {'detail': 'No vote found to remove.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
