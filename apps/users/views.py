#_*_ encoding:utf-8 _*_
import random
import json, datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
# Create your views here.
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
from django.utils.timezone import now
from .models import UserProfile, EmailVerifyRecord
from .forms import LoginForm, RegisterForm, ForgetForm, ModifyPwdForm, UploadImageForm
from .forms import UserInfoForm
from utils.email_send import send_register_email
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from utils.mixin_utils import LoginRequiredMixin
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from operation.models import UserCourse, UserFavorite, UserMessage
from organization.models import CourseOrg, Teacher
from courses.models import Course, Lesson
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from .models import Banner
from users.models import InstructorCourse
from django.core.urlresolvers import reverse
from courses.models import CourseCategory, Course
from MxOnline.settings import LIVE_ONLINE_COURSE
import logging
logger = logging.getLogger(__name__)


class CustomBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user = UserProfile.objects.get(Q(username=username)|Q(email=username))
            if user.check_password(password):
                return user
        except Exception as e:
            return None


class ActiveUserView(View):

    def get(self, request, active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                user = UserProfile.objects.get(email=email)
                user.is_active = True
                user.save()
        else:
            return render(request, "active_fail.html")
        return render(request, "login.html")


class RegisterView(View):

    def get(self, request):
        register_form = RegisterForm()
        return render(request, "register.html", {'register_form':register_form})

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            user_name = request.POST.get("email", "")
            if UserProfile.objects.filter(email=user_name):
                return render(request, "register.html", {"register_form": register_form, "msg": "User name you want to user already exist!"})
            pass_word = request.POST.get("password", "")
            user_profile = UserProfile()
            user_profile.username = user_name
            user_profile.email = user_name
            user_profile.password = make_password(pass_word)
            user_profile.is_active = False
            user_profile.save()

            #send welcome message
            user_message = UserMessage()
            user_message.user = user_profile.id
            user_message.message = "Welcome to Infyni Higher education! Start learning today!"
            user_message.save()


            send_register_email(user_name, "register")
            return render(request, "send_success.html")
        else:
            return render(request, 'register.html', {'register_form': register_form})


class LogoutView(View):
    """
    logout
    """
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse("index"))


class LoginView(View):

    def get(self, request):
        return render(request, "login.html", {})

    def post(self, request):
        login_form = LoginForm(request.POST)
        self.next = request.POST.get('next','/')
        logger.debug(self.next)
        
        if login_form.is_valid():
            user_name = request.POST.get("username", "")
            pass_word = request.POST.get("password", "")
            user = authenticate(username=user_name, password=pass_word)
            if user is not None:
                if user.is_active:
                    login(request, user)

                    return HttpResponseRedirect(self.next,reverse('index'))
                else:
                    return render(request, "login.html",
                                  {"msg": "User exist but does not active yet!"})
            else:
                return render(request, "login.html",
                              {"msg": "Username or password you entered is invalid, please try again!"})
        else:
            return render(request, "login.html", {"login_form": login_form})


class ForgetPwdView(View):
    def get(self, request):
        forget_form = ForgetForm()
        return render(request, "forgetpwd.html",{"forget_form": forget_form})

    def post(self, request):
        forget_form = ForgetForm(request.POST)#passing a dict
        if forget_form.is_valid():
            email = request.POST.get("email", "")

            all_records = UserProfile.objects.all()
            all_email = []
            for record in all_records:
                all_email.append(record.email)
            if email in all_email:
                send_register_email(email, "forget")
                return render(request, "send_success.html")
            else:
                return render(request, "forgetpwd.html",
                              {"forget_form": forget_form, "msg": "The email you entered does not match!"})
        return render(request, "forgetpwd.html", {"forget_form": forget_form})


