import random
import json
import ast      #convert list(type string) to type list
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse,HttpResponseRedirect
from django.utils.translation import get_language
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from operation.models import UserFavorite, UserCourse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from . import Checksum
from .models import PaytmHistory, Checkout, Coupon_code
from courses.models import Course
from users.models import UserProfile
import requests
import urllib
import logging
logger = logging.getLogger(__name__)


# Create your views here.
@login_required(login_url = '/login/')
def cart_list(request):
    user_fav = UserFavorite.objects.filter(user = request.user.id, fav_type=1)
    total_price = 0
    

    try:
        for i in user_fav:
            total_price += int(i.get_course_full_value().get_course_price())

    except Exception as e:
            total_price = ' -'
    

    context = {
        'user_fav':user_fav,
        'total_price':total_price
    }
    return render(request,'cart_list.html',context)

@login_required(login_url = '/login/')
def checkout(request):

    user_fav = UserFavorite.objects.filter(user = request.user.id, fav_type=1)
    
    total_price = 0
    try:
        for i in user_fav:
            total_price += int(i.get_course_full_value().get_course_price())
    except:
        total_price = 0

    user_fav_cources = []

    for i in user_fav:
        user_fav_cources.append(int(i.fav_id))




    number_of_user_fav = 0
    for i in user_fav:
        number_of_user_fav += 1

    if request.method== 'POST':
        try:
            promo_code_input = request.POST['promo_code_input']
            
            try:
                promo_match = Coupon_code.objects.get(code=promo_code_input)
            except:
                promo_match = False

            if promo_match:
                total_price = total_price - promo_match.total_amount
                
        except Exception as e:
            pass

        checkout = Checkout()
        checkout.first_name = request.POST['first_name']
        checkout.last_name = request.POST['last_name']
        checkout.email = request.POST['email']
        checkout.address1 = request.POST['address1']
        checkout.address2 = request.POST.get('address2','')
        checkout.country = request.POST['country']
        checkout.state = request.POST['state']
        checkout.zip = request.POST['zip']
        checkout.shipping_billing_address_same = request.POST.get('shipping_billing_address_same', 'off')

        checkout.cources = user_fav_cources       
        checkout.payment_status = 'pending'        
        checkout.user = request.user

        checkout.total_amount = total_price

        checkout.save()
        user_email=request.POST['email']        

        checkout = Checkout.objects.filter(user=request.user).order_by('-id').first()
        url = reverse('cart_payment:payment')+'?amount='+str(checkout.total_amount)+'&id='+str(checkout.id)+'&email='+str(user_email)
        return HttpResponseRedirect(url)

        # print(user.nick_name)
    context = {
        'total_price':(total_price),
        'user_fav':user_fav,
        'number_of_user_fav':number_of_user_fav,
    }


    return render(request,'checkout.html',context)


@csrf_exempt
@login_required(login_url = '/login/')
def promo_checker(request):
    
    try:
        promo_code = request.GET['promo_code']
        # promo_match = get_object_or_404(Coupon_code,code=promo_code)
        try:
            promo_match = Coupon_code.objects.get(code=promo_code)
            status = 'promo match'
        except:
            promo_match = False
            status = 'not match'

        if promo_match:
            context = {
                'status':status,
                'amount': promo_match.total_amount
            }
        else:
            context = {
                'status':status
            }
        
        return HttpResponse(json.dumps(context))
    except: 
        context = {
            'status':'send valid data'
        }
        return HttpResponse(json.dumps(context))



@login_required(login_url = '/login/')
def payment(request):
    MERCHANT_KEY = settings.PAYTM_MERCHANT_KEY
    MERCHANT_ID = settings.PAYTM_MERCHANT_ID
    get_lang = "/" + get_language() if get_language() else ''
#     CALLBACK_URL = settings.HOST_URL + settings.PAYTM_CALLBACK_URL
    paytm_server_url=settings.PAYTM_SERVER_URL
    # Generating unique temporary ids
    order_id = Checksum.__id_generator__()
    user_email_id=request.GET.get('email')
    logger.debug('payment:user_email_id %s',str(user_email_id))
    host_name=request.scheme+'://'+request.get_host()
    CALLBACK_URL = host_name + settings.PAYTM_CALLBACK_URL
    logger.debug('Callback URL: %s',CALLBACK_URL)


    # bill_amount = 100
    bill_amount = request.GET.get('amount',100)
    order_details = request.GET.get('id',0)
    if bill_amount:
        data_dict = {
            'MID':MERCHANT_ID,
            'ORDER_ID':order_id,
            'TXN_AMOUNT': bill_amount,
            'CUST_ID':str(user_email_id),
            'INDUSTRY_TYPE_ID':settings.PAYTM_INDUSTRY_TYPE_ID,
            'WEBSITE': settings.PAYTM_WEBSITE,
            'CHANNEL_ID':settings.PAYTM_CHANNEL_ID,
            'CALLBACK_URL':CALLBACK_URL,
            'ORDER_DETAILS': str(order_details)
        }
        param_dict = data_dict
        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(data_dict, MERCHANT_KEY)
        return render(request,"payment.html",{'paytmdict':param_dict,'paytm_url':paytm_server_url})
    return HttpResponse("Bill Amount Could not find. ?bill_amount=10")

