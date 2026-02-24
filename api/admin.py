from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile

# Inline do profile dentro do User
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Usuário'

# Custom UserAdmin com inline
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

# Registrar
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Registrar UserProfile também separadamente, se quiser listar todos
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'active', 'created_at')
    list_filter = ('role', 'active')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')