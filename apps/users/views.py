from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.decorators import action
from .serializers import RegisterSerializer,ProfileSerializer
from .services import UserService
from rest_framework.permissions import IsAuthenticated, AllowAny


User = get_user_model()

class UserRegisterView(generics.CreateAPIView):
    """
    Simple registration endpoint. Adjust to use your UserSerializer if available.
    Expects JSON: { "email": "...", "password": "...", "role": "client" }
    """
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'client')
        if not email or not password:
            return Response({'detail': 'email and password required'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(email=email, password=password, role=role)
        return Response({'id': str(user.id), 'email': user.email}, status=status.HTTP_201_CREATED)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Return / update current user's profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        return Response({'id': str(user.id), 'email': user.email, 'role': getattr(user, 'role', None)})

class UserLogoutView(APIView):
    """
    Logout by blacklisting refresh token (if simplejwt blacklist enabled).
    Accepts: { "refresh": "<token>" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh = request.data.get('refresh')
        if refresh:
            try:
                from rest_framework_simplejwt.tokens import RefreshToken
                RefreshToken(refresh).blacklist()
            except Exception:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self,request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(ProfileSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=False, methods=['get','patch'],url_path='m')
    def profile(self,request):
        user = UserService.get_current_user(request)
        if request.method == 'PATCH':
            data =request.data
            user = UserService.update_profile(user,data)
        serializer = ProfileSerializer(user)
        return Response(serializer.data)
