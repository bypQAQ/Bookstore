from tokenize import Comment
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django_redis import get_redis_connection
from django_redis.serializers import json
# from pure_pagination.tests import Article

from books.models import Books
from books.enums import *
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
import logging
from utils.decorators import login_required

# Create your views here.
logger = logging.getLogger('django.request')

# @login_required
# @cache_page(60 * 15)
def index(request):
	#显示首页
	python_new = Books.objects.get_books_by_type(PYTHON, 3, sort='new')
	python_hot = Books.objects.get_books_by_type(PYTHON, 4, sort='hot')
	javascript_new = Books.objects.get_books_by_type(JAVASCRIPT, 3, sort='new')
	javascript_hot = Books.objects.get_books_by_type(JAVASCRIPT, 4, sort='hot')
	algorithms_new = Books.objects.get_books_by_type(ALGORITHMS, 3, sort='new')
	algorithms_hot = Books.objects.get_books_by_type(ALGORITHMS, 4, sort='hot')
	machinelearning_new = Books.objects.get_books_by_type(MACHINELEARNING, 3, sort='new')
	machinelearning_hot = Books.objects.get_books_by_type(MACHINELEARNING, 4, sort='hot')
	operatingsystem_new = Books.objects.get_books_by_type(OPERATINGSYSTEM, 3, sort='new')
	operatingsystem_hot = Books.objects.get_books_by_type(OPERATINGSYSTEM, 4, sort='hot')
	database_new = Books.objects.get_books_by_type(DATABASE, 3, sort='new')
	database_hot = Books.objects.get_books_by_type(DATABASE, 4, sort='hot')
	logger.info(request.body)
	#定义模板上下文
	context = {
		'python_new': python_new,
		'python_hot': python_hot,
		'javascript_new': javascript_new,
		'javascript_hot': javascript_hot,
		'algorithms_new': algorithms_new,
		'algorithms_hot': algorithms_hot,
		'machinelearning_new': machinelearning_new,
		'machinelearning_hot': machinelearning_hot,
		'operatingsystem_new': operatingsystem_new,
		'operatingsystem_hot': operatingsystem_hot,
		'database_new': database_new,
		'database_hot': database_hot,
	}
	return render(request, 'books/index.html', context)

#商品详情页面
def detail(request,books_id):
	#获取商品的详情信息
	books = Books.objects.get_books_by_id(books_id=books_id)
	#判断商品是否存在,不存在跳转到是首页
	if books is None:
		return redirect(reverse('books:index'))
	#新品
	books_li = Books.objects.get_books_by_type(type_id=books.type_id,limit=2,sort='new')
	if request.session.has_key('islogin'):
		#用户已经登录,记录浏览记录
		con = get_redis_connection('default')
		key = 'history_%d' % request.session.get('passport_id')
		#从redis列表中移除books_id
		con.lrem(key, 0, books.id)
		con.lpush(key, books.id)
		#保存用户最近浏览的5个商品
		con.ltrim(key,0,4)
	#定义上下文
	context = {'books':books,'book_li':books_li}
	#使用模板
	return render(request,'books/detail.html',context)

#商品列表页
def list(request,type_id,page):
	#获取排序方式
	sort = request.GET.get('sort','default')
	#判断type_id是否合法
	if int(type_id) not in BOOKS_TYPE.keys():
		return redirect(reverse('books:index'))
	#根据商品种类id和排序方式查询数据
	books_li = Books.objects.get_books_by_type(type_id=type_id,sort=sort)
	#分页
	paginator = Paginator(books_li,2)
	#获取分页之后总页数
	num_pages = paginator.num_pages
	#获取第page页的数据
	if page == '' or int(page) > num_pages:
		page = 1
	else:
		page = int(page)

	books_li = paginator.page(page)
	#页码控制
	#总页数<5,显示所有页码
	#当前页是前3页,显示1-5页,当前页是后3页,显示后5页,其他情况显示当前页前2页,否2页,当前页
	if num_pages < 5:
		pages = range(1,num_pages+1)
	elif page <= 3:
		pages = range(1,6)
	elif num_pages - page <= 2:
		pages = range(num_pages-4,num_pages+1)
	else:
		pages = range(page-2,page+3)

	#新品推荐
	books_new = Books.objects.get_books_by_type(type_id=type_id,limit=2,sort='new')

	#上下文
	type_title = BOOKS_TYPE[int(type_id)]
	context = {
		'books_li':books_li,
		'books_new':books_new,
		'type_id':type_id,
		'sort':sort,
		'type_title': type_title,
		'pages':pages
	}
	return render(request,'books/list.html',context)


