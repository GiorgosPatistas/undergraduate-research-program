"""
Tests for the api app.
Covers: predictions (mocked ML service), appointments, articles, votes, permissions.
"""

from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Prediction, Appointment, Article, Vote

User = get_user_model()


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_patient(username='patient1', password='Pass1234!'):
    return User.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com', role='patient'
    )

def make_doctor(username='doctor1', password='Pass1234!'):
    return User.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com',
        role='doctor', specialty='Endocrinologist', full_name='Dr. Test'
    )

def auth_header(user):
    token = RefreshToken.for_user(user).access_token
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

VALID_PATIENT_DATA = {
    'age': '[50-60)', 'gender': 'Female', 'race': 'Caucasian',
    'time_in_hospital': 5, 'num_lab_procedures': 40,
    'num_procedures': 1, 'num_medications': 14,
    'number_outpatient': 0, 'number_inpatient': 1,
    'number_emergency': 0, 'number_diagnoses': 8,
    'diag_1_cat': 'circulatory', 'diag_2_cat': 'diabetes', 'diag_3_cat': 'other',
    'A1Cresult': 'None', 'max_glu_serum': 'None',
    'diabetesMed': 'Yes', 'change': 'No', 'insulin': 'Steady',
    'metformin': 'No', 'repaglinide': 'No', 'nateglinide': 'No',
    'chlorpropamide': 'No', 'glimepiride': 'No', 'glipizide': 'No',
    'glyburide': 'No', 'pioglitazone': 'No', 'rosiglitazone': 'No',
    'acarbose': 'No',
}

ML_SUCCESS_RESPONSE = {
    'prediction': True,
    'probability': 0.72,
    'shap_values': [{'feature': 'number_inpatient', 'value': 0.45}],
}


# ── Predictions ────────────────────────────────────────────────────────────────

