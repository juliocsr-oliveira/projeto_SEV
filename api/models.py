from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
import uuid

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
    ('AGUARDANDO_TESTE', 'Aguardando Teste'),
    ('EM_PROGRESSO', 'Em Progresso'),
    ('CONCLUIDO', 'Concluído'),
    ('FALHOU', 'Falhou'),
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
    system = models.CharField(max_length=100)
    environmment = models.CharField(max_length=50)
    validation_type = models.CharField(max_length=50, choices=VALIDATION_TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICE, default='AGUARDANDO TESTE')
    access_key = models.CharField(max_length=100, unique=True, validators=[MinLengthValidator(10)])
    gmud_version = models.ForeignKey(GMUDVersion, on_delete=models.SET_NULL, null=True, blank=True, related_name= 'test_plans')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_test_plans')
    responsibile = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='responsibile_test_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plano de Teste'
        verbose_name_plural = 'Plano de Teste'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['-status']), models.Index(fields=['created_by']),]

    def __str__(self):
        return self.name
    
class TestCase(models.Model):
    id = models. UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teste_plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='test_cases')
    description = models.TextFields()
    order_index = models.IntergerField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Caso de Teste'
        verbose_name_plural = 'Casos de Testes'
        ordering = ['test_plan', ' order_index']
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
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='executions')
    executed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='test_executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    comment = models.TextChoices(blank=True, null=True)
    executed_by = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Execução de Teste'
        verbose_name_plural = 'Execução de Testes'
        ordering = ['-executed_at']
        indexes = [models.Index(fields=['-executed_by']),]

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
    user = models.ForeignKey(user, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=255)
    entity = models.CharField(max_length=100, blank=True, null=True)
    entity_id = models.UUIDField(blank=True, null=True)
    details = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']
        indexes = [models.index(fields=['user']), models.index(fields=['created_at']),]

    def __srt__(self):
        return f"{self.user} - {self.action}"        