import json
import random
import redis
import time
import urllib
import http.client
from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
import re
from urllib import parse
from django_redis import get_redis_connection

from books.models import Books
from users.models import Passport,Address
from django.http import HttpResponse, JsonResponse
from utils.decorators import login_required
from order.models import OrderInfo,OrderGoods
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from bookstore import settings
from django.core.mail import send_mail
from users.tasks import send_active_email
import token as token
# Create your views here.

def register(request):
    #显示用户注册页面
    return render(request, 'users/register.html')

def register_handle(request):
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    phone=request.POST.get('phone')
    number=request.POST.get('number')

    if not all([username, password, email,phone,number]):
        return render(request, 'users/register.html', {'errmsg':'参数不能为空!'})

    if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'users/register.html', {'errmsg':'邮箱不合法!'})

    p = Passport.objects.check_passport(username=username)

    if p:
        return render(request, 'users/register.html', {'errmsg': '用户名已存在！'})

    passport = Passport.objects.add_one_passport(username=username, password=password, email=email)

    serializer = Serializer(settings.SECRET_KEY, 3600)
    token = serializer.dumps({'confirm':passport.id})
    token = token.decode()

    # 给用户的邮箱发激活邮件
    send_mail('当当书城用户激活', '', settings.EMAIL_FROM, [email], html_message='<a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/</a>' % token)
    print('------------++++++++++++==============')
    return redirect(reverse('user:login'))
#短信验证
def getGetPhoneCheckNum(request):
    phone=request.GET.get('phone')
    code = createPhoneCode(phone, request)
    res = sentPhoneCode(code, phone)
    if res == 'ok':
        return JsonResponse({'res': 200})


def checkCode(request):
    phone=request.GET.get('phone')
    codeNew = request.GET.get('code')
    pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    codeOld= r.get(phone)
    print(r.get(phone))
    if codeOld==codeNew:
        return JsonResponse({'res': "success"})
    else:
        return JsonResponse({'res': "error"})

