#_*_ encoding:utf-8 _*_
from __future__ import unicode_literals
from datetime import datetime
from organization.models import CourseOrg, Teacher
from django.db import models
from DjangoUeditor.models import UEditorField
from django.utils.dateparse import parse_date, parse_datetime, parse_time
# Create your models here.


class CourseCategory(models.Model):
    name=models.CharField(max_length=50, verbose_name=u"Course Category")
    description=models.CharField(max_length=50, verbose_name=u"Description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = u"Course Category"
        verbose_name_plural = verbose_name
    
    def __unicode__(self):
        return self.name

class Course(models.Model):
    course_org = models.ForeignKey(CourseOrg, verbose_name="Course organization", null=True, blank=True)
    course_category = models.ForeignKey(CourseCategory, verbose_name="Course Category", null=True, blank=True)
    name = models.CharField(max_length=50, verbose_name=u"Course name")
    teacher = models.ForeignKey(Teacher, verbose_name="Professor", null=Teacher, blank=True)
    desc = models.CharField(max_length=300, verbose_name=u"Course description")
    category = models.CharField(default=u"back end",max_length=20, verbose_name=u"Course category")
    detail = UEditorField(verbose_name="Course detail",width=600, height=300, imagePath="courses/ueditor/", filePath="courses/ueditor/", default="")
    is_banner = models.BooleanField(default=False, verbose_name="add banner")
    degree = models.CharField(choices=(("cj", "Begining level"),("zj", "Middle level"), ("gj", "High level")),
                              max_length=2)
    learn_times = models.IntegerField(default=0, verbose_name=u"Learning time(In minutes)")
    students = models.IntegerField(default=0, verbose_name=u"Total enrolled students")
    fav_nums = models.IntegerField(default=0, verbose_name=u"Favorite number")
    image = models.ImageField(upload_to="courses/%Y/%m", verbose_name=u"Cover", max_length=100)
    click_num = models.IntegerField(default=0, verbose_name=u"Click times")
    add_time = models.DateTimeField(default=datetime.now,verbose_name=u"Add time")
    tags = models.CharField(default="", verbose_name="Course tag", max_length=100)
    you_need_know = models.CharField(default="", max_length=300, verbose_name="Course requirement")
    teacher_notice = models.CharField(default="", max_length=300, verbose_name="Teacher notice")

    class Meta:
        verbose_name = u"Course"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.name

    def get_chapter_nums(self):
        #get the chapter nums
        return self.lesson_set.all().count()

    def get_learn_users(self):
        return self.usercourse_set.all()[:5]

    def get_course_lesson(self):
        #get course all chapter
        return self.lesson_set.all()

    def get_relate_courses(self):

        return self.course_org.course_set[:5]
    
    def get_course_category(self):
        #get course all category
        return self.course_category_set.all()
    def get_course_price(self):
        lessons = Lesson.objects.filter(course=self)
        total_price = 0;
        for lesson in lessons:
            total_price += int(lesson.price)
        return total_price
    def get_course_time(self):
        lessons = Lesson.objects.filter(course=self)
        class_time=None
        for lesson in lessons:
            class_from=lesson.live_class_from
            print(class_from)
#             class_time = parse_datetime(class_from)
            class_time=class_from.strftime('%b %d, %Y %H:%M %p')
#             class_time=class_from.strftime('%Y-%m-%d %H:%M:%S')
        print(class_time)
        return class_time


class Lesson(models.Model):
    course = models.ForeignKey(Course, verbose_name=u"Course")
    name = models.CharField(max_length=100, verbose_name=u"Chapter name")
    add_time = models.DateTimeField(default=datetime.now,verbose_name=u"Add time")
    price = models.CharField(max_length=12,default='0',verbose_name=u"Price")
    live_class_from = models.DateTimeField(default=datetime.now,verbose_name=u"Live Class From")
    live_class_to = models.DateTimeField(default=datetime.now,verbose_name=u"Live Class To")
    detail = UEditorField(verbose_name="Chapter Detail",width=600, height=300, imagePath="courses/ueditor/", filePath="courses/ueditor/", default="")


    class Meta:
        verbose_name = u"Chapter"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.name


    def get_lesson_video(self):
        #get chapter videos
        return self.video_set.all()


class Video(models.Model):
    lesson = models.ForeignKey(Lesson, verbose_name=u"Chapter")
    name = models.CharField(max_length=100, verbose_name=u"Video name")
    add_time = models.DateTimeField(default=datetime.now,verbose_name=u"Add time")
    url = models.CharField(max_length=200, default="", verbose_name="url")
    learn_times = models.IntegerField(default=0, verbose_name=u"Learning time(In minutes)")
    video_file= models.FileField(upload_to='org/%Y/%m', null=True, verbose_name="Video To Upload")

    class Meta:
        verbose_name = u"Course video"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.name


class CourseResource(models.Model):
    course = models.ForeignKey(Course, verbose_name=u"Course")
    name = models.CharField(max_length=100, verbose_name=u"name")
    download = models.FileField(upload_to="course/resource/%Y/%m", verbose_name=u"Resource files", max_length=100)
    add_time = models.DateTimeField(default=datetime.now,verbose_name=u"Add time")

    class Meta:
        verbose_name = u"Course resources"
        verbose_name_plural = verbose_name


class BannerCourse(Course):
    class Meta:
        verbose_name = "Banner course"
        verbose_name_plural = verbose_name
        proxy = True