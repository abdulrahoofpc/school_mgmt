from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import UserSerializer, UserListSerializer, CustomTokenObtainPairSerializer
from .permissions import IsAdminUser


# ─── Template Views ───────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'core:dashboard'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        if request.POST.get('password'):
            user.set_password(request.POST.get('password'))
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def user_list_view(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def user_create_view(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = User.objects.create_user(
                username=username, password=password,
                first_name=first_name, last_name=last_name,
                email=email, role=role, phone=phone
            )
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'action': 'Create'})


@login_required
def user_edit_view(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('accounts:user_list')
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.role = request.POST.get('role', user.role)
        user.phone = request.POST.get('phone', user.phone)
        if request.POST.get('password'):
            user.set_password(request.POST.get('password'))
        user.save()
        messages.success(request, 'User updated successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'action': 'Edit', 'edit_user': user})


@login_required
@require_http_methods(['POST'])
def user_delete_view(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')
    try:
        user = User.objects.get(pk=pk)
        if user == request.user:
            messages.error(request, 'Cannot delete your own account.')
        else:
            user.delete()
            messages.success(request, 'User deleted.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    return redirect('accounts:user_list')


# ─── API Views ────────────────────────────────────────────────────────────────

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