class ResetView(View):

    def get(self, request, active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                return render(request, "password_reset.html", {"email": email})
        else:
            return render(request, "active_fail.html")
        return render(request, "login.html")


class ModifyPwdView(View):

    """
    change user's password
    """

    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", "")
            pwd2 = request.POST.get("password2", "")
            email = request.POST.get("email", "")
            if pwd1 != pwd2:
                return render(request, "password_reset.html", {"email": email, "msg": "The password you entered does not match!"})
            user = UserProfile.objects.get(email=email)
            user.password = make_password(pwd1)
            user.save()
            #Sending greeting information
            return render(request, "login.html")
        else:
            email = request.POST.get("email", "")
            return render(request, "password_reset.html", {"email": email, "modify_form": modify_form})


class UserinfoView(LoginRequiredMixin, View):
    """
    user information
    """
    def get(self, request):
        return render(request, 'usercenter-info.html',{})

    def post(self, request):
        user_info_form = UserInfoForm(request.POST, instance=request.user)
        if user_info_form.is_valid():
            user_info_form.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse(json.dumps(user_info_form.errors),
                                content_type='application/json')



class UploadImageView(LoginRequiredMixin, View):
    """
    user change avatar
    """
    def post(self, request):
        image_form = UploadImageForm(request.POST, request.FILES, instance=request.user)
        if image_form.is_valid():
            image_form.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail"}', content_type='application/json')



class UpdatePwdView(View):

    """
    change user's password in user center
    """

    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", "")
            pwd2 = request.POST.get("password2", "")
            if pwd1 != pwd2:
                return HttpResponse('{"status":"fail", "msg":"Passwords does not identical!"}', content_type='application/json')
            user = request.user
            user.password = make_password(pwd1)
            user.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse(json.dumps(modify_form.errors),
                                content_type='application/json')


class SendEmailCodeView(LoginRequiredMixin, View):
    """
    send email verify code
    """
    def get(self, request):
        email = request.GET.get('email','')

        if UserProfile.objects.filter(email=email):
            return HttpResponse('{"status":"fail"}','{"msg":"Email already been used."}', content_type='application/json')
        else:
            send_register_email(email, "update_email")
            return HttpResponse('{"status":"success"}', content_type='application/json')


class UpdateEmailView(LoginRequiredMixin, View):
    def post(self, request):
        #change personal email
        email = request.POST.get('email','')
        code = request.POST.get('code','')
        existed_record = EmailVerifyRecord.objects.filter(email=email, code=code, send_type='update_email')
        if existed_record:
            user = request.user
            user.email = email
            user.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"email":"Verify code not match!"}', content_type='application/json')


class MyCourseView(LoginRequiredMixin, View):
    """
    My courses page
    """
    def get(self, request):
        user_courses = UserCourse.objects.filter(user=request.user)
        for i in user_courses:
            course = i.course
            break;
        # lesson = Lesson.objects.filter(course=course).first()
        lesson_live_class_from = ""
        lesson_live_class_to = ""
        try:
            lesson = Lesson.objects.filter(course=course).first()
            lesson_live_class_from = lesson.live_class_from
            lesson_live_class_to = lesson.live_class_to
        except:
            lesson_live_class_from = ""
            lesson_live_class_to = ""
        return render(request, 'usercenter-mycourse.html', {
            "user_courses": user_courses,
            "first_lesson_start_from": lesson_live_class_from,
            "first_lesson_ends_at": lesson_live_class_to,
            'online_course' : LIVE_ONLINE_COURSE,
        })
        
@login_required(login_url = '/login/')
@csrf_exempt
def mylesson(request):

    if request.method == 'POST':
        try:
            if request.POST['type'] == 'remove':
                id = int(request.POST['id'])
                lesson = InstructorCourse.objects.get(id=id).delete()

            if request.POST['type'] == 'update_start':
                id = int(request.POST['id'])
                time = int(request.POST['updated_time'])
                class_start = datetime.datetime.fromtimestamp(time/1000.0)
                lesson = InstructorCourse.objects.filter(id=id).update(class_start=class_start)

            if request.POST['type'] == 'update_end':
                id = int(request.POST['id'])
                time = int(request.POST['updated_time'])
                class_end = datetime.datetime.fromtimestamp(time/1000.0)
                # return HttpResponse('got data ') 
                lesson = InstructorCourse.objects.filter(id=id).update(class_end=class_end)

            if request.POST['type'] == 'update_price':
                id = request.POST['id']
                price = request.POST['updated_price']
                lesson = InstructorCourse.objects.filter(id=id).update(price=price)

        except Exception as e:
            return HttpResponse('Error is ',e)  

        return HttpResponse('Done')

    lessons = InstructorCourse.objects.filter(user=request.user)
    context = {
        "lessons":lessons,
    }
    return render(request,'usercenter-mylesson.html',context)




