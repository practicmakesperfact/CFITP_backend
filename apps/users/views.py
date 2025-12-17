
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema

from .serializers import (
    RegisterSerializer,
    ProfileSerializer,
    UserSerializer,
    LoginSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


# ------------------------------------------------------------
# CUSTOM LOGIN VIEW
# ------------------------------------------------------------
class CustomLoginView(TokenObtainPairView):
    """
    Custom login view that uses our enhanced LoginSerializer
    """
    serializer_class = LoginSerializer


# ------------------------------------------------------------
# USER VIEWSET (Updated to integrate with your existing structure)
# ------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'register':
            return RegisterSerializer
        elif self.action in ['profile', 'me']:
            return ProfileSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Set permissions based on action
        """
        if self.action in ['register', 'login']:
            return [AllowAny()]
        elif self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        else:
            return [IsAuthenticated()]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: ProfileSerializer},
        description="Register a new user (client role only)"
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Public endpoint for client registration only
        """
        import json
        print("=" * 50)
        print("REGISTRATION REQUEST RECEIVED")
        print("=" * 50)
        print("Request data:", json.dumps(request.data, indent=2))
        print("Headers:", dict(request.headers))
        
        serializer = RegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            print("VALIDATION ERRORS:", json.dumps(serializer.errors, indent=2))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = serializer.save()
            print(f"User created successfully: {user.email} (ID: {user.id})")
            
            # Generate tokens for auto-login
            # refresh = RefreshToken.for_user(user)
            
            response_data = {
                'user': ProfileSerializer(user).data,
                # 'refresh': str(refresh),
                # 'access': str(refresh.access_token),
                'message': 'Registration successful! Please login.'
            }
            
            print("Registration successful, returning response")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return Response(
                {"detail": "An error occurred during registration. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @extend_schema(
        responses=ProfileSerializer,
        description="Get or update user profile"
    )
    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def profile(self, request):
        """
        Get or update current user profile
        """
        user = request.user
        
        if request.method == "PATCH":
            # Prevent changing email and role through this endpoint
            if 'email' in request.data or 'role' in request.data:
                return Response(
                    {"error": "Email and role cannot be changed through profile update"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = ProfileSerializer(
                user, 
                data=request.data, 
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
        
        return Response(ProfileSerializer(user).data)

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: {"detail": "Password updated successfully"}}
    )
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """
        Change user password
        """
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": "Wrong password."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({"detail": "Password updated successfully"})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses=UserSerializer(many=True),
        description="Get all staff users"
    )
    @action(detail=False, methods=['get'], url_path='staff')
    def staff_users(self, request):
        """
        Get all staff users
        """
        # Only allow staff, managers, and admins to view staff list
        if request.user.role not in ['staff', 'manager', 'admin']:
            return Response(
                {"detail": "You don't have permission to view staff users."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        staff_users = User.objects.filter(role='staff', is_active=True)
        serializer = self.get_serializer(staff_users, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses=UserSerializer(many=True),
        description="Get all client users"
    )
    @action(detail=False, methods=['get'], url_path='clients')
    def client_users(self, request):
        """
        Get all client users
        """
        # Only allow staff, managers, and admins to view client list
        if request.user.role not in ['staff', 'manager', 'admin']:
            return Response(
                {"detail": "You don't have permission to view client users."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        client_users = User.objects.filter(role='client', is_active=True)
        serializer = self.get_serializer(client_users, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Filter users based on role
        """
        user = self.request.user
        
        if not user.is_authenticated:
            return User.objects.none()
        
        if user.role == 'admin':
            return User.objects.all()
        elif user.role == 'manager':
            # Managers can see everyone except admins
            return User.objects.exclude(role='admin')
        elif user.role == 'staff':
            # Staff can see clients and other staff
            return User.objects.filter(role__in=['client', 'staff'])
        else:  # client
            # Clients can only see themselves
            return User.objects.filter(id=user.id)
        
    extend_schema(
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'avatar': {'type': 'string', 'format': 'binary'}
            }
        }
    },
    responses=ProfileSerializer
)
    @action(detail=False, methods=['post'], url_path='me/avatar', 
            parser_classes=[MultiPartParser, FormParser])
    def upload_avatar(self, request):
        """
        Upload or update user avatar
        """
        user = request.user
        
        if 'avatar' not in request.FILES:
            return Response(
                {"error": "No avatar file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        avatar_file = request.FILES['avatar']
        
        # Validate file size (max 5MB)
        if avatar_file.size > 5 * 1024 * 1024:
            return Response(
                {"error": "Avatar file size must be less than 5MB"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if avatar_file.content_type not in allowed_types:
            return Response(
                {"error": "File must be an image (JPEG, PNG, GIF, WebP)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save avatar
        user.avatar = avatar_file
        user.save()
        
        serializer = ProfileSerializer(user)
        return Response(serializer.data)


# ------------------------------------------------------------
# LOGOUT VIEW
# ------------------------------------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string'}
                },
                'required': ['refresh']
            }
        },
        responses={200: {"detail": "Successfully logged out"}}
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"detail": "Successfully logged out"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": "Invalid token or already logged out"},
                status=status.HTTP_400_BAD_REQUEST
            )