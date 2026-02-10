# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ApiAuditlog(models.Model):
    id = models.UUIDField(primary_key=True)
    action = models.CharField(max_length=255)
    entity = models.CharField(max_length=100, blank=True, null=True)
    entity_id = models.UUIDField(blank=True, null=True)
    details = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField()
    user = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_auditlog'


class ApiEvidence(models.Model):
    id = models.UUIDField(primary_key=True)
    file = models.CharField(max_length=100)
    file_type = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    test_execution = models.ForeignKey('ApiTestexecution', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_evidence'


class ApiGmudversion(models.Model):
    id = models.UUIDField(primary_key=True)
    version = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    created_by = models.ForeignKey('AuthUser', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_gmudversion'


class ApiTestcase(models.Model):
    id = models.UUIDField(primary_key=True)
    description = models.TextField()
    order_index = models.IntegerField()
    active = models.BooleanField()
    created_at = models.DateTimeField()
    test_plan = models.ForeignKey('ApiTestplan', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_testcase'
        unique_together = (('test_plan', 'order_index'),)


class ApiTestexecution(models.Model):
    id = models.UUIDField(primary_key=True)
    status = models.CharField(max_length=20)
    comment = models.TextField(blank=True, null=True)
    executed_at = models.DateTimeField()
    executed_by = models.ForeignKey('AuthUser', models.DO_NOTHING)
    test_case = models.ForeignKey(ApiTestcase, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_testexecution'


class ApiTestplan(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    division = models.CharField(max_length=100)
    system = models.CharField(max_length=100)
    environment = models.CharField(max_length=50)
    validation_type = models.CharField(max_length=50)
    status = models.CharField(max_length=30)
    access_key = models.CharField(unique=True, max_length=100)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('AuthUser', models.DO_NOTHING)
    gmud_version = models.ForeignKey(ApiGmudversion, models.DO_NOTHING, blank=True, null=True)
    responsible = models.ForeignKey('AuthUser', models.DO_NOTHING, related_name='apitestplan_responsible_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_testplan'


class ApiUserprofile(models.Model):
    id = models.UUIDField(primary_key=True)
    role = models.CharField(max_length=20)
    active = models.BooleanField()
    created_at = models.DateTimeField()
    user = models.OneToOneField('AuthUser', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_userprofile'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Evidence(models.Model):
    id = models.UUIDField(primary_key=True)
    test_execution = models.ForeignKey('TestExecution', models.DO_NOTHING)
    file_url = models.TextField()
    file_type = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'evidence'


class GmudVersion(models.Model):
    id = models.UUIDField(primary_key=True)
    version = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey('Users', models.DO_NOTHING, db_column='created_by')
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gmud_version'


class Log(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    action = models.CharField(max_length=255)
    entity = models.CharField(max_length=100, blank=True, null=True)
    entity_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'log'


class TestCase(models.Model):
    id = models.UUIDField(primary_key=True)
    test_plan = models.ForeignKey('TestPlan', models.DO_NOTHING)
    description = models.TextField()
    order_index = models.IntegerField()
    active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'test_case'


class TestExecution(models.Model):
    id = models.UUIDField(primary_key=True)
    test_case = models.ForeignKey(TestCase, models.DO_NOTHING)
    executed_by = models.ForeignKey('Users', models.DO_NOTHING, db_column='executed_by')
    status = models.CharField(max_length=20)
    comment = models.TextField(blank=True, null=True)
    executed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'test_execution'


class TestPlan(models.Model):
    id = models.UUIDField(primary_key=True)
    division = models.CharField(max_length=100)
    system = models.CharField(max_length=100)
    environment = models.CharField(max_length=50)
    status = models.CharField(max_length=30)
    access_key = models.CharField(unique=True, max_length=100)
    gmud_version = models.ForeignKey(GmudVersion, models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey('Users', models.DO_NOTHING, db_column='created_by')
    created_at = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    validation_type = models.CharField(max_length=50, blank=True, null=True)
    responsible = models.ForeignKey('Users', models.DO_NOTHING, db_column='responsible', related_name='testplan_responsible_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'test_plan'


class Users(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=150)
    email = models.CharField(unique=True, max_length=150)
    role = models.CharField(max_length=20)
    active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    password_hash = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'users'
