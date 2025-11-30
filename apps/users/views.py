
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    RegisterSerializer,
    ProfileSerializer,
    UserSerializer,
    LoginSerializer      
)
from .services import UserService

User = get_user_model()



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset

    @extend_schema(request=RegisterSerializer, responses={201: ProfileSerializer})
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(ProfileSerializer(user).data, status=201)

    @extend_schema(responses=ProfileSerializer)
    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def profile(self, request):
        user = request.user  # Use request.user directly
        if request.method == "PATCH":
            serializer = ProfileSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
        return Response(ProfileSerializer(user).data)

    # Add this action to get staff users specifically
    @extend_schema(responses=UserSerializer(many=True))
    @action(detail=False, methods=['get'], url_path='staff')
    def staff_users(self, request):
        staff_users = User.objects.filter(role='staff')
        serializer = self.get_serializer(staff_users, many=True)
        return Response(serializer.data)