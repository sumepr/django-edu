# _*_ coding: utf-8 _*_
__author__ = 'Yujia Lian'
__date__ = '6/15/17 1:45 PM'

from random import Random
from users.models import EmailVerifyRecord
from MxOnline.settings import EMAIL_FROM,ADMIN_EMAIL
from django.core.mail import send_mail
from MxOnline.settings import HOST_URL


def send_register_email(email, send_type='register'):
    email_record = EmailVerifyRecord()
    if send_type == 'update_email':
        code = random_str(4)
    else:
        code = random_str(16)
    email_record.code = code
    email_record.email = email
    email_record.send_type = send_type
    email_record.save()

    email_title = ""
    email_body = ""

    if send_type == 'register':
        email_title = "Welcome to Infyni"
        email_body = "Please click the link below to active your account: {0}/active/{1}".format(HOST_URL,code)

        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        send_status = send_mail(email_title, email_body, EMAIL_FROM, [ADMIN_EMAIL])
        print(send_status)
        if send_status:
            pass
    elif send_type == 'forget':
        email_title = "Infyni Higher education reset password link"
        email_body = "Please click the link below to reset your password: {0}/reset/{1}".format(HOST_URL,code)
        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
    elif send_type == 'update_email':
        email_title = "Infyni Higher education update email link"
        email_body = "Here is you Infyni Higher education reset email code: {0}".format(code)
        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])


def random_str(randomlength=8):
    str = ''
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str
