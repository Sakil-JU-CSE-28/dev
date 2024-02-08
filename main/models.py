from django.db import models

# Create your models here.

class Message(models.Model):
    msg = models.CharField(max_length=10000)
    type = models.CharField(max_length = 20)
