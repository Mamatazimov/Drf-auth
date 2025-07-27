from django.contrib import admin
from users.models import UserVerifyEmail

class AdminUserVerifyEmail(admin.ModelAdmin):
    list_display=["email"]

admin.site.register(UserVerifyEmail,AdminUserVerifyEmail)
