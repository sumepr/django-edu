from django.contrib import admin

# Register your models here.

# Register your models here.

from .models import UserProfile,InstructorCourse

admin.site.register([UserProfile, InstructorCourse])