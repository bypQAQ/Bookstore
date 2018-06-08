from django.conf.urls import url
from users import views

urlpatterns = [
	#注册
	url(r'^register/$',views.register,name='register'),
	url(r'^register_handle/$', views.register_handle, name='register_handle'),
	#显示登录页面
	url(r'^login/$',views.login,name='login'),
	#登录校验
	url(r'^login_check/$',views.login_check,name='login_check'),
	#退出登录
	url(r'^logout?$',views.logout,name='logout'),
	#用户中心,信息页
	url(r'^$',views.user,name='user'),
	#用户中心-地址页
	url(r'^address/$',views.address,name='address'),
	#订单页
	url(r'^order/$',views.order,name='order'),
	#验证码
	url(r'^verifycode/$', views.verifycode, name='verifycode'),
	#手机号
	url(r'^getGetPhoneCheckNum/$', views.getGetPhoneCheckNum, name='getGetPhoneCheckNum'),
	#短信验证码
	url(r'^checkCode/$', views.checkCode, name='checkCode'),
	# url(r'^back/$', views.back, name='back'),
	#激活用户
	url(r'^active/(?P<token>.*)/$',views.register_active,name='active'),



]