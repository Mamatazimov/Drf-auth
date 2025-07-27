from django.db import models



class UserVerifyEmail(models.Model):
    email = models.EmailField()
    is_verify = models.BooleanField(default=False)
    email_hash = models.TextField(blank=True,null=True,unique=True)
    expired_time = models.DateTimeField(null=True,blank=True)
    code = models.CharField(max_length=5,blank=True,null=True)
    code_expired_time = models.DateTimeField(blank=True,null=True)
    trying = models.IntegerField(default=0)

    def __str__(self):
        return self.email


    










