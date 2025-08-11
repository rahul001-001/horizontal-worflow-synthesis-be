# Create your views here.
from django.shortcuts import render
from .models import User
from rest_framework import generics
from .serializers import UserCreateSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsAdminRole

class RegisterUserView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserCreateSerializer(request.user)
        return Response(serializer.data)
