from django.contrib import admin
from .models import PaytmHistory,Checkout

# Register your models here.
admin.site.register([PaytmHistory,Checkout])