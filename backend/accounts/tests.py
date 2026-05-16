"""
Tests for the accounts app.
Covers: registration, login, profile (GET/PATCH), password change, doctor list.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_patient(username='patient1', password='Pass1234!'):
    return User.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com', role='patient'
    )

def make_doctor(username='doctor1', password='Pass1234!', specialty='Endocrinologist'):
    return User.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com',
        role='doctor', specialty=specialty, full_name='Dr. Test'
    )

def auth_header(user):
    token = RefreshToken.for_user(user).access_token
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


# ── Registration ───────────────────────────────────────────────────────────────

class RegisterTests(APITestCase):

    def setUp(self):
        self.url = reverse('register')

    def test_patient_registration_succeeds(self):
        data = {
            'username': 'newpatient',
            'email': 'newpatient@test.com',
            'password': 'Pass1234!',
            'role': 'patient',
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newpatient').exists())

    def test_doctor_registration_requires_full_name(self):
        data = {
            'username': 'newdoctor',
            'email': 'newdoctor@test.com',
            'password': 'Pass1234!',
            'role': 'doctor',
            # full_name intentionally missing
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_doctor_registration_with_full_name_succeeds(self):
        data = {
            'username': 'newdoctor',
            'email': 'newdoctor@test.com',
            'password': 'Pass1234!',
            'role': 'doctor',
            'full_name': 'Dr. House',
            'specialty': 'Endocrinologist',
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_duplicate_username_fails(self):
        make_patient('existinguser')
        data = {
            'username': 'existinguser',
            'email': 'other@test.com',
            'password': 'Pass1234!',
            'role': 'patient',
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ── Login ──────────────────────────────────────────────────────────────────────

class LoginTests(APITestCase):

    def setUp(self):
        self.url = reverse('token_obtain_pair')
        self.user = make_patient()

    def test_login_with_correct_credentials_returns_tokens(self):
        res = self.client.post(self.url, {'username': 'patient1', 'password': 'Pass1234!'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_login_with_wrong_password_fails(self):
        res = self.client.post(self.url, {'username': 'patient1', 'password': 'wrongpass'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_cannot_access_protected_endpoint(self):
        url = reverse('me')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ── Profile (GET / PATCH) ──────────────────────────────────────────────────────

class ProfileTests(APITestCase):

    def setUp(self):
        self.url = reverse('me')
        self.patient = make_patient()
        self.doctor  = make_doctor()

    def test_patient_can_get_own_profile(self):
        res = self.client.get(self.url, **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'patient1')
        self.assertEqual(res.data['role'], 'patient')

    def test_doctor_can_get_own_profile(self):
        res = self.client.get(self.url, **auth_header(self.doctor))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['role'], 'doctor')

    def test_user_can_update_email(self):
        res = self.client.patch(
            self.url, {'email': 'updated@test.com'},
            **auth_header(self.patient)
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.email, 'updated@test.com')

    def test_role_is_read_only(self):
        self.client.patch(self.url, {'role': 'doctor'}, **auth_header(self.patient))
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.role, 'patient')


# ── Password Change ────────────────────────────────────────────────────────────

class ChangePasswordTests(APITestCase):

    def setUp(self):
        self.url = reverse('change_password')
        self.patient = make_patient()

    def test_change_password_with_correct_current_password(self):
        data = {'current_password': 'Pass1234!', 'new_password': 'NewPass5678!'}
        res = self.client.post(self.url, data, **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_change_password_with_wrong_current_password_fails(self):
        data = {'current_password': 'WrongPass!', 'new_password': 'NewPass5678!'}
        res = self.client.post(self.url, data, **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_change_password(self):
        data = {'current_password': 'Pass1234!', 'new_password': 'NewPass5678!'}
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ── Doctor List ────────────────────────────────────────────────────────────────

class DoctorListTests(APITestCase):

    def setUp(self):
        self.url = reverse('doctors')
        self.patient = make_patient()
        self.doctor1 = make_doctor('doctor1')
        self.doctor2 = make_doctor('doctor2', specialty='Cardiologist')

    def test_patient_can_see_doctor_list(self):
        res = self.client.get(self.url, **auth_header(self.patient))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_unauthenticated_cannot_see_doctor_list(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
