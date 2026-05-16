from django.conf import settings
from django.db import models


class Prediction(models.Model):
    """Stores a readmission prediction result for a patient."""
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    # Raw input data sent to the ML service (JSON)
    input_data  = models.JSONField()
    # Results from FastAPI
    prediction  = models.BooleanField()           # True = high risk
    probability = models.FloatField()             # 0.0 – 1.0
    shap_values = models.JSONField(null=True, blank=True)  # [{feature, value}, ...]
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        risk = 'High Risk' if self.prediction else 'Low Risk'
        return f'{self.user.username} — {risk} ({self.probability:.2%}) @ {self.created_at:%Y-%m-%d}'


class Appointment(models.Model):
    """A patient books an appointment with a doctor."""
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    patient    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments'
    )
    doctor     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_appointments'
    )
    prediction = models.ForeignKey(
        Prediction,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='appointments'
    )
    date       = models.DateField()
    time       = models.TimeField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f'{self.patient.username} → Dr. {self.doctor.full_name or self.doctor.username} on {self.date} {self.time}'


class Article(models.Model):
    """A blog article written by a doctor."""
    author    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles'
    )
    title     = models.CharField(max_length=255)
    content   = models.TextField()
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def upvotes(self):
        # Use annotated value if available (avoids extra query), else fallback
        if hasattr(self, '_upvotes'):
            return self._upvotes
        return self.votes.filter(direction=1).count()

    @upvotes.setter
    def upvotes(self, value):
        self._upvotes = value

    @property
    def downvotes(self):
        # Use annotated value if available (avoids extra query), else fallback
        if hasattr(self, '_downvotes'):
            return self._downvotes
        return self.votes.filter(direction=-1).count()

    @downvotes.setter
    def downvotes(self, value):
        self._downvotes = value


class Vote(models.Model):
    """A patient's up/down vote on an article."""
    DIRECTION_CHOICES = [(1, 'Upvote'), (-1, 'Downvote')]

    user      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    article   = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    direction = models.SmallIntegerField(choices=DIRECTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'article')   # one vote per user per article

    def __str__(self):
        label = 'Up' if self.direction == 1 else 'Down'
        return f'{self.user.username} {label}voted "{self.article.title}"'