@login_required(login_url = '/login/')
@csrf_exempt
def response(request):
    logger.debug('inside paytm response')

    if request.method == "POST":
        MERCHANT_KEY = settings.PAYTM_MERCHANT_KEY
        data_dict = {}
        for key in request.POST:
            data_dict[key] = request.POST[key]
        verify = Checksum.verify_checksum(data_dict, MERCHANT_KEY, data_dict['CHECKSUMHASH'])
        paytm_order_id=str(data_dict['ORDERID'])
        logger.debug('Paytm ORDERID: %s',paytm_order_id)
        
        if verify:
            transaction_status_response=get_paytm_payment_transactions_details(paytm_order_id)
            logger.debug('transaction_status_response:%s',transaction_status_response['STATUS'])
            if request.POST['STATUS'] == 'TXN_SUCCESS' and transaction_status_response['RESPCODE']=='01':
                logger.debug('paytm transaction was success')

                PaytmHistory.objects.create(user=request.user, **data_dict)
                

                # If payment done add to user center all courses and upate chackout payment status as done/
                try:
                    checkout = Checkout.objects.filter(id=request.POST['ORDER_DETAILS']).get()
                except:
                    checkout = Checkout.objects.filter(user=request.user).order_by('-id').first()

                course_ids = checkout.cources
                course_ids = ast.literal_eval(course_ids)
                
                for course in list(course_ids):
                    course = Course.objects.filter(id=course).get()
                    UserCourse.objects.create(user=request.user , course=course, enroll_id=generateEnrollmentId())
                try:
                    enrolled_courses = UserFavorite.objects.filter(user = request.user.id, fav_type=1)
                    enrolled_courses.delete();
                except:
                    logger.debug('Cart didn\'t remove')
                # send email to user email if payment done.                
                try:
                                    
                    checkout = Checkout()
                    course = Course()
                    userFavorite = UserFavorite()
                    course_name = []
                    course_price = []
                    course_lessons = {}
                    lesson_teacher = []
                    lesson_name = []
                    course_num = 0
                    class_start_date = []

                    enrolled_courses = UserFavorite.objects.filter(user = request.user.id, fav_type=1)
                    enrollment_created_date = enrolled_courses.order_by('-add_time').first().add_time
                    for i in enrolled_courses:
                        course_price += [int(i.get_course_full_value().get_course_price())]
                        course_name += [i.get_course_full_value().name]
                        lesson_teacher += [i.get_course_full_value().teacher]
                        lesson_name += [i.get_course_full_value().get_course_lesson()]
                        course_num += 1
                    course_lessons['name'] = course_name
                    course_lessons['price'] = course_price


                    cart_item_len = len(enrolled_courses)
                    userCourse = UserCourse.objects.filter(user=request.user.id).order_by('-id')[:cart_item_len]
                    userCourseEnrollmentId = []
                    for i in userCourse:
                        userCourseEnrollmentId.append(str(i.enroll_id))

                    checkout = Checkout.objects.filter(user=request.user).order_by('-id').first()
                    customer_name = checkout.first_name

                    subject, from_email, to = 'Enrollment Confirmations', settings.EMAIL_FROM, [request.user.email]
                    text_content = 'This is an important message.'
                    html_content = render_to_string('email_template.html', {
                        'customer_name':request.user.username,
                        'first_name':checkout.first_name,
                        'last_name':checkout.last_name,
                        'gender':request.user.gender,
                        'total_price': checkout.total_amount,
                        'enrollment_no':enrolled_courses.count(),
                        'enrollment_created_date':enrollment_created_date,
                        'course_num':range(course_num),
                        'course_name':course_name,
                        'course_price':course_price,
                        'course_lessons':course_lessons,
                        'lesson_teacher':lesson_teacher,
                        'lesson_name':lesson_name,
                        'promotion_price':0,
                        'shipping_price':0,
                        'order_price':checkout.total_amount + 0 + 0,
                        'class_start_date':class_start_date,
                        'enrolled_courses':enrolled_courses,
                        'userCourseEnrollmentId':userCourseEnrollmentId
                    }) 
                    
                    to = str(to[0])
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [to,])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                except Exception as e:
                    logger.debug('Error with Sending Email %s',e)
                return render(request,"response.html",{"paytm":data_dict,"msg":'Succesfull',"reason":request.POST['RESPMSG']})
            else:
                try:
                    PaytmHistory.objects.create(user=request.user, **data_dict)
                except:
                    pass

                return render(request,"response.html",{"paytm":data_dict,"msg":'Canceled',"reason":request.POST['RESPMSG']})
        else:
            return HttpResponse("checksum verify failed")
    return HttpResponse(status=200)


def generateEnrollmentId():
    return 'INF'+''.join(map(str,random.sample(range(1, 9), 8)))


def get_paytm_payment_transactions_details(paytm_order_id):
    MERCHANT_ID = settings.PAYTM_MERCHANT_ID
    MERCHANT_KEY = settings.PAYTM_MERCHANT_KEY
    URL = settings.PAYTM_TRANSACTION_STATUS_URL
    data_dict = {
            'MID':MERCHANT_ID,
            'ORDER_ID':paytm_order_id
        }
    param_dict = data_dict
    checksum_hash=Checksum.generate_checksum(data_dict, MERCHANT_KEY)
    param_dict['CHECKSUMHASH'] = urllib.quote(checksum_hash)
    payload = json.dumps(param_dict)
#     logger.debug('payload: %s',payload)
    link = URL+'?JsonData='+payload
    logger.debug(link)
    f=urllib.urlopen(link)
    myfile = f.read()
    response_data=json.loads(myfile)
    logger.debug('getTxnStatus API response: %s',response_data)
    if "MID" in response_data:
        response_data.pop("MID")
    if "REFUNDAMT" in response_data:
        response_data.pop("REFUNDAMT")
    return response_data


def test(request):
    return HttpResponse('')
    # return render(request,'response.html')