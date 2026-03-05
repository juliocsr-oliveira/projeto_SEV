from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from .models import (UserProfile, GMUDVersion, TestPlan, TestCase, TestExecution, Evidence, AuditLog, ValidationSession)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',)

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

class TestExecutionInlineSerializer(serializers.ModelSerializer):
    executed_by_name = serializers.CharField(
        source='executed_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = TestExecution
        fields = (
            'id',
            'status',
            'comment',
            'executed_by',
            'executed_by_name',
            'executed_at'
        )        

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ('id', 'test_plan', 'description', 'order_index', 'active', 'created_at')
        read_only_fields = ('id', 'order_index', 'created_at')

    def create(self, validated_data):
        test_plan = validated_data['test_plan']

        last_case = (
            TestCase.objects.filter(test_plan=test_plan)
            .order_by('-order_index')
            .first()
        )

        next_order = 1 if not last_case else last_case.order_index + 1

        validated_data['order_index'] = next_order
        return super().create(validated_data)

class TestCaseDetailSerializer(serializers.ModelSerializer):
    executions = TestExecutionInlineSerializer(many=True, read_only=True)
    execution_count = serializers.SerializerMethodField()

    class Meta:
        model = TestCase
        fields = (
            'id',
            'name',
            'description',
            'order_index',
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
            'id', 'name', 'division', 'system', 'environment', 'status', 'validation_type', 
            'created_by', 'created_by_name', 'responsible', 'responsible_name', 'test_case_count', 'created_at'
        )
        read_only_fields = ('created_by', 'created_at')

    def get_test_case_count(self, obj):
        return obj.test_cases.count()
        
class TestPlanDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    responsible_name = serializers.CharField(source='responsible.username', read_only=True)
    test_cases = TestCaseSerializer(many=True, required=False)

    class Meta:
        model = TestPlan
        fields = (
            'id', 'name', 'description', 'division', 'system', 'environment', 'validation_type',
            'status', 'access_key', 'gmud_version', 'created_by', 'created_by_name', 'responsible', 
            'responsible_name', 'test_cases', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_by', 'access_key', 'status', 'created_at', 'updated_at')

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
    
    def validate(self, data):
        test_case = data['test_case']
        session = data['session']

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

class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ('id', 'test_execution', 'file', 'file_type', 'created_at')

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            'id', 'user', 'user_name', 'action', 'entity', 'entity_id', 'details', 'created_at'
        )

class ValidationSessionSerializer(serializers.ModelSerializer):
    started_by_name = serializers.CharField(
        source='started_by.get_full_name',
        read_only=True
    )
    executions = TestExecutionInlineSerializer(many=True, read_only=True)

    class Meta:
        model = ValidationSession
        fields = (
            'id',
            'test_plan',
            'started_by',
            'started_by_name',
            'status',
            'started_at',
            'finished_at',
            'executions'
        )
        read_only_fields = (
            'started_by',
            'status',
            'started_at',
            'finished_at'
        )