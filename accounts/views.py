from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import RegistrationSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register hospital staff.
    
    Required fields:
    - hospital_name: Name of the hospital
    - full_name: Full name of the staff member
    - email: Email address
    - password: Password (min 8 characters)
    """
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
