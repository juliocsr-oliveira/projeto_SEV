from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
import uuid
from django.conf import settings
from django.utils import timezone
from django.db.models import Q


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrador'),
        ('AUDITOR', 'Auditor'),
        ('TESTADOR', 'Testador'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name= 'profile')
    role = models.CharField(max_length=20, choices= ROLE_CHOICES)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"
    
class GMUDVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable= False)
    version = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='gmud_versions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Versão GMUD'
        verbose_name_plural = 'Versões GMUD'
        ordering = ['-created_at']

    def __str__(self):
        return f"GMUD {self.version}"
    
class TestPlan(models.Model):
    STATUS_CHOICE = (
    ('RASCUNHO', 'Rascunho'),
    ('CONFIGURADA', 'Configurada'),
    ('PRONTA_PARA_TESTE', 'Pronta para Teste'),
    )

    VALIDATION_TYPE_CHOICES = (
        ('FUNCIONAL','Funcional'),
        ('REGRESSAO', 'Regressão'),
        ('INTEGRACAO', 'Integração'),
        ('PERFORMANCE', 'Performance'),
        ('SEGURANCA', 'Segurança'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    division = models.CharField(max_length=100)
    system = models.CharField(max_length=100, null=True, blank=True)
    environment = models.CharField(max_length=50, null=True, blank=True)
    validation_type = models.CharField(max_length=50, choices=VALIDATION_TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICE, default='RASCUNHO')
    access_key = models.CharField(max_length=100, unique=True, validators=[MinLengthValidator(10)])
    gmud_version = models.ForeignKey(GMUDVersion, on_delete=models.SET_NULL, null=True, blank=True, related_name= 'test_plans')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_test_plans')
    responsible = models.ForeignKey(User, on_delete=models.PROTECT, related_name='responsible_test_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plano de Teste'
        verbose_name_plural = 'Plano de Teste'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-status']), 
            models.Index(fields=['created_by']),
]
    
    def configurar(self):
        if self.status != 'RASCUNHO':
            raise ValueError("Apenas planos em rascunho podem ser configurados.")

        if not self.test_cases.exists():
            raise ValueError("Plano precisa ter pelo menos um caso de teste.")

        self.status = 'CONFIGURADA'
        self.save(update_fields=['status'])


    def preparar_para_teste(self):
        if self.status != 'CONFIGURADA':
            raise ValueError("Plano precisa estar configurado.")

        if not self.gmud_version:
            raise ValueError("Plano precisa estar vinculado a uma GMUD.")

        if self.sessions.filter(status='IN_PROGRESS').exists():
            raise ValueError("Já existe sessão ativa para este plano.")

        self.status = 'PRONTA_PARA_TESTE'
        self.save(update_fields=['status'])

    def __str__(self):
        return self.name
    
class TestCase(models.Model):
    
    id = models. UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='test_cases')
    description = models.TextField()
    order_index = models.IntegerField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Caso de Teste'
        verbose_name_plural = 'Casos de Testes'
        ordering = ['test_plan', 'order_index']
        unique_together = ['test_plan', 'order_index']

    def __str__(self):
        return f"{self.test_plan.name} - Caso {self.order_index}"

class TestExecution(models.Model):
        
    STATUS_CHOICES = (
        ('OK', 'OK'),
        ('FALHOU', 'Falhou'),
        ('NAO_APLICA', 'Não se Aplica'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    session = models.ForeignKey(
        'ValidationSession', 
        on_delete=models.CASCADE, 
        related_name='executions'
    )
    
    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    executed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='test_executions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    comment = models.TextField(blank=True, null=False)
    executed_at = models.DateTimeField(auto_now_add=True)
    evidence = models.FileField(upload_to='evidence/', null=True, blank=True)

    class Meta:
        ordering = ['-executed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'test_case'],
                name='unique_execution_per_test_case_per_session'
            )
        ]
    
    def __str__(self):
        return f"{self.test_case} - {self.status}"

    
class Evidence(models.Model):
    FILE_TYPE_CHOICES = (
        ('IMAGE', 'Imagem'),
        ('VIDEO', 'Vídeo'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_execution = models.ForeignKey(TestExecution, on_delete=models.CASCADE, related_name='evidences')
    file = models.FileField(upload_to='evidences/%Y/%m/%d/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evidência'
        verbose_name_plural = 'Evidências'
        ordering = ['-created_at']

    def __str__(self):
        return f"Evidência - {self.test_execution}"
    
class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=255)
    entity = models.CharField(max_length=100, blank=True, null=True)
    entity_id = models.UUIDField(blank=True, null=True)
    details = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']), 
            models.Index(fields=['created_at']),
]

    def __str__(self):
        return f"{self.user} - {self.action}"        

class ValidationSession(models.Model): 
    class Status(models.TextChoices): 
        IN_PROGRESS = "IN_PROGRESS", "Em andamento" 
        FAILED = "FAILED", "Reprovada" 
        APPROVED = "APPROVED", "Aprovada" 
        ARCHIVED = "ARCHIVED", "Arquivada" 
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    test_plan = models.ForeignKey( TestPlan, on_delete=models.CASCADE, related_name="sessions" ) 
    started_by = models.ForeignKey( User, on_delete=models.PROTECT, related_name="validation_sessions" ) 
    status = models.CharField( max_length=20, choices=Status.choices, default=Status.IN_PROGRESS ) 
    started_at = models.DateTimeField(auto_now_add=True) 
    finished_at = models.DateTimeField(null=True, blank=True) 
    
    class Meta: 
        ordering = ['-started_at'] 
        indexes = [ models.Index(fields=['test_plan']), 
                   models.Index(fields=['status']), ] 
        
        constraints = [
            models.UniqueConstraint(
                fields = ['test_plan'], 
                          condition= Q(status='IN_PROGRESS'),
                          name = 'unique_active_session_per_plan')
        ]
        
    def finalize(self):
        if self.status != self.Status.IN_PROGRESS:
            raise ValueError("Sessão já finalizada.") 
        executions = self.executions.all() 

        if not executions.exists():
            raise ValueError("Não é possível finalizar sessão sem execuções.")
        
        if executions.filter(status='FALHOU').exists(): 
            self.status = self.Status.FAILED 
        else: 
            self.status = self.Status.APPROVED 
            
        self.finished_at = timezone.now() 
        self.save(update_fields=['status', 'finished_at']) 
            
    def __str__(self): 
        return f"{self.test_plan.name} - {self.status}"