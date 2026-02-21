from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import RegistrationSerializer, LoginSerializer
from .models import UserProfile


@swagger_auto_schema(
    method='post',
    operation_description="Register a new hospital staff member. If the hospital doesn't exist, it will be created.",
    operation_summary="Register Hospital Staff",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['hospital_name', 'full_name', 'email', 'password'],
        properties={
            'hospital_name': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Name of the hospital',
                example='General Hospital Lagos'
            ),
            'full_name': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Full name of the staff member',
                example='Dr. Jane Smith'
            ),
            'email': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_EMAIL,
                description='Email address (must be unique)',
                example='jane.smith@hospital.com'
            ),
            'password': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_PASSWORD,
                description='Password (minimum 8 characters)',
                example='securepass123'
            ),
        },
    ),
    responses={
        201: openapi.Response(
            description='Registration successful',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example='Registration successful'),
                    'hospital': openapi.Schema(type=openapi.TYPE_STRING, example='General Hospital Lagos'),
                    'username': openapi.Schema(type=openapi.TYPE_STRING, example='jane'),
                    'email': openapi.Schema(type=openapi.TYPE_STRING, example='jane.smith@hospital.com'),
                    'full_name': openapi.Schema(type=openapi.TYPE_STRING, example='Dr. Jane Smith'),
                    'is_new_hospital': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                },
            ),
        ),
        400: openapi.Response(
            description='Validation errors',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'email': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        example=['Email already registered']
                    ),
                    'password': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        example=['Ensure this field has at least 8 characters.']
                    ),
                },
            ),
        ),
    },
    tags=['Authentication'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register hospital staff."""
    serializer = RegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        result = serializer.save()
        
        return Response({
            'message': 'Registration successful',
            'hospital': result['hospital'].name,
            'username': result['user'].username,
            'email': result['user'].email,
            'full_name': result['profile'].full_name,
            'is_new_hospital': result['is_new_hospital']
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_description="Login with email and password. Returns JWT access and refresh tokens.",
    operation_summary="Login",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email', 'password'],
        properties={
            'email': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_EMAIL,
                description='Email address',
                example='jane.smith@hospital.com'
            ),
            'password': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_PASSWORD,
                description='Password',
                example='securepass123'
            ),
        },
    ),
    responses={
        200: openapi.Response(
            description='Login successful',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example='Login successful'),
                    'access': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGc...'),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGc...'),
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                            'username': openapi.Schema(type=openapi.TYPE_STRING, example='jane'),
                            'email': openapi.Schema(type=openapi.TYPE_STRING, example='jane.smith@hospital.com'),
                            'full_name': openapi.Schema(type=openapi.TYPE_STRING, example='Dr. Jane Smith'),
                            'hospital': openapi.Schema(type=openapi.TYPE_STRING, example='General Hospital Lagos'),
                        },
                    ),
                },
            ),
        ),
        400: openapi.Response(
            description='Validation errors',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'non_field_errors': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        example=['Invalid email or password']
                    ),
                },
            ),
        ),
    },
    tags=['Authentication'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login with email and password."""
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Build user response - handle users without profiles
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        }
        
        # Try to get profile if it exists
        try:
            profile = user.profile
            user_data['full_name'] = profile.full_name
            user_data['hospital'] = profile.hospital.name
            user_data['hospital_id'] = profile.hospital.id
        except UserProfile.DoesNotExist:
            # User has no profile - use basic info
            user_data['full_name'] = user.get_full_name() or user.username
            user_data['hospital'] = None
            user_data['hospital_id'] = None
        
        return Response({
            'message': 'Login successful',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
