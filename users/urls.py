from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SendCodeEmailApiView,VerifyEmailApiView,RegisterUser,LoginUser,ForgotPasswordApiView

app_name="users"
urlpatterns = [
    path("verify-email/",VerifyEmailApiView.as_view(),name="verify_email"),
    path("send-code-email/",SendCodeEmailApiView.as_view(),name="send_code_email"),
    path("register/",RegisterUser.as_view(),name="register"),
    path("login/",LoginUser.as_view(),name="login"),
    path("refresh/",TokenRefreshView.as_view(),name="refresh"),
    path("forgot-password/",ForgotPasswordApiView.as_view(),name="forgot-password")
]


