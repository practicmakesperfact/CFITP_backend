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
    UserListSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    AdminCreateUserSerializer  # Add this import
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
# USER VIEWSET (UPDATED FOR ADMIN CREATE FUNCTIONALITY)
# ------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        """
        Use different serializers based on action
        """
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'create':
            return RegisterSerializer
        elif self.action == 'admin_create':
            return AdminCreateUserSerializer
        elif self.action == 'register':
            return RegisterSerializer
        elif self.action in ['profile', 'me']:
            return ProfileSerializer
        else:
            return UserSerializer
    
    def get_serializer_context(self):
        """
        Add request to serializer context
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_permissions(self):
        """
        Set permissions based on action
        """
        if self.action in ['register', 'login']:
            return [AllowAny()]
        elif self.action == 'admin_create':
            return [IsAdminUser()]
        elif self.action == 'list':
            return [IsAuthenticated()]
        elif self.action in ['retrieve', 'profile', 'me', 'change_password', 'upload_avatar']:
            return [IsAuthenticated()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only admin can create/update/delete users (except self-profile updates)
            return [IsAdminUser()]
        else:
            return [IsAuthenticated()]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: ProfileSerializer},
        description="Register a new user (client role only for public, any role for admin)"
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Public endpoint for registration. Admin users can create any role.
        """
        import json
        print("=" * 50)
        print("REGISTRATION REQUEST RECEIVED")
        print("=" * 50)
        print("Request data:", json.dumps(request.data, indent=2))
        print("User making request:", request.user.email if request.user.is_authenticated else "Anonymous")
        
        # Pass request context to serializer
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            print("VALIDATION ERRORS:", json.dumps(serializer.errors, indent=2))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = serializer.save()
            print(f"User created successfully: {user.email} (ID: {user.id}, Role: {user.role})")
            
            response_data = {
                'user': ProfileSerializer(user).data,
                'message': 'Registration successful!'
            }
            
            print("Registration successful, returning response")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return Response(
                {"detail": f"An error occurred during registration: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        request=AdminCreateUserSerializer,
        responses={201: UserDetailSerializer},
        description="Admin-only endpoint to create users with any role"
    )
    @action(detail=False, methods=['post'], url_path='admin/create', permission_classes=[IsAdminUser])
    def admin_create(self, request):
        """
        Admin-only endpoint to create users with any role
        """
        import json
        print("=" * 50)
        print("ADMIN CREATE USER REQUEST")
        print("=" * 50)
        print("Admin user:", request.user.email)
        print("Request data:", json.dumps(request.data, indent=2))
        
        serializer = AdminCreateUserSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            print("VALIDATION ERRORS:", json.dumps(serializer.errors, indent=2))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = serializer.save()
            print(f"User created by admin: {user.email} (ID: {user.id}, Role: {user.role})")
            
            return Response(
                UserDetailSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            print(f"Error creating user as admin: {str(e)}")
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
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
        responses=UserListSerializer(many=True),
        description="Get all staff users (role='staff' only)"
    )
    @action(detail=False, methods=['get'], url_path='staff')
    def staff_users(self, request):
        """
        Get ONLY staff users (role='staff'), EXCLUDE managers and admins
        """
        # Only allow managers and admins to view staff list
        if request.user.role not in ['manager', 'admin']:
            return Response(
                {"detail": "You don't have permission to view staff users."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # FIXED: Only get users with role='staff' (not 'manager')
        staff_users = User.objects.filter(
            role='staff',
            is_active=True
        ).order_by('first_name')
        
        print("=" * 50)
        print("DEBUG: /users/staff/ endpoint called")
        print(f"Query SQL: {staff_users.query}")
        print(f"Number of users found: {staff_users.count()}")
        
        # Check what users were found
        found_users = list(staff_users)
        print(f"Found users: {[user.email for user in found_users]}")
        
        # Double-check each user's role
        for user in found_users:
            print(f"  - {user.email}: role='{user.role}'")
        print("=" * 50)
        
        serializer = UserListSerializer(staff_users, many=True)
        
        # Debug the serialized data too
        serialized_data = serializer.data
        print(f"Serialized data being returned: {serialized_data}")
        
        return Response(serialized_data)

    @extend_schema(
        responses=UserListSerializer(many=True),  
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
        serializer = UserListSerializer(client_users, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Filter users based on role
        """
        user = self.request.user
        
        if not user.is_authenticated:
            return User.objects.none()
        
        if user.role == 'admin':
            return User.objects.all().order_by('-date_joined')
        elif user.role == 'manager':
            # Managers can see everyone except admins
            return User.objects.exclude(role='admin').order_by('-date_joined')
        elif user.role == 'staff':
            # Staff can see clients and other staff
            return User.objects.filter(role__in=['client', 'staff']).order_by('-date_joined')
        else:  # client
            # Clients can only see themselves
            return User.objects.filter(id=user.id)

    @extend_schema(
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

    @extend_schema(
        responses=UserListSerializer(many=True),
        description="Admin-only endpoint to get all users with full details"
    )
    @action(detail=False, methods=['get'], url_path='admin/users', permission_classes=[IsAdminUser])
    def admin_users_list(self, request):
        """
        Admin-only endpoint to get all users with full details
        """
        users = User.objects.all().order_by('-date_joined')
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'user_ids': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'List of user IDs to update'
                    },
                    'action': {
                        'type': 'string',
                        'enum': ['activate', 'deactivate', 'delete'],
                        'description': 'Action to perform'
                    }
                },
                'required': ['user_ids', 'action']
            }
        },
        responses={200: {"detail": "Bulk operation completed"}}
    )
    @action(detail=False, methods=['post'], url_path='admin/users/bulk', permission_classes=[IsAdminUser])
    def admin_users_bulk(self, request):
        """
        Admin bulk operations
        """
        user_ids = request.data.get('user_ids', [])
        action = request.data.get('action')
        
        if not user_ids:
            return Response(
                {"error": "No user IDs provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action not in ['activate', 'deactivate', 'delete']:
            return Response(
                {"error": "Invalid action. Must be 'activate', 'deactivate', or 'delete'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            users = User.objects.filter(id__in=user_ids)
            
            if action == 'activate':
                users.update(is_active=True)
                message = f"Activated {users.count()} users"
            elif action == 'deactivate':
                users.update(is_active=False)
                message = f"Deactivated {users.count()} users"
            elif action == 'delete':
                count = users.count()
                users.delete()
                message = f"Deleted {count} users"
            
            return Response({"detail": message})
            
        except Exception as e:
            return Response(
                {"error": f"Error performing bulk operation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # Override update method to use UserUpdateSerializer with context
    def update(self, request, *args, **kwargs):
        """
        Update user information
        """
        user = self.get_object()
        
        # Regular users can only update their own profile through 'me' endpoint
        if request.user != user and request.user.role != 'admin':
            return Response(
                {"detail": "You don't have permission to update this user."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserUpdateSerializer(user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full user details
        return Response(UserDetailSerializer(user).data)

    # Override retrieve to use UserDetailSerializer
    def retrieve(self, request, *args, **kwargs):
        """
        Get user details
        """
        user = self.get_object()
        
        # Check permissions
        if request.user.role == 'client' and request.user != user:
            return Response(
                {"detail": "You don't have permission to view this user."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserDetailSerializer(user)
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