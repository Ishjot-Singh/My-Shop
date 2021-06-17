from django.http import HttpResponse
from django.shortcuts import redirect
from .models import CustomUserProfile,MembershipPrice
def manager_required(allowed_roles=[]):
	def decorator(view_func):
		def wrapper_func(request,*args,**kwargs):
			group = None
			if request.user.groups.exists():
				group = request.user.groups.all()[0].name	
			if group in allowed_roles:
				obj = CustomUserProfile.objects.get(username_in = request.user.username)
				approved = obj.admin_approval
				if approved == False:
					return HttpResponse('You have not been approved by the admin, please request for approval <br> <a href = "/"> Return to previous page </a>')
				else:	
					return view_func(request,*args,**kwargs)
			else:
				return HttpResponse('You are not authorized to view this page <br> <a href = "/"> Return to previous page </a>')
		return wrapper_func
	return decorator

def permission_required(allowed_roles=[]):
	def decorator(view_func):
		def wrapper_func(request,*args,**kwargs):
			group = None
			if request.user.groups.exists():
				group = request.user.groups.all()[0].name	
			if group in allowed_roles:
				approved = CustomUserProfile.objects.get(username_in = request.user.username).admin_approval
				if approved == False:
					return HttpResponse('You have not been approved by the admin, please request for approval <br> <a href = "/"> Return to previous page </a>')
				else:	
					return view_func(request,*args,**kwargs)
			else:
				return HttpResponse('You are not authorized to view this page <br> <a href = "/"> Return to previous page </a>')
		return wrapper_func
	return decorator

def profile_completion(view_func):
	def wrapper_func(request,*args,**kwargs):
		check = False
		addresses = request.user.address_set.all()
		for i in addresses:
			if i.permanent == True:
				check = True
		if check:
			return view_func(request,*args,**kwargs)
		else:
			return redirect('/complete_profile')
	return wrapper_func

def membership_price(view_func):
	def wrapper_func(request,*args,**kwargs):
		if request.user.groups.exists():
			group = request.user.groups.all()[0].name
		if group != 'Admin':
			return view_func(request,*args,**kwargs)
		else:
			try:
				price = MembershipPrice.objects.all()
				if price.exists():
					return view_func(request,*args,**kwargs)
				else:
					return redirect('/membership_price')
			except:
				return redirect('/membership_price')
	return wrapper_func

