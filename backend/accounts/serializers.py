from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model  = User
        fields = ('username', 'email', 'password', 'role', 'full_name', 'specialty')
        extra_kwargs = {
            'email':     {'required': True},
            'full_name': {'required': False},
            'specialty': {'required': False},
        }

    def validate(self, data):
        # Doctors should provide full_name
        if data.get('role') == 'doctor' and not data.get('full_name'):
            raise serializers.ValidationError({'full_name': 'Full name is required for doctors.'})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username  = validated_data['username'],
            email     = validated_data['email'],
            password  = validated_data['password'],
            role      = validated_data.get('role', 'patient'),
            full_name = validated_data.get('full_name', ''),
            specialty = validated_data.get('specialty', ''),
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ('id', 'username', 'email', 'role', 'full_name', 'specialty')
        read_only_fields = ('id', 'username', 'role')


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password     = serializers.CharField(required=True, validators=[validate_password])

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value


class DoctorListSerializer(serializers.ModelSerializer):
    """Minimal doctor info shown to patients when booking."""
    class Meta:
        model  = User
        fields = ('id', 'username', 'full_name', 'specialty')