class PredictViewTests(APITestCase):

    def setUp(self):
        self.url = reverse('predict')
        self.patient = make_patient()
        self.doctor  = make_doctor()

    @patch('api.views.requests.post')
    def test_patient_can_make_prediction(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: ML_SUCCESS_RESPONSE,
            raise_for_status=lambda: None,
        )
        res = self.client.post(self.url, VALID_PATIENT_DATA, format='json', **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('prediction', res.data)
        self.assertIn('probability', res.data)
        self.assertEqual(Prediction.objects.count(), 1)

    @patch('api.views.requests.post')
    def test_prediction_is_saved_to_database(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: ML_SUCCESS_RESPONSE,
            raise_for_status=lambda: None,
        )
        self.client.post(self.url, VALID_PATIENT_DATA, format='json', **auth_header(self.patient))
        pred = Prediction.objects.first()
        self.assertEqual(pred.user, self.patient)
        self.assertTrue(pred.prediction)
        self.assertAlmostEqual(float(pred.probability), 0.72)

    def test_doctor_cannot_make_prediction(self):
        res = self.client.post(self.url, VALID_PATIENT_DATA, format='json', **auth_header(self.doctor))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_make_prediction(self):
        res = self.client.post(self.url, VALID_PATIENT_DATA, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('django.core.handlers.base.log_response')
    @patch('api.views.requests.post')
    def test_ml_service_unavailable_returns_503(self, mock_post, mock_log):
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError
        res = self.client.post(self.url, VALID_PATIENT_DATA, format='json', **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch('django.core.handlers.base.log_response')
    @patch('api.views.requests.post')
    def test_ml_service_timeout_returns_504(self, mock_post, mock_log):
        import requests as req
        mock_post.side_effect = req.exceptions.Timeout
        res = self.client.post(self.url, VALID_PATIENT_DATA, format='json', **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_504_GATEWAY_TIMEOUT)


class PredictionHistoryTests(APITestCase):

    def setUp(self):
        self.url = reverse('predictions')
        self.patient = make_patient()
        self.other   = make_patient('other')
        Prediction.objects.create(
            user=self.patient, input_data={},
            prediction=True, probability=0.8
        )

    def test_patient_sees_own_predictions_only(self):
        res = self.client.get(self.url, **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_other_patient_sees_empty_list(self):
        res = self.client.get(self.url, **auth_header(self.other))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)


# ── Appointments ───────────────────────────────────────────────────────────────

class AppointmentTests(APITestCase):

    def setUp(self):
        self.url     = reverse('appointments')
        self.patient = make_patient()
        self.doctor  = make_doctor()

    def _book(self, patient=None, doctor=None):
        patient = patient or self.patient
        doctor  = doctor  or self.doctor
        return self.client.post(
            self.url,
            {'doctor_id': doctor.id, 'date': '2026-06-01', 'time': '10:00:00'},
            format='json',
            **auth_header(patient)
        )

    def test_patient_can_book_appointment(self):
        res = self._book()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_doctor_cannot_book_appointment(self):
        res = self.client.post(
            self.url,
            {'doctor_id': self.doctor.id, 'date': '2026-06-01', 'time': '10:00:00'},
            format='json',
            **auth_header(self.doctor)
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_sees_own_appointments(self):
        self._book()
        res = self.client.get(self.url, **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_doctor_sees_their_appointments(self):
        self._book()
        res = self.client.get(self.url, **auth_header(self.doctor))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)


class AppointmentStatusTests(APITestCase):

    def setUp(self):
        self.patient = make_patient()
        self.doctor  = make_doctor()
        self.appt    = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            date='2026-06-01', time='10:00:00', status='pending'
        )
        self.url = reverse('appointment_status', kwargs={'pk': self.appt.pk})

    def test_doctor_can_confirm_appointment(self):
        res = self.client.patch(self.url, {'status': 'confirmed'}, format='json', **auth_header(self.doctor))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.appt.refresh_from_db()
        self.assertEqual(self.appt.status, 'confirmed')

    def test_patient_can_cancel_appointment(self):
        res = self.client.patch(self.url, {'status': 'cancelled'}, format='json', **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.appt.refresh_from_db()
        self.assertEqual(self.appt.status, 'cancelled')

    def test_patient_cannot_confirm_appointment(self):
        res = self.client.patch(self.url, {'status': 'confirmed'}, format='json', **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_status_value_fails(self):
        res = self.client.patch(self.url, {'status': 'invalid'}, format='json', **auth_header(self.doctor))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ── Articles ───────────────────────────────────────────────────────────────────

class ArticleTests(APITestCase):

    def setUp(self):
        self.url     = reverse('blog')
        self.patient = make_patient()
        self.doctor  = make_doctor()

    def test_doctor_can_create_article(self):
        res = self.client.post(
            self.url,
            {'title': 'Diabetes Tips', 'content': 'Some content here.'},
            format='json',
            **auth_header(self.doctor)
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.count(), 1)

    def test_patient_cannot_create_article(self):
        res = self.client.post(
            self.url,
            {'title': 'Fake Article', 'content': 'Some content.'},
            format='json',
            **auth_header(self.patient)
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_list_articles(self):
        Article.objects.create(author=self.doctor, title='Test', content='Content')
        res = self.client.get(self.url, **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)

    def test_unauthenticated_cannot_list_articles(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ── Votes ──────────────────────────────────────────────────────────────────────

class VoteTests(APITestCase):

    def setUp(self):
        self.patient = make_patient()
        self.doctor  = make_doctor()
        self.article = Article.objects.create(
            author=self.doctor, title='Test Article', content='Content'
        )
        self.url = reverse('article_vote', kwargs={'pk': self.article.pk})

    def test_patient_can_upvote_article(self):
        res = self.client.post(self.url, {'direction': 1}, format='json', **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vote.objects.count(), 1)

    def test_patient_can_downvote_article(self):
        res = self.client.post(self.url, {'direction': -1}, format='json', **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_duplicate_vote_returns_409(self):
        self.client.post(self.url, {'direction': 1}, format='json', **auth_header(self.patient))
        res = self.client.post(self.url, {'direction': 1}, format='json', **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_patient_can_change_vote(self):
        self.client.post(self.url, {'direction': 1}, format='json', **auth_header(self.patient))
        res = self.client.patch(self.url, {'direction': -1}, format='json', **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Vote.objects.get(user=self.patient).direction, -1)

    def test_patient_can_delete_vote(self):
        self.client.post(self.url, {'direction': 1}, format='json', **auth_header(self.patient))
        res = self.client.delete(self.url, **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Vote.objects.count(), 0)

    def test_delete_nonexistent_vote_returns_404(self):
        res = self.client.delete(self.url, **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_direction_fails(self):
        res = self.client.post(self.url, {'direction': 99}, format='json', **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
