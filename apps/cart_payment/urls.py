from django.conf.urls import url, include
from .views import cart_list, checkout, payment, response, promo_checker, test

urlpatterns = [
    # cart page
    url(r'^cart_list/$', cart_list, name="cart_list"),

# checkout page
    url(r'^checkout/$', checkout, name= 'checkout'),

    url(r'^payment/', payment, name='payment'),
    url(r'^response/', response, name='response'),
    url(r'^promo_checker/', promo_checker, name='promo_checker'),
    url(r'^test/', test, name='test')
]