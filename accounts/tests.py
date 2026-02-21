from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile
from hospitals.models import Hospital


class UserProfileModelTest(TestCase):
    """Test cases for UserProfile model"""
    
    def setUp(self):
        self.hospital = Hospital.objects.create(name="Test Hospital")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
    
    def test_create_user_profile(self):
        """Test creating a user profile"""
        profile = UserProfile.objects.create(
            user=self.user,
            hospital=self.hospital,
            full_name="Test User"
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.hospital, self.hospital)
        self.assertEqual(profile.full_name, "Test User")
        self.assertIsNotNone(profile.created_at)
    
    def test_user_profile_string_representation(self):
        """Test string representation of user profile"""
        profile = UserProfile.objects.create(
            user=self.user,
            hospital=self.hospital,
            full_name="Test User"
        )
        
        expected = f"Test User - {self.hospital.name}"
        self.assertEqual(str(profile), expected)
    
    def test_user_profile_one_to_one_relationship(self):
        """Test that user can only have one profile"""
        UserProfile.objects.create(
            user=self.user,
            hospital=self.hospital,
            full_name="Test User"
        )
        
        # Trying to create another profile for the same user should fail
        with self.assertRaises(Exception):
            UserProfile.objects.create(
                user=self.user,
                hospital=self.hospital,
                full_name="Another Profile"
            )


