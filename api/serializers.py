from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from .models import (UserProfile, GMUDVersion, TestPlan, TestCase, TestExecution, Evidence, AuditLog, ValidationSession, ValidationAccessKey)

class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    active = serializers.SerializerMethodField()
    role_write = serializers.CharField(write_only=True, required=False)
    active_write = serializers.BooleanField(write_only=True, required=False)
    username = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'active', 'role_write', 'active_write',) 

    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return None

    def get_active(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.active
        return False

    def create(self, validated_data):
        with transaction.atomic():  

            role = validated_data.pop('role_write', 'TESTADOR')
            role = role.upper() if role else 'TESTADOR'

            active = validated_data.pop('active_write', True)

            email = validated_data.get('email')
            if not email:
                raise serializers.ValidationError({"email": "Campo obrigatório"})

            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                password='123456'
            )

            UserProfile.objects.create(
                user=user,
                role=role,
                active=active
            )

            return user

    def update(self, instance, validated_data):
        role = validated_data.pop('role_write', None)
        active = validated_data.pop('active_write', None)

        if 'first_name' in validated_data:
            instance.first_name = validated_data['first_name']

        if 'last_name' in validated_data:
            instance.last_name = validated_data['last_name']

        if 'email' in validated_data:
            instance.email = validated_data['email']
            instance.username = validated_data['email'] 

        instance.save()

        if hasattr(instance, 'profile'):
            if role:
                instance.profile.role = role.upper()

            if active is not None:
                instance.profile.active = active

            instance.profile.save()

        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'role', 'active', 'created_at')

class UserMeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    active = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'active',
        )

    def get_role(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.role
        return None

    def get_active(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.active
        return False


class GMUDVersionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField (source='created_by.get_full_name', read_only=True)

    class Meta:
        model = GMUDVersion
        fields = ('id', 'version', 'description', 'created_by', 'created_by_name', 'created_at')
        read_only_fields = ('created_by','created_at')

class EvidenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Evidence
        fields = (
            'id',
            'test_execution',
            'file',
            'file_type',
            'created_at'
        )
        read_only_fields = ('created_at',)

    def validate_file(self, value):
        max_size = 10 * 1024 * 1024
        valid_types = ['image/png', 'image/jpeg', 'application/pdf']

        if value.size > max_size:
            raise serializers.ValidationError("Arquivo muito grande (máx 10MB)")

        if value.content_type not in valid_types:
            raise serializers.ValidationError("Tipo de arquivo não permitido")

        return value

class TestExecutionInlineSerializer(serializers.ModelSerializer):
    test_case_name = serializers.CharField(
        source='test_case.description',
        read_only=True
    )

    executed_by_name = serializers.SerializerMethodField()
    
    def get_executed_by_name(self, obj):
        return obj.executed_by.get_full_name() or obj.executed_by.username

    evidences = EvidenceSerializer(many=True, read_only=True)

    class Meta:
        model = TestExecution
        fields = (
            'id',
            'test_case',
            'test_case_name',
            'status',
            'comment',
            'executed_by',
            'executed_by_name',
            'executed_at',
            'evidences'
        )        

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ('id', 'test_plan', 'description', 'setor', 'order_index', 'active', 'created_at')
        read_only_fields = ('id', 'order_index', 'created_at')

    def validate(self, data):
        exists = TestCase.objects.filter(
            test_plan=data["test_plan"],
            setor=data["setor"],
            description=data["description"]
        ).exists()

        if exists:
            raise serializers.ValidationError(
                "Já existe um TestCase com essa descrição neste setor."
            )

        return data

    def create(self, validated_data):
        test_plan = validated_data["test_plan"]

        last_case = TestCase.objects.filter(
            test_plan=test_plan
        ).order_by("-order_index").first()

        next_order = 1 if not last_case else last_case.order_index + 1

        validated_data["order_index"] = next_order

        return super().create(validated_data)

class TestCaseDetailSerializer(serializers.ModelSerializer):
    executions = TestExecutionInlineSerializer(many=True, read_only=True)
    execution_count = serializers.SerializerMethodField()

    class Meta:
        model = TestCase
        fields = (
            'id',
            'description',
            'order_index',
            'execution_count',
            'executions'
        )

    def get_execution_count(self, obj):
        return obj.executions.count()
    

class TestPlanListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    test_case_count = serializers.SerializerMethodField()

    class Meta:
        model = TestPlan
        fields = (
            'id', 'name', 'division', 'system', 'setores', 'environment', 'status', 'validation_type', 
            'created_by', 'created_by_name', 'responsible', 'responsible_name', 'test_case_count', 'created_at'
        )
        read_only_fields = ('created_by', 'created_at')

    def get_test_case_count(self, obj):
        return obj.test_cases.count()
        
class TestPlanDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    responsible_name = serializers.SerializerMethodField()
    test_cases = TestCaseSerializer(many=True, required=False)
    access_keys = serializers.SerializerMethodField()
    current_validation_session_id = serializers.SerializerMethodField()

    class Meta:
        model = TestPlan
        fields = (
            'id', 'name', 'description', 'division', 'setores', 'system','is_multivalidation', 'access_keys', 'environment', 'validation_type',
            'status', 'gmud_version', 'created_by', 'created_by_name', 'responsible', 
            'responsible_name', 'test_cases', 'created_at', 'updated_at', 'current_validation_session_id'
        )
        read_only_fields = ('created_by', 'access_key', 'status', 'created_at', 'updated_at')

    def get_access_keys(self, obj):
        keys = ValidationAccessKey.objects.filter(test_plan=obj, key__startswith="VAL-")

        resultado = {}

        for key in keys:
            setor = key.setor

            if not setor or setor == "default":
                continue

            if setor not in resultado:
                resultado[setor] = []

            resultado[setor].append({
                "key": key.key,
                "used": key.used
            })

        return resultado

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username
    
    def get_responsible_name(self, obj):
        return obj.responsible.get_full_name() or obj.responsible.username

    def get_current_validation_session_id(self, obj):
        session = obj.sessions.order_by('-started_at').first()
        return session.id if session else None

    def create(self, validated_data):

        test_cases_data = validated_data.pop('test_cases', [])
        with transaction.atomic():
            test_plan = TestPlan.objects.create(**validated_data)

            for case in test_cases_data:
                TestCase.objects.create(test_plan=test_plan, **case)


        return test_plan

class TestExecutionSerializer(serializers.ModelSerializer):
    executed_by_name = serializers.CharField(source='executed_by.get_full_name', read_only=True)

    class Meta:
        model = TestExecution
        fields = ('id', 'session', 'test_case', 'executed_by', 'executed_by_name', 'status', 'comment', 'executed_at')
        read_only_fields = ('executed_by', 'executed_at')

    def create(self, validated_data):
        validated_data['executed_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data['executed_by'] = self.context['request'].user
        return super().update(instance, validated_data)
    
    def validate(self, data):
        test_case = data.get('test_case') or self.instance.test_case
        session = data.get('session') or self.instance.session

        if not test_case.active:
            raise serializers.ValidationError(
            "Não é possível executar um TestCase inativo"
        )
    
        if session.status != session.Status.IN_PROGRESS:
            raise serializers.ValidationError(
            "Não é possível executar testes em uma sessão finalizada"
        )
    
        if test_case.test_plan != session.test_plan:
            raise serializers.ValidationError(
            "O TestCase não pertence ao TestPlan da sessão"
        )
    
        return data

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            'id', 'user', 'user_name', 'action', 'entity', 'entity_id', 'details', 'created_at'
        )

class ValidationSessionSerializer(serializers.ModelSerializer):
    queryset = ValidationSession.objects.prefetch_related('executions', 'executions__test_case', 'executions__evidences', 
                                                          'executions__executed_by')
    started_by_name = serializers.CharField(source='started_by.get_full_name', read_only=True)
    gmud_version = serializers.CharField(source='test_plan.gmud_version.version', read_only=True)
    executions = TestExecutionInlineSerializer(many=True, read_only=True)
    test_plan_system = serializers.CharField(source='test_plan.system', read_only=True)
    test_plan_name = serializers.CharField(source='test_plan.name', read_only=True)
    test_plan_environment = serializers.CharField(source='test_plan.environment', read_only=True)
    test_plan_division = serializers.CharField(source='test_plan.division', read_only=True)
    access_key = serializers.SerializerMethodField()

    def get_access_key(self, obj):
        key = ValidationAccessKey.objects.filter(
            test_plan=obj.test_plan,
            setor=obj.setor
        ).first()

        return key.key if key else None 

    class Meta:
        model = ValidationSession
        fields = (
            'id',
            'setor',
            'test_plan',            
            'gmud_version',
            'test_plan_system',
            'test_plan_division',
            'test_plan_environment',
            'test_plan_name',            
            'started_by',
            'started_by_name',
            'status',
            'started_at',
            'finished_at',
            'signature',
            'executions',
            'access_key',
        )
        read_only_fields = (
            'started_by',
            'status',
            'started_at',
            'finished_at'
        )