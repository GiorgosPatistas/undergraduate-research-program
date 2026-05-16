from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor',  'Doctor'),
    ]

    SPECIALTY_CHOICES = [
        ('General Practitioner', 'General Practitioner'),
        ('Endocrinologist',      'Endocrinologist'),
        ('Cardiologist',         'Cardiologist'),
        ('Internist',            'Internist'),
        ('Nephrologist',         'Nephrologist'),
        ('Diabetologist',        'Diabetologist'),
        ('Other',                'Other'),
    ]

    role      = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    full_name = models.CharField(max_length=150, blank=True)
    specialty = models.CharField(max_length=50, choices=SPECIALTY_CHOICES, blank=True)

    def __str__(self):
        return f'{self.username} ({self.role})'

    @property
    def is_doctor(self):
        return self.role == 'doctor'

    @property
    def is_patient(self):
        return self.role == 'patient'
