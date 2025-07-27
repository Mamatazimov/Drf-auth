import random
import uuid
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from rest_framework import views
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializer import VerifyEmailSerializer,RegisterUserSerializer,LoginUserSerializer,ForgotPasswordSerializer
from .models import UserVerifyEmail


class SendCodeEmailApiView(views.APIView):
    def post(self, request):
        print("------------------------------------------------")
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data

            if data.get("code"):
                return Response({"message":"Siz nomalum codeni ro'yhatdan o'tqazmoqchi bo'ldingiz!"},status=400)
            
            edata=UserVerifyEmail.objects.filter(email=data["email"])
            if edata:
                user = edata.order_by("-id").first()
                if user.email_hash is not None and user.expired_time > timezone.now():
                    return Response({"message":"Sizda active token bor!"},status=400)
                elif user.email_hash is not None and user.expired_time < timezone.now():
                    edata.delete()
                if user.code and user.code_expired_time > timezone.now():
                    return Response({"message":"Sizda xali active code bor"},status=400)
                elif user.code and user.code_expired_time < timezone.now():
                    edata.delete()
            

                    

            code = self.generate_code()
            self.send_code(data["email"],code)
            uve = UserVerifyEmail(**data)
            uve.code=code
            uve.code_expired_time=timezone.now()+timedelta(minutes=2)
            uve.save()            

            data={
                "message":"Muvaffaqiyatli!",
                "data":{
                    "email":uve.email
                }
            }
            return Response(data,status=201)
        return Response({"message":"Email xato kiritilgan!"},status=400)

    def send_code(self,email,code):
        # bu portfolio uchunligi uchun...
        print(email,code)
    
    def generate_code(self):
        code = "".join([str(random.randint(0,9)) for _ in range(4)])
        return code

class VerifyEmailApiView(views.APIView):
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            db_data = UserVerifyEmail.objects.filter(email=data["email"]).first()
            if data.get("code") is None:
                return Response({"message":"Siz bu email uchun tasdiqlash kodini jo'natmadingiz!"},status=400)

            if db_data.email_hash is not None and db_data.expired_time > timezone.now():
                    return Response({"message":"Sizda active token bor!"},status=400)

            if int(db_data.trying)>50:
                return Response({"message":"Siz juda ko'p so'rov yuborib qora ro'yhatga tushdingiz.Qora ro'yhatdan chiqguncha ro'yhatdan o'tolmaysiz!"},status=400)


            if data.get("code") == db_data.code and db_data.code is not None:
                if timezone.now()>db_data.code_expired_time:
                    return Response({"message":"Sizning kodingiz vaqti eskirgan. Iltimos qaytadan urunib ko'ring!"},status=400)


                db_data.is_verify=True
                db_data.email_hash=str(uuid.uuid4())
                db_data.expired_time=timezone.now()+timedelta(hours=1)
                db_data.trying=0 
                db_data.save()

                return Response({"message":"Muvaffaqiyatli!","data":{"email":db_data.email,"token":db_data.email_hash}},status=200)

            db_data.trying=db_data.trying + 1
            db_data.save()
            return Response({"message":"Tasdiqlash kodingiz xato!"},status=400)

        return Response({"message":"Nomalum xatolik yuz berdi"},status=400)

class RegisterUser(views.APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data=serializer.validated_data.copy()
            
            data_token=UserVerifyEmail.objects.filter(email_hash=data["token"],email=data["email"]).first()
            print(UserVerifyEmail.objects.all())
            if data_token is not None:
                if data_token.expired_time < timezone.now():
                    return Response({"message":"Siz emailingizni tasdiqlaganingiz uchun berilgan token eskirgan. Emailingizni qayta tasdiqlang!"},status=400)
                
                user=User.objects.create_user(
                    username=data["username"],
                    password=data["password"],
                    email=data["email"],
                    first_name=data.get("first_name",''),
                    last_name=data.get("last_name",'')
                )
                refresh = RefreshToken.for_user(user)

                data={
                    "refresh":str(refresh),
                    "access":str(refresh.access_token)
                }

                return Response(data,status=201)


            return Response({"message":"Bunaqa token va emailga mos keladigan data topilmadi"},status=404) 
            
        return Response({"message":"Nomalum xatolik yuz berdi!"},status=400)

class LoginUser(views.APIView):
    def post(self,request):
        serializer=LoginUserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data=serializer.validated_data.copy()
            user = authenticate(username=data.get("username"),password=data.get("password"))
            if user is not None:
                refresh=RefreshToken.for_user(user)

                data={
                    "refresh":str(refresh),
                    "access":str(refresh.access_token)
                }

                return Response(data,200)

            else:
                return Response({"message":"Bu ma'lumotlarga mos keladigan user topilmadi!"},status=404)
        return Response({"message":"Nomalum xatolik yuz berdi"},status=400)

class ForgotPasswordApiView(views.APIView):
    def post(self,request):
        serializer=ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data=serializer.validated_data

            everify=UserVerifyEmail.objects.filter(email=data.get("email"),email_hash=data.get("token")).first()
            if everify:
                if everify.expired_time > timezone.now():
                    user=User.objects.filter(email=data.get("email")).first()
                    user.set_password(data.get("password"))
                    user.save()

                    return Response({"message":"Siz parolingiz muvaffaqiyatli o'zgartirdiz!"},status=200)

                return Response({"message":"Sizning emailingiz taslanganiga ko'p vaqt bo'lgan. Iltimos yana qayta tasdiqlang!"},status=400)
            return Response({"message":"Bunaqa emailga tegishli token topilmadi."},status=404)
        return Response({"message":"Nomalum xatolik yuz berdi"},status=400)
        
        



