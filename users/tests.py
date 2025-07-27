import uuid
import time
from django.utils import timezone
from datetime import timedelta
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from users.models import UserVerifyEmail



class SendCodeApiTestCase(APITestCase):
    def setUp(self):
        self.data={
            "email":"test@mail.com"
        }

    def test_send_code(self):
        response = self.client.post(reverse("users:send_code_email"),self.data,format="json")

        self.assertEqual(response.status_code,201)
        self.assertEqual(response.data["data"]["email"],"test@mail.com")
        self.assertEqual(response.data["message"],"Muvaffaqiyatli!")

    def test_send_code_has_active_code(self):
        self.client.post(reverse("users:send_code_email"),self.data,format="json")
        response = self.client.post(reverse("users:send_code_email"),self.data,format="json")

        self.assertEqual(response.status_code,400)
        self.assertEqual(response.data["message"],"Sizda xali active code bor")

    def test_send_code_has_active_token(self):
        email=UserVerifyEmail(email="test@mail.com",is_verify=True,email_hash=str(uuid.uuid4()),expired_time=timezone.now()+timedelta(hours=1))
        email.save()
        
        response = self.client.post(reverse("users:send_code_email"),self.data,format="json")

        self.assertEqual(response.status_code,400)
        self.assertEqual(response.data["message"],"Sizda active token bor!")
    
    def test_send_code_has_inactive_code(self):
        email = UserVerifyEmail(email="test@mail.com",code=1234,code_expired_time=timezone.now()+timedelta(seconds=1))
        email.save()
        time.sleep(3)

        response = self.client.post(reverse("users:send_code_email"),self.data,format="json")
        
        email = UserVerifyEmail.objects.filter(email="test@mail.com")

        self.assertEqual(response.status_code,201)
        self.assertEqual(response.data["data"]["email"],"test@mail.com")
        self.assertEqual(len(email),1)


    def test_send_code_has_inactive_token(self):
        email = UserVerifyEmail(email="test@mail.com",email_hash=str(uuid.uuid4()),expired_time=timezone.now()+timedelta(seconds=1))
        email.save()
        time.sleep(3)

        response = self.client.post(reverse("users:send_code_email"),self.data,format="json")
        
        email = UserVerifyEmail.objects.filter(email="test@mail.com")
        

        self.assertEqual(response.status_code,201)
        self.assertEqual(response.data["data"]["email"],"test@mail.com")
        self.assertEqual(len(email),1)
        

    def test_send_invalid_email(self):
        data={
            "email":"testmailcom"
        }
        response = self.client.post(reverse("users:send_code_email"),data,format="json")
        self.assertNotEqual(response.status_code,201)

    def test_gives_other_fields(self):
        data={
            "email":"test@mail.com",
            "token":"qwertyuiop"
        }
        response = self.client.post(reverse("users:send_code_email"),data,format="json")
        db_data=UserVerifyEmail.objects.filter(email=data["email"]).first()
        
        self.assertEqual(response.status_code,400)
        self.assertTrue(db_data is None)

    def test_gives_code(self):
        data={
            "email":"test@mail.com",
            "code":1234
        }
        
        response = self.client.post(reverse("users:send_code_email"),data,format="json")
        db_data = UserVerifyEmail.objects.filter(email=data["email"]).first()
        self.assertEqual(response.status_code,400)
        self.assertTrue(db_data is None)

        
class VerifyEmailApiTestCase(APITestCase):
    def setUp(self):
        self.data={
            "email":"test@mail.com",
            "code":1234
        }
        self.user = UserVerifyEmail(email="test@mail.com",code=1234,code_expired_time=timezone.now()+timedelta(hours=1))
        self.user.save()


    def test_verify_email(self):
        response = self.client.post(reverse("users:verify_email"),self.data,format="json")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data["data"]["email"],"test@mail.com")
        self.assertTrue(response.data.get("data",{}).get("token"))

    def test_invalid_email_code(self):
        response = self.client.post(reverse("users:verify_email"),{"email":"test@mail.com","code":1111},format="json")
        self.assertNotEqual(response.status_code,200)
        self.assertTrue(response.data.get("message",{}))

    def test_trying(self):
        for _ in range(51):
            self.client.post(reverse("users:verify_email"),{"email":"test@mail.com","code":1111},format="json") 
        else:
            response = self.client.post(reverse("users:verify_email"),self.data,format="json")

        self.assertNotEqual(response.status_code,200)
        self.assertFalse(response.data.get("token",{}))
    

    def test_none_code(self):
        response = self.client.post(reverse("users:verify_email"),{"email":"test@mail.com"},format="json")
        self.assertEqual(response.status_code,400)
        self.assertEqual(len(response.data),1)

    def test_verify_email_has_valid_token(self):
        self.user.email_hash = str(uuid.uuid4())
        self.user.expired_time = timezone.now()+timedelta(hours=1)
        self.user.save()

        response = self.client.post(reverse("users:verify_email"),self.data,format="json")

        self.assertEqual(response.status_code,400)
        self.assertEqual(response.data.get("message"),"Sizda active token bor!")

    def test_verify_email_has_invalid_token(self):
        self.user.email_hash = str(uuid.uuid4())
        self.user.expired_time = timezone.now()+timedelta(seconds=1)
        self.user.save()

        time.sleep(3)

        response = self.client.post(reverse("users:verify_email"),self.data,format="json")

        self.assertEqual(response.status_code,200)
        self.assertTrue(response.data.get("data",{}).get("token"))
    
    def test_not_exist_email(self):
        response = self.client.post(reverse("users:verify_email"),{"email":"aaaaaaaaa","code":1234},format="json")
        self.assertEqual(response.status_code,400)

