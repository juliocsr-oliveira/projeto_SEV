from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsAdmin, IsAuditorOrAdmin, IsOwnerOrAdmin
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import F
import secrets
from django.utils import timezone
 
from .models import (
    UserProfile, GMUDVersion, TestPlan, TestCase,
    TestExecution, Evidence, AuditLog, ValidationSession, ValidationAccessKey
)
from .serializers import (
    UserSerializer, UserProfileSerializer, UserMeSerializer,
    GMUDVersionSerializer, TestPlanListSerializer, TestPlanDetailSerializer,
    TestCaseSerializer, TestExecutionSerializer, EvidenceSerializer,
    AuditLogSerializer, TestCaseDetailSerializer, ValidationSessionSerializer
)

 
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['profile__role', 'profile__active']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]
    
    def get_serializer_class(self):
        if self.action == 'me':
            return UserMeSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Obter dados do usuário autenticado"""
        serializer = UserMeSerializer(request.user)
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'validation_type', 'environment', 'division', 'sessions']
    search_fields = ['name', 'description', 'division', 'system']
    ordering_fields = ['created_at', 'name', 'status']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['create','update', 'partial_update', 'destroy', 'add_test_case', 'preparar', 'generate_keys']:
            return [IsAuthenticated(), IsAuditorOrAdmin()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'create']:
            return TestPlanDetailSerializer
        return TestPlanListSerializer
    
    def perform_create(self, serializer):

        plan = serializer.save(
            created_by=self.request.user,
            responsible=self.request.user,
    )

        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            entity='TestPlan',
            entity_id=plan.id
    )
        
    @action(detail=True, methods=['post'])
    def preparar(self, request, pk=None):
        plan = self.get_object()

        try:
            plan.preparar_para_teste()
            return Response({"detail": "Plano pronto para validação"})
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
    
    @action(detail=True, methods=['post'])
    def add_test_case(self, request, pk=None):
        """Adicionar caso de teste ao plano"""
        test_plan = self.get_object()

        serializer = TestCaseSerializer(data=request.data)
        
        if serializer.is_valid():
            last_order = test_plan.test_cases.count()

            serializer.save(test_plan=test_plan, order_index=last_order +1)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def configurar(self, request, pk=None):
        plan = self.get_object()
        plan.configurar()
        return Response({"detail": "Plano configurado com sucesso"})
    
    @action(detail=True, methods=['post'], url_path='generate-keys')
    def generate_keys(self, request, pk=None):
        test_plan = self.get_object()

        if not test_plan.test_cases.exists():
            return Response(
            {"error": "Adicione pelo menos um caso de teste antes de gerar as keys"},
            status=400
        )

        keys_data = request.data.get('keys', [])

        if not keys_data:
            return Response({"error": "Informe ao menos um setor"}, status=400)
        
        if not test_plan.is_multivalidation and len(keys_data) > 1:
            return Response(
            {"error": "Plano não permite múltiplas validações"},
            status=400)

        created_keys = []

        for setor in test_plan.setores:
            
            key = ValidationAccessKey.objects.create(
                key=f"VAL-{secrets.token_hex(8).upper()}",
                test_plan=test_plan,
                setor=setor,
                max_uses=1
            )
            
            created_keys.append({"key":key.key, "setor": key.setor})

        return Response({
            "message": "Keys geradas com sucesso",
            "keys": created_keys
        })
    
class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated, IsAuditorOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['test_plan', 'active', 'setor']
    ordering_fields = ['order_index', 'created_at']
    ordering = ['order_index']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TestCaseDetailSerializer
        return TestCaseSerializer
    
    def perform_create(self, serializer):
        test_plan = serializer.validated_data.get("test_plan")
        setor = serializer.validated_data.get("setor")

        print("SALVANDO SETOR:", setor)

        last_order = (
            TestCase.objects
            .filter(test_plan=test_plan, setor=setor)
            .count()
        )

        serializer.save(order_index=last_order + 1)

    def get_queryset(self):
        queryset = super().get_queryset()
    
        setor = self.request.query_params.get("setor")
        test_plan = self.request.query_params.get("test_plan")

        print("🔍 FILTRANDO SETOR:", setor)
        print("🔍 FILTRANDO TEST_PLAN:", test_plan)

        if setor:
            queryset = queryset.filter(setor=setor)

        if test_plan:
            queryset = queryset.filter(test_plan=test_plan)

        return queryset
    
class ValidationSessionViewSet(viewsets.ModelViewSet):

    queryset = ValidationSession.objects.all()
    serializer_class = ValidationSessionSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['test_plan', 'status']
    ordering_fields = ['started_at']
    ordering = ['-started_at']

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            test_plan_id = request.data.get("test_plan_id")
            setor = request.data.get("setor")

            if not test_plan_id:
                return Response({"error": "test_plan_id é obrigatório"}, status=400)

            if not setor:
                return Response({"error": "Setor é obrigatório"}, status=400)

            try:
                test_plan = TestPlan.objects.get(id=test_plan_id)
            except TestPlan.DoesNotExist:
                return Response({"error": "TestPlan não encontrado"}, status=404)

            # 🚨 evitar duplicidade
            existing_session = ValidationSession.objects.filter(
                test_plan=test_plan,
                setor=setor,
                started_by=request.user
            ).first()

            if existing_session:
                return Response({
                    "message": "Sessão já existente",
                    "session_id": existing_session.id
                })

            # 🚀 cria session
            session = ValidationSession.objects.create(
                test_plan=test_plan,
                setor=setor,
                started_by=request.user
            )

            # 🔥 cria executions
            test_cases = test_plan.test_cases.filter(active=True)

            executions = [
                TestExecution(
                    session=session,
                    test_case=tc,
                    executed_by=request.user,
                    status="PENDENTE"
                )
                for tc in test_cases
            ]

            TestExecution.objects.bulk_create(executions)

            # 🔥 atualiza setores do plano (AGORA FAZ SENTIDO)
            if setor not in test_plan.setores:
                test_plan.setores.append(setor)
                test_plan.save()

            return Response({
                "message": "Sessão criada com sucesso",
                "session_id": session.id
            }, status=201)
    
    @action(detail=False, methods=['post'], url_path='enter-with-key')
    def enter_with_key(self, request):

        with transaction.atomic():
            key_value = request.data.get('key')

            if not key_value:
                return Response({"error": "Key é obrigatória"}, status=400)

            key = ValidationAccessKey.objects.select_for_update().filter(key=key_value).first()

            if not key:
                return Response({"error": "Key Inválida"}, status=400)

            if key.test_plan.status not in ['READY', 'IN_PROGRESS']:
                return Response(
                    {"error": "Plano não disponível para validação"},
                    status=400
                )
            
            if not key.test_plan.is_multivalidation:
                if ValidationSession.objects.filter(test_plan=key.test_plan).exists():
                    return Response(
                        {"error": "Plano permite apenas uma validação"}, status=400
                    )

            # 🔒 valida limite de uso
            if key.used_count >= key.max_uses:
                return Response({"error": "Key já atingiu o limite de uso"}, status=400)

            # 🔍 verifica se usuário já tem session nesse setor + test_plan
            existing_session = ValidationSession.objects.filter(
                test_plan=key.test_plan,
                setor=key.setor,
                started_by=request.user
            ).first()

            if existing_session:
                if existing_session.status == ValidationSession.Status.COMPLETED:
                    return Response({"error": "Sessão já finalizada"}, status=400)
                
                return Response({
                    "message": "Sessão já existente",
                    "session_id": existing_session.id
                })

            # 🚀 cria nova session
            session = ValidationSession.objects.create(
                test_plan=key.test_plan,
                setor=key.setor,
                started_by=request.user
            )

            # 🔥 cria executions automaticamente
            test_cases = key.test_plan.test_cases.filter(active=True)

            executions = [
                TestExecution(
                    session=session,
                    test_case=tc,
                    executed_by=request.user,
                    status="PENDENTE"
                )
                for tc in test_cases
            ]

            TestExecution.objects.bulk_create(executions)

            # 🔢 incrementa uso da key
            ValidationAccessKey.objects.filter(pk=key.pk).update(
                used_count=F('used_count') + 1
            )

            return Response({
                "message": "Sessão criada com sucesso",
                "session_id": session.id
            }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        session = self.get_object()

        signature = request.data.get("signature")

        if not signature:
            return Response(
                {"detail": "Assinatura obrigatória"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.signature = signature

        try:

            session.signature = signature
            session.signed_at = timezone.now()

            session.finalize()

            return Response({
                "message": "Sessão finalizada",
                "status": session.status
            })

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class TestExecutionViewSet(viewsets.ModelViewSet):
    queryset = TestExecution.objects.all()
    serializer_class = TestExecutionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['session', 'test_case', 'status']

    http_method_names = ['get', 'patch', 'put']

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.session.status != ValidationSession.Status.IN_PROGRESS:
            return Response(
                {"detail": "Sessão finalizada. Não é permitido alterar execuções."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.session.status != ValidationSession.Status.IN_PROGRESS:
            return Response(
                {"detail": "Sessão finalizada. Não é permitido alterar execuções."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
 
class EvidenceViewSet(viewsets.ModelViewSet):

    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['test_execution', 'file_type']

    def perform_create(self, serializer):

        evidence = serializer.save()

        AuditLog.objects.create(
            user=self.request.user,
            action='UPLOAD',
            entity='Evidence',
            entity_id=evidence.id,
            details={
                "test_execution": str(evidence.test_execution.id),
                "file_type": evidence.file_type
            }
        )
 
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'action', 'entity']
    search_fields = ['action', 'entity']
    ordering_fields = ['created_at']
    ordering = ['-created_at']