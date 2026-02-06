from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (UserViewSet, GMUDVersionViewSet, TestPlanViewSet, TestCaseViewSet, TestExecutionViewSet, EvidenceViewSet, AuditLogViewSet)

router = DefaultRouter()
router.register (r'users', UserViewSet)
router.register (r'gmud-versions', GMUDVersionViewSet)
router.register (r'test-plans', TestPlanViewSet)
router.register (r'test-case', TestCaseViewSet)
router.register (r'test-executions', TestExecutionViewSet)
router.register (r'evidences', EvidenceViewSet)
router.register (r'audit-logs', AuditLogViewSet)

urlpatterns = [   path('', include(router.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]