class RegisterUserApiTestCase(APITestCase):
    def setUp(self):
        self.data={
            "email":"test@mail.com",
            "token":"qwertyuiop",
            "username":"Testbek",
            "first_name":"Testjon",
            "last_name":"Testtoyov",
            "password":"tst1234",
            "confirm_password":"tst1234"
        }

        self.email_token = UserVerifyEmail(email="test@mail.com",email_hash="qwertyuiop",expired_time=timezone.now()+timedelta(hours=1))
        
    
    def test_register(self):
        self.email_token.save()
        response = self.client.post(reverse("users:register"),self.data,format="json")
        self.assertEqual(response.status_code,201)
        self.assertIn("refresh",response.data)
        self.assertIn("access",response.data)

    def test_invalid_token(self):
        self.email_token.save()
        data = self.data
        data["token"] = "asdfghjkl"
        response = self.client.post(reverse("users:register"),data,format="json")

        self.assertEqual(response.status_code,404)
        self.assertNotIn("refresh",response.data)
        self.assertNotIn("access",response.data)

    def test_expired_token(self):
        
        self.email_token.expired_time=timezone.now()+timedelta(seconds=1)
        self.email_token.save()

        time.sleep(3)

        response = self.client.post(reverse("users:register"),self.data,format="json")
        self.assertEqual(response.status_code,400)

        self.assertIn("message",response.data)

    def test_invalid_data(self):
        self.email_token.save()
        data = self.data
        data["email"]="testmailcom"
        response = self.client.post(reverse("users:register"),data,format="json")
        self.assertEqual(response.status_code,400)

        data = self.data
        data["username"]="com"
        response = self.client.post(reverse("users:register"),data,format="json")
        self.assertEqual(response.status_code,400)

        data = self.data
        data["username"]="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaatestmailcom"
        response = self.client.post(reverse("users:register"),data,format="json")
        self.assertEqual(response.status_code,400)

    def test_username_email_exists(self):
        self.email_token.save()
        self.client.post(reverse("users:register"),self.data,format="json")
        response = self.client.post(reverse("users:register"),self.data,format="json")
        self.assertEqual(response.status_code,400)

class LoginUserApiTestCase(APITestCase):
    def setUp(self):
        data={
            "email":"test@mail.com",
            "token":"qwertyuiop",
            "username":"Testbek",
            "first_name":"Testjon",
            "last_name":"Testtoyov",
            "password":"tst1234",
            "confirm_password":"tst1234"
        }

        self.email_token = UserVerifyEmail(email="test@mail.com",email_hash="qwertyuiop",expired_time=timezone.now()+timedelta(hours=1))
        self.email_token.save()
        self.client.post(reverse("users:register"),data,format="json")

        self.data={
            "username":"Testbek",
            "password":"tst1234"
        }

        
    def test_login(self):
        response = self.client.post(reverse("users:login"),self.data,format="json")
        self.assertEqual(response.status_code,200)
        self.assertIn("refresh",response.data)
        self.assertIn("access",response.data)

    def test_invalid_data(self):
        data=self.data
        data['username']="testbek"
        response = self.client.post(reverse("users:login"),self.data,format="json")
        self.assertNotEqual(response.status_code,200)
        self.assertNotIn("refresh",response.data)
        self.assertNotIn("access",response.data)

class ForgotPasswordApiTestCase(APITestCase):
    def setUp(self):
        data={
            "email":"test@mail.com",
            "token":"qwertyuiop",
            "username":"Testbek",
            "first_name":"Testjon",
            "last_name":"Testtoyov",
            "password":"tst1234",
            "confirm_password":"tst1234"
        }

        self.email_token = UserVerifyEmail(email="test@mail.com",email_hash="qwertyuiop",expired_time=timezone.now()+timedelta(hours=1))
        self.email_token.save()
        self.client.post(reverse("users:register"),data,format="json")

        self.data={
            "email":"test@mail.com",
            "password":"tst1234",
            "token":"qwertyuiop",
            "confirm_password":"tst1234"
        }
        
    def test_change_password(self):
        response=self.client.post(reverse("users:forgot-password"),self.data,format="json")
        print(response.data)
        self.assertEqual(response.status_code,200)

    def test_invalid_data(self):
        self.data["email"]="salommailcom"
        response=self.client.post(reverse("users:forgot-password"),self.data,format="json")
        self.assertNotEqual(response.status_code,200)
 


