from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from .serializers import RegisterSerializer,ProfileSerializer
from .services import UserService
from .permissions import IsAdminOrReadOnly


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
