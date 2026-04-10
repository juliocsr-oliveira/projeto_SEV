from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
import uuid
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
import secrets


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
    ('DRAFT', 'Em elaboração'),
    ('READY', 'Pronto para validação'),
    ('IN_PROGRESS', 'Em validação'),
    ('VALIDATED_IN_PARTS', 'Validado em partes'),
    ('VALIDATED', 'Validado'),
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
    setores = models.JSONField(default=list)
    division = models.CharField(max_length=100)
    system = models.CharField(max_length=100, null=True, blank=True)
    environment = models.CharField(max_length=50, null=True, blank=True)
    validation_type = models.CharField(max_length=50, choices=VALIDATION_TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICE, default='DRAFT')
    gmud_version = models.ForeignKey(GMUDVersion, on_delete=models.SET_NULL, null=True, blank=True, related_name= 'test_plans')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_test_plans')
    responsible = models.ForeignKey(User, on_delete=models.PROTECT, related_name='responsible_test_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_multivalidation = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Plano de Teste'
        verbose_name_plural = 'Plano de Teste'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-status']), 
            models.Index(fields=['created_by']),
]

    def preparar_para_teste(self):
        if self.status != 'DRAFT':
            raise ValueError("Plano precisa estar configurado.")
        
        if not self.test_cases.exists():
            raise ValueError("Plano precisa ter pelo menos um caso de teste")
        
        if not self.setores:
            raise ValueError("Plano precisa ter pelo menos um setor definido")
        
        self.status = 'READY'
        self.save(update_fields =['status'])

        for setor in self.setores:
            existing = ValidationAccessKey.objects.filter(test_plan=self,setor=setor).exists()

        if not existing:
            ValidationAccessKey.objects.create(
                test_plan=self,
                setor=setor,
                key=f"VAL-{secrets.token_hex(8).upper()}",
                max_uses=1
            )

    def __str__(self):
        return self.name
    
class TestCase(models.Model):
    
    id = models. UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='test_cases')
    description = models.TextField()
    order_index = models.IntegerField()
    setor = models.CharField(max_length=100)
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
        ('PENDENTE', 'Pendente'),
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    comment = models.TextField(blank=True, null=True)
    executed_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.session.status != ValidationSession.Status.IN_PROGRESS:
            raise ValueError("Sessão finalizada. Não é permitido alterar execuções.")

        super().save(*args, **kwargs)
    
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
        COMPLETED = "COMPLETED", "Concluída" 
        ARCHIVED = "ARCHIVED", "Arquivada" 
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    test_plan = models.ForeignKey( TestPlan, on_delete=models.CASCADE, related_name="sessions" )
    setor = models.CharField(max_length=100) 
    started_by = models.ForeignKey( User, on_delete=models.PROTECT, related_name="validation_sessions" ) 
    status = models.CharField( max_length=20, choices=Status.choices, default=Status.IN_PROGRESS ) 
    started_at = models.DateTimeField(auto_now_add=True) 
    finished_at = models.DateTimeField(null=True, blank=True)
    signature = models.CharField(max_length=255, null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True) 
    
    class Meta: 
        ordering = ['-started_at'] 
        indexes = [ models.Index(fields=['test_plan']), 
                   models.Index(fields=['status']), ] 
          
    def finalize(self):
        if self.status != self.Status.IN_PROGRESS:
            raise ValueError("Sessão já finalizada.")
        
        if not self.signature:
            raise ValueError("Assinatura é obrigatória para finalizar a sessão.")

        executions = self.executions.all()

        if not executions.exists():
            raise ValueError("Não é possível finalizar sessão sem execuções.")

        # 🔒 NOVA REGRA CRÍTICA
        if executions.filter(status='PENDENTE').exists():
            raise ValueError("Existem testes pendentes. Finalize todos antes de concluir.")
        
        self.status = self.Status.COMPLETED

        self.finished_at = timezone.now()
        self.save(update_fields=['status', 'finished_at', 'signature', 'signed_at'])

        self.update_test_plan_status()

    def update_test_plan_status(self):
        test_plan = self.test_plan
        sessions = test_plan.sessions.all()

        if not sessions.exists():
            test_plan.status = 'READY'

        elif sessions.filter(status=self.Status.IN_PROGRESS).exists():
            test_plan.status = 'IN_PROGRESS'

        elif sessions.filter(status=self.Status.COMPLETED).count() == sessions.count():
            test_plan.status = 'VALIDATED'

        elif sessions.filter(status=self.Status.COMPLETED).exists():
            test_plan.status = 'VALIDATED_IN_PARTS'

        else:
            test_plan.status = 'READY'

        test_plan.save(update_fields=['status'])

class ValidationAccessKey(models.Model):
    key = models.CharField(max_length=50, unique=True)
    test_plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='access_keys')
    setor = models.CharField(max_length=100)
    max_uses = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)