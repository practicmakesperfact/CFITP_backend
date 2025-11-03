from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema  # For Swagger

from .serializers import RegisterSerializer, ProfileSerializer, UserSerializer
from .services import UserService

User = get_user_model()

# 1. USER REGISTER VIEW 

class UserRegisterView(generics.CreateAPIView):
    """
    Simple registration endpoint.
    Expects JSON: { "email": "...", "password": "...", "role": "client" }
    """
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer  

    # Tell Swagger what to show in "Parameters"
    @extend_schema(
        request=RegisterSerializer,
        responses={201: ProfileSerializer},
        description="Register new user. Role must be: client, staff, manager, admin"
    )
    def post(self, request, *args, **kwargs):
        """
        Use DRF's built-in create() instead of manual parsing
        → Keeps validation, hashing, and Swagger docs
        """
        return self.create(request, *args, **kwargs)

    # OPTIONAL: Override create() only if you need custom logic
    # But better to let DRF handle it
    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     user = serializer.save()
    #     return Response(ProfileSerializer(user).data, status=status.HTTP_201_CREATED)

# 2. USER PROFILE VIEW 
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Return / update current user's profile.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user

    #  Add schema for GET
    @extend_schema(responses=ProfileSerializer)
    def get(self, request, *args, **kwargs):
        return Response(ProfileSerializer(request.user).data)

    #  Add schema for PATCH
    @extend_schema(responses=ProfileSerializer)
    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(ProfileSerializer(user).data)
    
# 3. USER LOGOUT VIEW 

class UserLogoutView(APIView):
    """
    Logout by blacklisting refresh token.
    Accepts: { "refresh": "<token>" }
    """
    permission_classes = [IsAuthenticated]

    # Define request body for Swagger
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
        responses={204: None}
    )
    def post(self, request, *args, **kwargs):
        refresh = request.data.get('refresh')
        if refresh:
            try:
                from rest_framework_simplejwt.tokens import RefreshToken
                RefreshToken(refresh).blacklist()
            except Exception:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)

# 4. USER VIEWSET 

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    # Document register action
    @extend_schema(
        request=RegisterSerializer,
        responses={201: ProfileSerializer}
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(ProfileSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    #  Document profile action (GET/PATCH /users/m/)
    @extend_schema(responses=ProfileSerializer)
    @action(detail=False, methods=['get', 'patch'], url_path='m')
    def profile(self, request):
        user = UserService.get_current_user(request)
        if request.method == 'PATCH':
            serializer = ProfileSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
        return Response(ProfileSerializer(user).data)