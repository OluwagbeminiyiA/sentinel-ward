from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from .models import UserProfile
from hospitals.models import Hospital


class RegistrationSerializer(serializers.Serializer):
    """
    Simple registration requiring only:
    - hospital_name
    - full_name
    - email
    - password
    """
    hospital_name = serializers.CharField(max_length=255)
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        # Get or create hospital
        hospital, created = Hospital.objects.get_or_create(
            name=validated_data['hospital_name']
        )
        
        # Create user with email as username
        username = validated_data['email'].split('@')[0]
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # Create user profile
        profile = UserProfile.objects.create(
            user=user,
            hospital=hospital,
            full_name=validated_data['full_name']
        )
        
        return {
            'user': user,
            'profile': profile,
            'hospital': hospital,
            'is_new_hospital': created
        }


class LoginSerializer(serializers.Serializer):
    """
    Simple login requiring only:
    - email
    - password
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Must include email and password")
        
        # Get user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")
        
        # Authenticate with username and password
        user = authenticate(username=user.username, password=password)
        
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
        
        data['user'] = user
        return data