class MyFavOrgView(LoginRequiredMixin, View):
    """
    My favor collection page
    """

    def get(self, request):
        org_list = []
        fav_orgs = UserFavorite.objects.filter(user=request.user, fav_type=2)
        for fav_org in fav_orgs:
            org_id = fav_org.fav_id
            org = CourseOrg.objects.get(id=org_id)
            org_list.append(org)
        return render(request, 'usercenter-fav-org.html', {
            "org_list": org_list
        })


class MyFavTeacherView(LoginRequiredMixin, View):
    """
    My favor collection page
    """

    def get(self, request):
        teacher_list = []
        fav_teachers = UserFavorite.objects.filter(user=request.user, fav_type=3)
        for fav_teacher in fav_teachers:
            teacher_id = fav_teacher.fav_id
            teacher = Teacher.objects.get(id=teacher_id)
            teacher_list.append(teacher)
        return render(request, 'usercenter-fav-teacher.html', {
            "teacher_list": teacher_list
        })


class MyFavCourseTView(LoginRequiredMixin, View):
    """
    My favor collection page
    """

    def get(self, request):
        course_list = []
        fav_courses = UserFavorite.objects.filter(user=request.user, fav_type=1)
        for fav_course in fav_courses:
            course_id = fav_course.fav_id
            course = Course.objects.get(id=course_id)
            course_list.append(course)
        return render(request, 'usercenter-fav-course.html', {
            "course_list": course_list
        })


class MyMessageView(LoginRequiredMixin, View):
    """
    My message
    """
    def get(self, request):
        all_messsages = UserMessage.objects.filter(user=request.user.id)

        #mark unread messages as read when user check the message box
        all_unread_messages = UserMessage.objects.filter(user=request.user.id, has_read=False)
        for unread_message in all_unread_messages:
            unread_message.has_read = True
            unread_message.save()

        # paging messages
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_messsages, 5, request=request)
        messages = p.page(page)
        return render(request, 'usercenter-message.html', {
            "messages":messages
        })


class IndexView(View):
    #infyni online main page
    logger.debug('Inside IndexView MxOnline')
    def get(self, request):
        #get slide picture
        all_banners = Banner.objects.all().order_by('index')
        courses = Course.objects.filter(is_banner=False)[:6]
        banner_courses = Course.objects.filter(is_banner=True)[:3]
        course_orgs = CourseOrg.objects.all()[:15]
        return render(request, 'index.html', {
            'all_banners':all_banners,
            'courses':courses,
            'banner_courses':banner_courses,
            'course_orgs':course_orgs
        })

@login_required(login_url='/login/')
def become_instructor(request):
    if request.method == "GET":
        categories = CourseCategory.objects.all().order_by('id')
        return render(request, 'usercenter-addcourse.html', {'categories': categories})

