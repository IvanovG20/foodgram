from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


class UserAdmin(admin.ModelAdmin):

    list_display = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email',)
    search_fields = ('username', 'email', 'first_name', 'last_name')


admin.site.register(User, UserAdmin)
