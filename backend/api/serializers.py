from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Prediction, Appointment, Article, Vote

User = get_user_model()


# ── ML Input Validation ────────────────────────────────────────────────────────

AGE_CHOICES  = [
    '[0-10)', '[10-20)', '[20-30)', '[30-40)', '[40-50)',
    '[50-60)', '[60-70)', '[70-80)', '[80-90)', '[90-100)',
]
GENDER_CHOICES  = ['Male', 'Female', 'Unknown/Invalid']
RACE_CHOICES    = ['Caucasian', 'AfricanAmerican', 'Hispanic', 'Asian', 'Other']
DIAG_CHOICES    = ['diabetes', 'circulatory', 'respiratory', 'digestive',
                   'genitourinary', 'musculoskeletal', 'injury', 'neoplasms',
                   'external', 'other']
A1C_CHOICES     = ['None', 'Norm', '>7', '>8']
GLU_CHOICES     = ['None', 'Norm', '>200', '>300']
MED_CHOICES     = ['No', 'Steady', 'Up', 'Down']
YES_NO_CHOICES  = ['Yes', 'No']
CHANGE_CHOICES  = ['Ch', 'No']


class PatientDataSerializer(serializers.Serializer):
    """
    Validates clinical input before forwarding to the FastAPI ML service.
    Mirrors the PatientData Pydantic schema in ml_service/main.py.
    Returns 400 immediately if any field is invalid, without ever calling FastAPI.
    """
    # Demographics
    age    = serializers.ChoiceField(choices=AGE_CHOICES,    default='[50-60)')
    gender = serializers.ChoiceField(choices=GENDER_CHOICES, default='Female')
    race   = serializers.ChoiceField(choices=RACE_CHOICES,   default='Caucasian')

    # Admission details
    time_in_hospital   = serializers.IntegerField(min_value=1,  max_value=14,  default=3)
    num_lab_procedures = serializers.IntegerField(min_value=0,  max_value=132, default=44)
    num_procedures     = serializers.IntegerField(min_value=0,  max_value=6,   default=1)
    num_medications    = serializers.IntegerField(min_value=0,  max_value=81,  default=16)
    number_outpatient  = serializers.IntegerField(min_value=0,                 default=0)
    number_inpatient   = serializers.IntegerField(min_value=0,                 default=0)
    number_emergency   = serializers.IntegerField(min_value=0,                 default=0)
    number_diagnoses   = serializers.IntegerField(min_value=1,  max_value=16,  default=9)

    # Diagnosis categories (ICD-9 already grouped — matches map_diag() in notebook)
    diag_1_cat = serializers.ChoiceField(choices=DIAG_CHOICES, default='other')
    diag_2_cat = serializers.ChoiceField(choices=DIAG_CHOICES, default='other')
    diag_3_cat = serializers.ChoiceField(choices=DIAG_CHOICES, default='other')

    # Lab results
    A1Cresult     = serializers.ChoiceField(choices=A1C_CHOICES, default='None')
    max_glu_serum = serializers.ChoiceField(choices=GLU_CHOICES, default='None')

    # Medications
    diabetesMed   = serializers.ChoiceField(choices=YES_NO_CHOICES, default='Yes')
    change        = serializers.ChoiceField(choices=CHANGE_CHOICES, default='No')
    insulin       = serializers.ChoiceField(choices=MED_CHOICES,    default='Steady')
    metformin     = serializers.ChoiceField(choices=MED_CHOICES,    default='No')
    repaglinide   = serializers.ChoiceField(choices=MED_CHOICES,    default='No')
    nateglinide   = serializers.ChoiceField(choices=MED_CHOICES,    default='No')
    chlorpropamide= serializers.ChoiceField(choices=MED_CHOICES,    default='No')
    glimepiride   = serializers.ChoiceField(choices=MED_CHOICES,    default='No')
    glipizide     = serializers.ChoiceField(choices=MED_CHOICES,    default='No')
    glyburide     = serializers.ChoiceField(choices=MED_CHOICES,    default='No')
    pioglitazone  = serializers.ChoiceField(choices=MED_CHOICES,    default='No')
    rosiglitazone = serializers.ChoiceField(choices=MED_CHOICES,    default='No')
    acarbose      = serializers.ChoiceField(choices=MED_CHOICES,    default='No')

    # Administrative data availability flags
    has_weight    = serializers.IntegerField(min_value=0, max_value=1, default=0)
    has_specialty = serializers.IntegerField(min_value=0, max_value=1, default=0)
    has_payer     = serializers.IntegerField(min_value=0, max_value=1, default=0)


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Prediction
        fields = ('id', 'prediction', 'probability', 'shap_values', 'created_at')
        read_only_fields = fields


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name  = serializers.CharField(source='patient.username',  read_only=True)
    patient_email = serializers.EmailField(source='patient.email',    read_only=True)
    doctor_name   = serializers.CharField(source='doctor.full_name',  read_only=True)
    prediction    = PredictionSerializer(read_only=True)
    prediction_id = serializers.PrimaryKeyRelatedField(
        queryset=Prediction.objects.all(), source='prediction',
        write_only=True, required=False, allow_null=True
    )
    doctor_id     = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='doctor'),
        source='doctor', write_only=True
    )

    class Meta:
        model  = Appointment
        fields = (
            'id', 'patient_name', 'patient_email',
            'doctor_id', 'doctor_name',
            'prediction', 'prediction_id',
            'date', 'time', 'status', 'created_at'
        )
        read_only_fields = ('id', 'patient_name', 'patient_email', 'doctor_name', 'prediction', 'status', 'created_at')


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Vote
        fields = ('direction',)


class ArticleSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    upvotes     = serializers.IntegerField(read_only=True)
    downvotes   = serializers.IntegerField(read_only=True)
    user_vote   = serializers.SerializerMethodField()

    class Meta:
        model  = Article
        fields = (
            'id', 'title', 'content', 'image_url',
            'author_name', 'upvotes', 'downvotes',
            'user_vote', 'created_at'
        )
        read_only_fields = ('id', 'author_name', 'upvotes', 'downvotes', 'user_vote', 'created_at')

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        vote = obj.votes.filter(user=request.user).first()
        return vote.direction if vote else None