@login_required(login_url='/login/')
def become_instructor_markup_data(request):

    step_no = request.GET.get('step_no',1)
    context = {
        "step_no": int(step_no)
    }
    step_no = int(step_no)
    if step_no == 1:
        category_list = 'show all category list'
        course_category = CourseCategory.objects.all()

        context = {
            "course_category":course_category,
            "step_no": int(step_no)
        }

    if step_no == 2:
        try:
            category_id =  int(request.GET['category_id'])
            course_category =  CourseCategory.objects.filter(id=category_id).first()

            category_obj = get_object_or_404(CourseCategory, id=category_id)
            courses = Course.objects.filter(course_category=category_obj)
            
        except:
            return HttpResponse('error')
            # pass

        context = {
            "step_no": int(step_no),
            "courses" : courses,
            "course_category":course_category
        }

    if step_no == 3:
        try:
            course_id = int(request.GET['course_id'])
            course_obj = get_object_or_404(Course, id=course_id)
            lessons = Lesson.objects.filter(course=course_obj)
        except Exception as e:
            return HttpResponse(e)
            # pass

        context = {
            "step_no": int(step_no),
            "lessons": lessons,
            "course_obj":course_obj
        }

    if step_no == 4:

        try:
            try:
                hidden_id_lesson_start_date_str = str(request.GET['hidden_id_lesson_start_date_str'])
                hidden_id_lesson_end_date_str = str(request.GET['hidden_id_lesson_end_date_str'])
                hidden_id_price = str(request.GET['hidden_id_price'])
                
            except:
                hidden_id_lesson_start_date_str = ""
                hidden_id_lesson_end_date_str = ""
                hidden_id_price = ""
            lesson_id = int(request.GET['lesson_id'])
            lesson = Lesson.objects.get(id=lesson_id)

            course_obj = lesson.course
        except:
            return HttpResponse('error')
            # pass

        context = {
            "lesson": lesson,
            "step_no": int(step_no),
            "course_obj":course_obj,
            "lesson_start_date_str":hidden_id_lesson_start_date_str[:-1],  #last word z shouldn't be there
            "lesson_end_date_str":hidden_id_lesson_end_date_str[:-1],   #last word z shouldn't be there
            "hidden_id_price":hidden_id_price
        }

    if step_no == 5:
        try:
            lesson_start_date_str = str(request.GET['lesson_start_date_str'])
            lesson_end_date_str = str(request.GET['lesson_end_date_str'])
            lesson_id = int(request.GET['lesson_id'])
            lesson = Lesson.objects.get(id=lesson_id)
            price = int(request.GET['price'])
            class_from_timestamp = int(request.GET['class_from'])
            class_from = datetime.datetime.fromtimestamp(class_from_timestamp/1000.0)
 
            class_to_timestamp = int(request.GET['class_to'])
            class_to = datetime.datetime.fromtimestamp(class_to_timestamp/1000.0)

        except Exception as e:

            return HttpResponse('error')
            # pass

        context = {
            'lesson_start_date_str':lesson_start_date_str,
            'lesson_end_date_str':lesson_end_date_str,

            "lesson": lesson,
            "price": price,
            "class_from": class_from,
            "class_to": class_to,
            "class_from_timestamp": class_from_timestamp,
            "class_to_timestamp": class_to_timestamp, 
            "step_no": int(step_no)
        }
    if step_no == 6:
        try:
            lesson_id = int(request.GET['lesson_id'])
            price = int(request.GET['price'])
            class_start = datetime.datetime.fromtimestamp(int(request.GET['class_start'])/1000.0)
            class_end = datetime.datetime.fromtimestamp(int(request.GET['class_end'])/1000.0)
            # lesson = get_object_or_404(Lesson,pk=lesson_id),
            lesson = Lesson.objects.get(id=lesson_id)
            InstructorCourse.objects.create(
                user = request.user,
                lesson = lesson,
                price = price,
                class_start = class_start,
                class_end = class_end
            )
            try:
                user = UserProfile.objects.filter(id=request.user.id).update(is_instructor=True)
            except:
                print('user can not be a instructor')

            try:
                from_email, to_email = settings.EMAIL_FROM, request.user.email

                header = '<h2><b>Thank You For Adding Lesson</b></h2><br>'
                header = header + '<b>Here are you lesson info</b><br>'
                Course_Category = '<b>Category</b> : '+lesson.course.course_category.name+'<br>'
                Course_Name = '<b>Course</b>  : '+lesson.course.name+'<br>'
                Lesson_Name = '<b>Lesson</b> : '+lesson.name+'<br>'

                try:
                    course_Details = '<b>Course Details</b> : '+lesson.course.datail+'<br>'
                except:
                    course_Details = '<b>Course Details</b> : -- <br>'
                try:
                    lesson_Details = '<b>Lesson Details</b> : '+lesson.detail+'<br>'
                except:
                    lesson_Details = '<b>Lesson Details</b> : -- <br>'
                    

                Class_From = '<b>Class From</b> : '+str(lesson.live_class_from)+'<br>'
                Class_To = '<b>Class To</b> : '+str(lesson.live_class_to)+'<br>'

                msg_body  = header + Course_Category + Course_Name+ course_Details + Lesson_Name + lesson_Details + Class_From + Class_To

                print(msg_body)

                msg = EmailMultiAlternatives('Add Course Done','', from_email, [to_email])
                # msg = EmailMultiAlternatives('Add Course Done', msg_body , from_email, [to_email,'webcodestar@gmail.com'])
                msg.attach_alternative(msg_body, "text/html")
                msg.send()
            except Exception as e:
                print('Email Didnt send ',e )
                pass
            context = {}
            return HttpResponse('Done')
        except Exception as e:
            print(e)
            return HttpResponse('error')

    return render(request, 'usercenter-addcourse_markup_data.html', context)

