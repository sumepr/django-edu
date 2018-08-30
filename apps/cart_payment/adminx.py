# _*_ coding: utf-8 _*_
__author__ = 'Yujia Lian'
__date__ = '6/6/17 1:52 AM'
import xadmin
from .models import PaytmHistory,Checkout,Coupon_code
from xadmin import views
from xadmin.layout import Fieldset, Main, Side, Row
from xadmin.plugins.auth import UserAdmin



class Coupon_code_Admin(object):
    list_display = ['code','total_amount']
    search_fields =  ['code','total_amount']
    list_filter =  ['code','total_amount']
    


xadmin.site.register(Coupon_code, Coupon_code_Admin)