#发送验证码
def sentPhoneCode(code, mobile):
    account = "C03064143"
    password = "570d1287f4916bcd617447cebd3d9053"
    host = "106.ihuyi.com"
    sms_send_url = "/webservice/sms.php?method=Submit"
    text= "您的验证码是："+code+"。请不要把验证码泄露给其他人。"
    params = urllib.parse.urlencode({'account': account, 'password':password , 'content': text, 'mobile': mobile, 'format': 'json'})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    #pthon3写法
    conn = http.client.HTTPConnection(host, port=80, timeout=30)
    #python2写法
    # conn = httplib.HTTPConnection(host, port=80, timeout=30)
    conn.request("POST", sms_send_url, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()
    return 'ok'
#生成4位随机验证码
def createPhoneCode(phone,session):
    chars=['0','1','2','3','4','5','6','7','8','9']
    x = random.choice(chars),random.choice(chars),random.choice(chars),random.choice(chars)
    verifyCode = "".join(x)
    # request.session['phone'] = {"time":int(time.time()), "code":verifyCode}
    pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    r.set(phone,verifyCode)
    print(verifyCode)
    return verifyCode

#登录页面
def login(request):
    username = ''
    checked = ''

    context = {
        'username':username,
        'checked':checked,
    }
    return render(request,'users/login.html',context)

#登录校验
def login_check(request):
    username = request.POST.get('username')
    password= request.POST.get('password')
    remember = request.POST.get('remember')
    verifycode = request.POST.get('verifycode')

    if not all([username,password,remember,verifycode]):
    #有数据为空
        # print('+++++++++++')
        return JsonResponse({'res':2})
    # print(verifycode, request.session['verifycode'])
    if verifycode.upper() != request.session['verifycode']:
        return JsonResponse({'res':3})

    passport = Passport.objects.get_one_passport(username=username,password=password)
    # print(passport)
    if passport:
    #用户名密码正确
        #获取session中的url_path
        next_url = reverse('books:index')
        jres = JsonResponse({'res': 1, 'next_url': next_url})

        # 判断是否需要记住用户名
        if remember == 'true':
        # 记住用户名
            jres.set_cookie('username', username, max_age=7*24*3600)
        else:
        # 不要记住用户名
            jres.delete_cookie('username')

        # 记住用户的登录状态
        request.session['islogin'] = True
        request.session['username'] = username
        request.session['passport_id'] = passport.id
        return jres
    else:
        return JsonResponse({'res': 0})

#退出登录
def logout(request):
    #清空session信息
    request.session.flush()
    #跳转到首页
    return redirect(reverse('books:index'))

@login_required
#用户中心
def user(request):
    '''用户中心-信息页'''
    passport_id = request.session.get('passport_id')
    # 获取用户的基本信息
    addr = Address.objects.get_default_address(passport_id=passport_id)
    # 获取用户的最近浏览信息
    con = get_redis_connection('default')
    key = 'history_%d' % passport_id
    # 取出用户最近浏览的5个商品的id
    history_li = con.lrange(key, 0, 4)
    # 查询数据库,获取用户最近浏览的商品信息
    books_li = []
    for id in history_li:
        books = Books.objects.get_books_by_id(books_id=id)
        books_li.append(books)

    return render(request, 'users/user_center_info.html', {'addr': addr,
                                                           'page': 'user',
                                                           'books_li': books_li})
@login_required
#用户中心-地址页
def address(request):
    passport_id = request.session.get('passport_id')
    if request.method == 'GET':
        addr = Address.objects.get_default_address(passport_id=passport_id)
        return render(request,'users/user_center_site.html',{'addr':addr,'page':'address'})
    else:
        #添加收货地址,接受数据
        recipient_name = request.POST.get('username')
        recipient_addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        recipient_phone = request.POST.get('phone')
        #进行校验
        if not all([recipient_name,recipient_addr,zip_code,recipient_phone]):
            return render(request,'users/user_center_site.html',{'errmsg':'参数不必为空'})
        #添加收货地址
        Address.objects.add_one_address(
            passport_id=passport_id,
            recipient_name=recipient_name,
            recipient_addr=recipient_addr,
            zip_code=zip_code,
            recipient_phone=recipient_phone
        )
        return redirect(reverse('user:address'))

# 用户中心-订单页
@login_required
def order(request):
    passport_id = request.session.get('passport_id')
    order_li = OrderInfo.objects.filter(passport_id=passport_id)

    for order in order_li:
        #根据订单id查询订单商品信息
        order_id = order.order_id
        order_books_li = OrderGoods.objects.filter(order_id=order_id)

        #计算商品的小计
        for order_books in order_books_li:
            count = order_books.count
            price = order_books.price
            amount = count * price
            #保存商品小计
            order_books.amount = amount

        #给order对象动态增加一个属性order_books_li,保存订单中商品的信息
        order.order_books_li = order_books_li

    context = {
        'order_li':order_li,
        'page':'order'
    }
    return render(request,'users/user_center_order.html',context)

#验证码
def verifycode(request):
    #引入绘图模块
    from PIL import Image,ImageDraw,ImageFont
    #引入随机函数模块
    import random
    bgcolor = (random.randrange(20, 100), random.randrange(
        20, 100), 255)
    width = 100
    height = 25
    im = Image.new('RGB',(width,height),bgcolor)
    draw = ImageDraw.Draw(im)
    for i in range(0,100):
        xy = (random.randrange(0,width),random.randrange(0,height))
        fill = (random.randrange(0,255),255,random.randrange(0,255))
        draw.point(xy,fill=fill)
    str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
    rand_str = ''
    for i in range(0,4):
        rand_str += str1[random.randrange(0,len(str1))]
    print(rand_str)
    font = ImageFont.truetype("font/consolaz.ttf", 18)

    #字体颜色
    fontcolor = (255,random.randrange(0,255),random.randrange(0,255))
    #绘制4个字
    draw.text((5, 2), rand_str[0], font=font, fill=fontcolor)
    draw.text((25, 2), rand_str[1], font=font, fill=fontcolor)
    draw.text((50, 2), rand_str[2], font=font, fill=fontcolor)
    draw.text((75, 2), rand_str[3 ], font=font, fill=fontcolor)
    #释放画笔
    del draw
    #存入session
    request.session['verifycode'] = rand_str
    # 内存文件
    import io
    buf = io.BytesIO()
    # 保存图片
    im.save(buf,'png')
    return HttpResponse(buf.getvalue(),'image/png')

#用户帐户激活
def register_active(request,token):
    serializer = Serializer(settings.SECRET_KEY,3600)
    try:
        info = serializer.load(token)
        passport_id = info['confirm']
        passport = Passport.objects.get(id=passport_id)
        passport.is_active = True
        passport.save()
        return redirect(reverse('user:login'))
    except SignatureExpired:
        return HttpResponse('激活链接已过期')
# #评论
#
# def comment(request,id):
#     if request.method == "POST":
#         form = CommentForm(request.POST)