def become_instructor_api_view(request):
    # course_category = CourseCategory.objects.all()
    course_category = CourseCategory.objects.values_list('name')
    context = {
        'course_category':course_category
    }
    return JsonResponse(context)
    # return render(request, 'usercenter-addcourse_api_view.html', context)


def generateEnrollmentId():
    return 'INF'+''.join(map(str,random.sample(range(1, 9), 8)))




@csrf_exempt
@login_required(login_url='/login/')
def try_for_free(request):
    if request.method ==  'POST':
        try:
            course_id = request.POST['course_id']
            course = Course.objects.filter(id=course_id).first()
            lesson = Lesson.objects.filter(course=course)
            
            course_name = course.name
            EnrollmentId=generateEnrollmentId()
            # UserCourse.objects.create(user=request.user , course=course, enroll_id=EnrollmentId)
            user_course = UserCourse(user=request.user , course=course, enroll_id=EnrollmentId)
            
            user_course.save()
            # user_course.id
            enrolled_courses = Course.objects.filter(id=course_id)
            user_course_count = UserCourse.objects.filter(user=request.user).count()


            try:
                subject, from_email, to = 'Enrollment Confirmations', settings.EMAIL_FROM, [request.user.email]
                text_content = 'This is an important message.'
                html_content = render_to_string('try_fo_free_email_template.html', {
                    'customer_name':request.user.username,
                    'first_name':request.user.first_name,
                    'last_name':request.user.last_name,
                    'gender':request.user.gender,
                    'total_price': 'Free',
                    'enrollment_no':user_course_count,
                    'enrollment_created_date':now(),
                    'course_num':course_id,
                    'course_name':course_name,
                    'course_price':'Free',
                    'course_lessons':lesson,
                    # 'lesson_teacher':lesson_teacher,
                    # 'lesson_name':lesson_name,
                    'promotion_price':0,
                    'shipping_price':0,
                    'order_price':'Free',
                    # 'class_start_date':class_start_date,
                    'enrolled_courses':enrolled_courses,
                    'EnrollmentId':EnrollmentId
                }) 
                
                to = str(to[0])
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to,])
                msg.attach_alternative(html_content, "text/html")
                msg.send()

            except Exception as e:
                print('Email Didnt send ',e )
                pass
        except:
            return HttpResponse('Error')            

    return HttpResponse('Done')


def page_not_found(request):
    #404 page processing function
    from django.shortcuts import render_to_response
    response = render_to_response('404.html', {})
    response.status_code = 404
    return response


def page_error(request):
    #404 page processing function
    from django.shortcuts import render_to_response
    response = render_to_response('500.html', {})
    response.status_code = 500
    return response
