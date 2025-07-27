from rest_framework import serializers
from rest_framework.validators import UniqueValidator 
from django.contrib.auth.models import User
from .models import UserVerifyEmail


class VerifyEmailSerializer(serializers.ModelSerializer):
    
    email = serializers.EmailField(required=True,validators=[])

    class Meta:
        model = UserVerifyEmail
        fields = ["code","email"]


    def to_internal_value(self, data):
        unexpected_fields = set(data.keys()) - set(self.fields.keys())
        if unexpected_fields:
            raise serializers.ValidationError({
                "detail": f"Unexpected fields: {unexpected_fields}"
            })
        return super().to_internal_value(data)   

class RegisterUserSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    email = serializers.EmailField(required=True,validators=[UniqueValidator(queryset=User.objects.all())])
    first_name = serializers.CharField(required=False,allow_blank=True)
    last_name = serializers.CharField(required=False,allow_blank=True)
    username = serializers.CharField(required=True,max_length=35,min_length=5,validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(required=True,max_length=35,min_length=5,write_only=True)
    confirm_password = serializers.CharField(required=True,max_length=35,min_length=5,write_only=True)

    def validate(self, attrs):
        input_keys = set(self.initial_data.keys())
        allowed_keys = set(self.fields.keys())

        unexpected_fields = input_keys - allowed_keys
        if unexpected_fields:
           raise serializers.ValidationError(
                {"detail": f"Unexpected fields: {unexpected_fields}"}
            )

        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
    
        return attrs

class LoginUserSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)
    username = serializers.CharField(required=True,max_length=35,min_length=5,validators=[])

class ForgotPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True,max_length=35,min_length=5,write_only=True)
    confirm_password = serializers.CharField(required=True,max_length=35,min_length=5,write_only=True)

    def validate(self,attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        
        return attrs
    
    
    

        





