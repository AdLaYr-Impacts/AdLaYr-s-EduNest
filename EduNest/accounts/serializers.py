from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import Users

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['school'] = str(user.school.uuid) if user.school else None

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = self.user.uuid
        data['role'] = self.user.role
        data['school'] = self.user.school.uuid if self.user.school else None
        data['is_active'] = self.user.is_active
        data['is_deleted'] = self.user.is_deleted

        return data

class SchoolAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Users
        fields = [
            'id', 'uuid', 'username', 'first_name', 'last_name', 
            'email', 'phone_number', 'password', 'confirm_password',
            'is_active'
        ]

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        errors = {}

        if not self.instance:
            if not password:
                errors["password"] = "This field is required."
            if not confirm_password:
                errors["confirm_password"] = "This field is required."

        if password or confirm_password:
            if password != confirm_password:
                errors["password"] = "Password fields didn't match."
        
        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = Users.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            validated_data.pop('confirm_password', None)
            instance.set_password(password)
        return super().update(instance, validated_data)