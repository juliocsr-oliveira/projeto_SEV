from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
import secrets
 
from .models import (
    UserProfile, GMUDVersion, TestPlan, TestCase,
    TestExecution, Evidence, AuditLog
)
from .serializers import (
    UserSerializer, UserProfileSerializer, UserDetailSerializer,
    GMUDVersionSerializer, TestPlanListSerializer, TestPlanDetailSerializer,
    TestCaseSerializer, TestExecutionSerializer, EvidenceSerializer,
    AuditLogSerializer
)
from .permissions import IsAdmin, IsAuditorOrAdmin, IsOwnerOrAdmin
 
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['profile__role', 'profile__active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Obter dados do usuário autenticado"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
 
class GMUDVersionViewSet(viewsets.ModelViewSet):
    queryset = GMUDVersion.objects.all()
    serializer_class = GMUDVersionSerializer
    permission_classes = [IsAuthenticated, IsAuditorOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['version', 'description']
    ordering_fields = ['created_at', 'version']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
 
class TestPlanViewSet(viewsets.ModelViewSet):
    queryset = TestPlan.objects.all()
    permission_classes = [IsAuthenticated, IsAuditorOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'validation_type', 'environment', 'division']
    search_fields = ['name', 'description', 'division', 'system']
    ordering_fields = ['created_at', 'name', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TestPlanDetailSerializer
        return TestPlanListSerializer
    
    def perform_create(self, serializer):
        access_key = f"VAL-{secrets.token_hex(8).upper()}"
        serializer.save(created_by=self.request.user, access_key=access_key)
        # Log de auditoria
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            entity='TestPlan',
            entity_id=serializer.instance.id
        )
    
    @action(detail=True, methods=['post'])
    def add_test_case(self, request, pk=None):
        """Adicionar caso de teste ao plano"""
        test_plan = self.get_object()
        serializer = TestCaseSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(test_plan=test_plan)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def access_key(self, request, pk=None):
        """Obter chave de acesso do plano"""
        test_plan = self.get_object()
        return Response({'access_key': test_plan.access_key})
 
class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated, IsAuditorOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['test_plan', 'active']
    ordering_fields = ['order_index', 'created_at']
    ordering = ['order_index']
 
class TestExecutionViewSet(viewsets.ModelViewSet):
    queryset = TestExecution.objects.all()
    serializer_class = TestExecutionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['test_case', 'executed_by', 'status']
    ordering_fields = ['executed_at']
    ordering = ['-executed_at']
    
    def perform_create(self, serializer):
        serializer.save(executed_by=self.request.user)
        # Log de auditoria
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            entity='TestExecution',
            entity_id=serializer.instance.id
        )
 
class EvidenceViewSet(viewsets.ModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['test_execution', 'file_type']
 
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'action', 'entity']
    search_fields = ['action', 'entity']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