class RegistrationAPITest(APITestCase):
    """Test cases for registration endpoint"""
    
    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.valid_payload = {
            'hospital_name': 'General Hospital',
            'full_name': 'Dr. Jane Smith',
            'email': 'jane@hospital.com',
            'password': 'securepass123'
        }
    
    def test_successful_registration(self):
        """Test successful user registration"""
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Registration successful')
        self.assertEqual(response.data['hospital'], 'General Hospital')
        self.assertEqual(response.data['email'], 'jane@hospital.com')
        self.assertEqual(response.data['full_name'], 'Dr. Jane Smith')
        self.assertTrue(response.data['is_new_hospital'])
        
        # Verify user was created
        self.assertTrue(User.objects.filter(email='jane@hospital.com').exists())
        
        # Verify hospital was created
        self.assertTrue(Hospital.objects.filter(name='General Hospital').exists())
        
        # Verify profile was created
        user = User.objects.get(email='jane@hospital.com')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
    
    def test_registration_creates_hospital_once(self):
        """Test that hospital is created only once for multiple registrations"""
        # First registration
        response1 = self.client.post(
            self.register_url,
            self.valid_payload,
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response1.data['is_new_hospital'])
        
        # Second registration with same hospital
        payload2 = {
            'hospital_name': 'General Hospital',
            'full_name': 'Dr. John Doe',
            'email': 'john@hospital.com',
            'password': 'securepass456'
        }
        response2 = self.client.post(
            self.register_url,
            payload2,
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response2.data['is_new_hospital'])
        
        # Verify only one hospital exists
        self.assertEqual(Hospital.objects.filter(name='General Hospital').count(), 1)
        
        # Verify both users belong to same hospital
        hospital = Hospital.objects.get(name='General Hospital')
        self.assertEqual(hospital.staff.count(), 2)
    
    def test_registration_with_duplicate_email(self):
        """Test registration fails with duplicate email"""
        # First registration
        self.client.post(self.register_url, self.valid_payload, format='json')
        
        # Try to register again with same email
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_registration_missing_fields(self):
        """Test registration fails with missing required fields"""
        incomplete_payloads = [
            {'full_name': 'Test', 'email': 'test@test.com', 'password': 'pass123'},
            {'hospital_name': 'Hospital', 'email': 'test@test.com', 'password': 'pass123'},
            {'hospital_name': 'Hospital', 'full_name': 'Test', 'password': 'pass123'},
            {'hospital_name': 'Hospital', 'full_name': 'Test', 'email': 'test@test.com'},
        ]
        
        for payload in incomplete_payloads:
            response = self.client.post(
                self.register_url,
                payload,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_password_too_short(self):
        """Test registration fails with short password"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['password'] = 'short'
        
        response = self.client.post(
            self.register_url,
            invalid_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_registration_invalid_email(self):
        """Test registration fails with invalid email"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['email'] = 'not-an-email'
        
        response = self.client.post(
            self.register_url,
            invalid_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_username_generation_from_email(self):
        """Test that username is generated from email"""
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email='jane@hospital.com')
        self.assertEqual(user.username, 'jane')
    
    def test_username_conflict_handling(self):
        """Test that username conflicts are handled with counter"""
        # Create first user
        User.objects.create_user(
            username='jane',
            email='existing@example.com',
            password='pass123'
        )
        
        # Register new user with email that would create same username
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that new user got a different username
        user = User.objects.get(email='jane@hospital.com')
        self.assertIn('jane', user.username)
        self.assertNotEqual(user.username, 'jane')


class LoginAPITest(APITestCase):
    """Test cases for login endpoint"""
    
    def setUp(self):
        self.login_url = '/api/auth/login/'
        self.register_url = '/api/auth/register/'
        
        # Create a test hospital and user
        self.hospital = Hospital.objects.create(name='Test Hospital')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@hospital.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            hospital=self.hospital,
            full_name='Dr. Test User'
        )
    
    def test_successful_login(self):
        """Test successful login with email and password"""
        payload = {
            'email': 'test@hospital.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Login successful')
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIsNotNone(response.data['access'])
        self.assertIsNotNone(response.data['refresh'])
        
        # Verify user data in response
        self.assertEqual(response.data['user']['email'], 'test@hospital.com')
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['full_name'], 'Dr. Test User')
        self.assertEqual(response.data['user']['hospital'], 'Test Hospital')
        self.assertEqual(response.data['user']['id'], self.user.id)
    
    def test_login_creates_jwt_tokens(self):
        """Test that login creates JWT access and refresh tokens"""
        payload = {
            'email': 'test@hospital.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify JWT tokens were created
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Verify tokens are not empty
        self.assertTrue(len(response.data['access']) > 0)
        self.assertTrue(len(response.data['refresh']) > 0)
    
    def test_login_returns_new_tokens(self):
        """Test that multiple logins return new JWT tokens"""
        payload = {
            'email': 'test@hospital.com',
            'password': 'testpass123'
        }
        
        # First login
        response1 = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        access1 = response1.data['access']
        refresh1 = response1.data['refresh']
        
        # Second login
        response2 = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        access2 = response2.data['access']
        refresh2 = response2.data['refresh']
        
        # JWT tokens should be different each time
        self.assertNotEqual(access1, access2)
        self.assertNotEqual(refresh1, refresh2)
    
    def test_login_with_invalid_email(self):
        """Test login fails with non-existent email"""
        payload = {
            'email': 'nonexistent@hospital.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_login_with_wrong_password(self):
        """Test login fails with incorrect password"""
        payload = {
            'email': 'test@hospital.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_login_with_missing_email(self):
        """Test login fails when email is missing"""
        payload = {
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_login_with_missing_password(self):
        """Test login fails when password is missing"""
        payload = {
            'email': 'test@hospital.com'
        }
        
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_login_with_empty_credentials(self):
        """Test login fails with empty email and password"""
        payload = {
            'email': '',
            'password': ''
        }
        
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_with_invalid_email_format(self):
        """Test login fails with invalid email format"""
        payload = {
            'email': 'not-an-email',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_login_with_inactive_user(self):
        """Test login fails for inactive user account"""
        # Deactivate user
        self.user.is_active = False
        self.user.save()
        
        payload = {
            'email': 'test@hospital.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_login_after_registration(self):
        """Test that user can login immediately after registration"""
        # Register new user
        register_payload = {
            'hospital_name': 'New Hospital',
            'full_name': 'Dr. New User',
            'email': 'newuser@hospital.com',
            'password': 'newpass123'
        }
        
        register_response = self.client.post(
            self.register_url,
            register_payload,
            format='json'
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        
        # Login with new credentials
        login_payload = {
            'email': 'newuser@hospital.com',
            'password': 'newpass123'
        }
        
        login_response = self.client.post(
            self.login_url,
            login_payload,
            format='json'
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data['message'], 'Login successful')
        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)
        self.assertEqual(login_response.data['user']['email'], 'newuser@hospital.com')
        self.assertEqual(login_response.data['user']['full_name'], 'Dr. New User')
        self.assertEqual(login_response.data['user']['hospital'], 'New Hospital')
    
    def test_jwt_token_can_be_used_for_authentication(self):
        """Test that the returned JWT token can be used for authenticated requests"""
        # Login to get JWT token
        payload = {
            'email': 'test@hospital.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
        
        access_token = response.data['access']
        
        # Use JWT token to make authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Verify the token format is correct (JWT tokens have 3 parts separated by dots)
        self.assertEqual(len(access_token.split('.')), 3)
