# _*_ coding: utf-8 _*_
__author__ = 'Yujia Lian'
__date__ = '7/4/17 1:22 AM'

from django.conf.urls import url, include
from .views import UserinfoView, UploadImageView, UpdatePwdView, SendEmailCodeView, UpdateEmailView, mylesson
from .views import MyCourseView, MyFavOrgView, MyFavTeacherView, MyFavCourseTView, MyMessageView
from .views import become_instructor, become_instructor_markup_data, become_instructor_api_view,try_for_free

urlpatterns = [
    #User detail page
    url(r'^info/$', UserinfoView.as_view(), name="user_info"),

    #User head upload
    url(r'^image/upload/$', UploadImageView.as_view(), name= 'image_upload'),

    #user center change password
    url(r'^update/pwd/$', UpdatePwdView.as_view(), name='update'),

    #send email verify code
    url(r'^sendemail_code/$', SendEmailCodeView.as_view(), name='sendemail_code'),

    # modify email
    url(r'^update_email/$', UpdateEmailView.as_view(), name='update_email'),

    #My courses
    url(r'^mycourse/$', MyCourseView.as_view(), name='mycourse'),

    #Add Course
    url(r'^addcourse/$', become_instructor, name='addcourse'),

    #My lesson
    url(r'^mylesson/$', mylesson, name='mylesson'),

    # My course collection
    url(r'^myfav/org/$', MyFavOrgView.as_view(), name='myfav_org'),

    # My teacher collection
    url(r'^myfav/teacher/$', MyFavTeacherView.as_view(), name='myfav_teacher'),

    # My course collection
    url(r'^myfav/course/$', MyFavCourseTView.as_view(), name='myfav_course'),

    # My message
    url(r'^mymessage/$', MyMessageView.as_view(), name='mymessage'),

    # Become a Instructor
    url(r'^become_instructor/$', become_instructor, name='become_instructor'),

    # Become a Instructor markup data
    url(r'^become_instructor_markup_data/$', become_instructor_markup_data, name='become_instructor_markup_data'),

    # Become a Instructor api view
    url(r'^become_instructor_api_view/$', become_instructor_api_view, name='become_instructor_api_view'),

    url(r'^try_for_free/$', try_for_free, name='try_for_free')


]