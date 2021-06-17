from django.shortcuts import render
from django.http import HttpResponse
import pytz 

from django.http import FileResponse
from reportlab.pdfgen import canvas
import random
from io import BytesIO
from xhtml2pdf import pisa


tz_local = pytz.timezone('Asia/Kolkata')
import razorpay as razorpay
from django.template.loader import get_template
import app
from django.db.models import Sum,Count
razorpay_client = razorpay.Client(auth=(app.settings.razorpay_id, app.settings.razorpay_account_id))
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
import random
import string
from datetime import date
from django.contrib.auth import authenticate, login, logout 
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.models import User
from .decorators import manager_required,permission_required,profile_completion, membership_price
from django.contrib.auth.decorators import login_required
from datetime import timedelta, datetime
from django.forms import inlineformset_factory

from .filters import IngredientFilter
from django.contrib import messages
from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm, CustomUserRegister,SubscriptionForm, IngredientUpdateForm,ModifyCustomUserForm,AddIngredientForm,AddItemForm, ReviewForm,FranchiseForm,CustomEmployeeRegister,ProfileForm,MembershipPriceForm
from .models import Item, OrderLineItem, Order, Address, Payment, Coupon, Refund, UserProfile,CustomUserProfile, Subscription, Ingredient,Item_Ingredient, Review,Franchise, Membership,MembershipPrice
# stripe.api_key = settings.STRIPE_SECRET_KEY
# stripe.api_key = "ddd"


@login_required
def payment_razorpay(request):
    order = Order.objects.get(status = 'NotOrdered',user =request.user)
    subscription = None
    price = 0
    if order.subscription_set.exists():
        subscription = order.subscription_set.first()
    if subscription == None:
        price = order.get_total()
    else:
        price = subscription.total_bill
    context = {'order':order,'subscription':subscription}
    
    order_currency = 'INR'
    callback_url = 'http://'+ "127.0.0.1:8000" +"/handlerequest/"
    # callback_url = 'http://'+ str(get_current_site(request))+"/handlerequest/"
    notes = {'order-type': "basic order from the website", 'key':'value'}
    razorpay_order = razorpay_client.order.create(dict(amount=price*100, currency=order_currency, notes = notes, receipt=str(order.id), payment_capture='0'))
    order.razorpay_order_id = razorpay_order['id']
    order.save()
    return render(request,'razorpay_page.html',{'order':order, 'order_id': razorpay_order['id'], 'orderId':order.id, 'final_price':price, 'razorpay_merchant_id':app.settings.razorpay_id, 'callback_url':callback_url,'price':price})

@login_required
def payment_razorpay2(request,amt, slug):
    membership = Membership.objects.get(user = request.user)
    price = amt
    order_currency = 'INR'
    callback_url = 'http://'+ "127.0.0.1:8000" +"/handlerequest2/{}/".format(slug)
    # callback_url = 'http://'+ str(get_current_site(request))+"/handlerequest/"
    notes = {'order-type': "basic order from the website", 'key':'value'}
    razorpay_order = razorpay_client.order.create(dict(amount=price*100, currency=order_currency, notes = notes, receipt=str(membership.id), payment_capture='0'))
    membership.razorpay_order_id = razorpay_order['id']
    membership.amount = amt
    membership.save()
    return render(request,'razorpay_page.html',{'order_id': razorpay_order['id'], 'final_price':price, 'razorpay_merchant_id':app.settings.razorpay_id, 'callback_url':callback_url,'price':price})



@csrf_exempt
def handlerequest(request):
    if request.method == "POST":
        # try:
        sub = None
        subs_db = None
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id','')
        signature = request.POST.get('razorpay_signature','')
        params_dict = { 
        'razorpay_order_id': order_id, 
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature
        }
        try:

            order_db = Order.objects.get(razorpay_order_id=order_id,status = 'NotOrdered')
            if order_db.subscription_set.exists():
                print("true")
                sub = order_db.subscription_set.first()
                print("subscription located")
        except:
            return HttpResponse("505 Not Found")
        if sub:
            sub.razorpay_payment_id = payment_id 
            sub.razorpay_signature = signature
            sub.razorpay_order_id = order_id
            sub.save()
        else:
            order_db.razorpay_payment_id = payment_id
            order_db.razorpay_signature = signature
            order_db.save()
        result = razorpay_client.utility.verify_payment_signature(params_dict)
        if result==None:
            if sub:
                amount = sub.total_bill
            else:
                amount = order_db.get_total() 
            razorpay_client.payment.capture(payment_id, amount*100)
            if sub:
                sub.payment_status = True
                sub.datetime_of_payment = datetime.now()
                sub.save()
            else:
                order_db.payment_status = True
                # order_db.datetime_of_payment = datetime.datetime.now()
                order_db.datetime_of_payment =datetime.now()
                order_db.save()
                if sub:
                    subs_db = Subscription.objects.get(razorpay_order_id = order_id,payment_status = True)
                else:
                    order_db = Order.objects.get(razorpay_order_id=order_id,status = 'Ordered')
                data = {
                'order_id': order_db.id,
                'transaction_id': order_db.razorpay_payment_id,
                'user_email': order_db.user.email,
                'name': order_db.user.username,
                'order': order_db,
                'amount': order_db.get_total(),
            }
            if sub:
                subs_db = Subscription.objects.get(razorpay_order_id = order_id,payment_status = True)
                order_db = subs_db.order
                return render(request,'payment/paymentsuccess.html',{'sub':True,'id':order_db.id})
            else:
                return render(request,'payment/paymentsuccess.html',{'sub':False,'id':order_db.id})
        else:
            order_db.payment_status = False
            order_db.save()
            return render(request, 'payment/paymentfailed.html')

@csrf_exempt
def handlerequest2(request,slug):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id','')
        signature = request.POST.get('razorpay_signature','')
        params_dict = { 
        'razorpay_order_id': order_id, 
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature
        }
        try:
            membership = Membership.objects.get(razorpay_order_id=order_id)
        except:
            return HttpResponse("505 Not Found")
        membership.razorpay_payment_id = payment_id
        membership.razorpay_signature = signature
        membership.save()
        result = razorpay_client.utility.verify_payment_signature(params_dict)
        if result==None:
            amount = membership.amount 
            razorpay_client.payment.capture(payment_id, amount*100)
            membership.membership_type = slug
            a = MembershipPrice.objects.first()
            if membership.amount == a.silver_3m:
                membership.ending_date=datetime.today() + timedelta(days = 91)
            elif membership.amount == a.silver_6m:
                membership.ending_date = datetime.today() + timedelta(days = 182)
            elif membership.amount == a.gold_3m:
                membership.ending_date = datetime.today() + timedelta(days = 91)
            elif membership.amount == a.gold_6m:
                membership.ending_date = datetime.today() + timedelta(days = 182)
            elif membership.amount == a.platinum_3m:
                membership.ending_date = datetime.today() + timedelta(days = 91)
            else:
                membership.ending_date = datetime.today() + timedelta(days = 182)
            membership.save()

            return render(request,'payment/paymentsuccess2.html',{'membership':membership})
        else:
            return render(request, 'payment/paymentfailed2.html')


# use this copy if any error occurs 
# @csrf_exempt
# def handlerequest(request):
#     if request.method == "POST":
#         try:
#             payment_id = request.POST.get('razorpay_payment_id', '')
#             order_id = request.POST.get('razorpay_order_id','')
#             signature = request.POST.get('razorpay_signature','')
#             print(order_id)
#             params_dict = { 
#             'razorpay_order_id': order_id, 
#             'razorpay_payment_id': payment_id,
#             'razorpay_signature': signature
#             }
#             try:
#                 order_db = Order.objects.get(razorpay_order_id=order_id,status = 'NotOrdered')
#             except:
#                 return HttpResponse("505 Not Found")
#             order_db.razorpay_payment_id = payment_id
#             order_db.razorpay_signature = signature
#             order_db.save()
#             result = razorpay_client.utility.verify_payment_signature(params_dict)
#             if result==None:
#                 amount = order_db.get_total() #we have to pass in paisa
#                 # try:
#                 razorpay_client.payment.capture(payment_id, amount*100)
#                 order_db.payment_status = True
#                 order_db.save()
#                 print("checkpoint 4.0")
#                 template = get_template('payment/invoice.html')
#                 data = {
#                     'order_id': order_db.order_id,
#                     'transaction_id': order_db.razorpay_payment_id,
#                     'user_email': order_db.user.email,
#                     'date': str(order_db.datetime_of_payment),
#                     'name': order_db.user.name,
#                     'order': order_db,
#                     'amount': order_db.total_amount,
#                 }
#                 print("checkpoint 4.1")
#                 html  = template.render(data)
#                 # result = BytesIO()
#                 # pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)#, link_callback=fetch_resources)
#                 # pdf = result.getvalue()
#                 # filename = 'Invoice_' + data['order_id'] + '.pdf'

#                 mail_subject = 'Recent Order Details'
#                 # message = render_to_string('firstapp/payment/emailinvoice.html', {
#                 #     'user': order_db.user,
#                 #     'order': order_db
#                 # })
#                 context_dict = {
#                     'user': order_db.user,
#                     'order': order_db
#                 }
#                 template = get_template('payment/emailinvoice.html')
#                 message  = template.render(context_dict)
#                 to_email = order_db.user.email
#                 # email = EmailMessage(
#                 #     mail_subject,
#                 #     message, 
#                 #     settings.EMAIL_HOST_USER,
#                 #     [to_email]
#                 # )

#                 # for including css(only inline css works) in mail and remove autoescape off
#                 email = EmailMultiAlternatives(
#                     mail_subject,
#                     "hello",       # necessary to pass some message here
#                     settings.EMAIL_HOST_USER,
#                     [to_email]
#                 )
#                 email.attach_alternative(message, "text/html")
#                 email.attach(filename, pdf, 'application/pdf')
#                 email.send(fail_silently=False)

#                 return render(request, 'payment/paymentsuccess.html',{'id':order_db.id})
#                 # except:
#                 #     order_db.payment_status = 2
#                 #     order_db.save()
#                 #     return render(request, 'payment/paymentfailed.html')
#             else:
#                 order_db.payment_status = 2
#                 order_db.save()
#                 return render(request, 'payment/paymentfailed.html')
#         except:
#             return HttpResponse("505 not found")
@login_required
@profile_completion
def IndexPage(request):
    context = {}
    return render(request,'index.html',context)


@login_required
def ReviewView(request):
    context = {}
    return render(request,'rating_item.html',context)


@login_required
@permission_required(allowed_roles = ['Admin'])
def AdminView(request):
    shops = None
    try:
        from .models import Franchise
        shops = Franchise.objects.all()
    except:
        pass
    today = date.today()
    last_week = today - timedelta(days = 7)
    labels_today = []
    data_today = []
    orders_today = Order.objects.filter(delivery_date__gte=str(str(today))).order_by('-ordered_date').exclude(status = 'NotOrdered')
    qs_today = (orders_today.values('shop_name').annotate(total=Sum('order_bill')))
    orders_today = orders_today[0:5]

    if shops:
        for i in qs_today:
            try:
                labels_today.append(str(shops[i['shop_name']-1]))
                data_today.append(int(i['total']))
            except:
                pass
    qs_week = Order.objects.filter(delivery_date__gte=str(str(last_week))).values('shop_name').annotate(total=Sum('order_bill'))
    for i in orders_today:
        print(i.ordered_date)


    print("type of labels ",labels_today)
    print("type of data",data_today)
    mylist = list()
    most_ordered = dict()
    for i in orders_today:
        for j in i.items.all():
            try:
                most_ordered[j.item.title]
                most_ordered[j.item.title] += j.quantity
            except:
                most_ordered[j.item.title] = j.quantity
    for i in most_ordered:
        mylist.append(most_ordered[i])
    context = {'orders_today':orders_today, 'most_ordered':most_ordered,'mylist':mylist,'data_today':data_today,'labels_today':labels_today}
    print(most_ordered)
    return render(request,'admin_view.html',context)

#****************Admin View original 

# @login_required
# @permission_required(allowed_roles = ['Admin'])
# def AdminView(request):
#     today = date.today()
#     now = datetime.now()
#     print(today)
#     print(now)
#     orders_today = Order.objects.all().order_by('-ordered_date').exclude(status = 'NotOrdered')[0:5]
#        #shop info
#     #manager details
#     # link to each shops
#     mylist = list()
#     most_ordered = dict()
#     for i in orders_today:
#         for j in i.items.all():
#             try:
#                 most_ordered[j.item.title]
#                 most_ordered[j.item.title] += j.quantity
#             except:
#                 most_ordered[j.item.title] = j.quantity
#     for i in most_ordered:
#         mylist.append(most_ordered[i])
#     context = {'orders_today':orders_today, 'most_ordered':most_ordered,'mylist':mylist}
#     print(most_ordered)
#     return render(request,'admin_view.html',context)

@login_required
# @permission_required(allowed_roles = ['Admin'])
def AddFranchiseView(request):
    form = FranchiseForm()
    if request.method == 'POST' or None:
        form = FranchiseForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request,'New shop named {} successfully created'.format(form.cleaned_data.get('shop_name')))
            return redirect('/')
        else:
            messages.error(request,'Shop details is not valid')
            return redirect('/admin-view')
    else:
        form = FranchiseForm()
        context  = {'form': form}
        return render(request,'add_franchise.html',context)


def ReviewOrderView(request,id):
    order = Order.objects.get(id = id)
    items = order.items.all() #Orderline items
    reviews = list()
    form = ReviewForm()
    review_exists = False
    if order.reviewed:
        for i in range(0,len(items)):
            reviews.append(Review.objects.filter(rslug = str(request.user.username) + str(items[i].item.title) + str(order.id))[0])
    print(reviews)
    if len(reviews) > 0:
        review_exists = True
        print(len(reviews))
    if request.method == 'POST':
        if order.reviewed:
            for i in reviews:
                i.delete()
            order.reviewed=False
        response = dict(request.POST)
        for i in range(len(items)):
            Review.objects.create(user = request.user,item = items[i].item,feedback = response['feedback'][i],star_rating = int(response['rating {}'.format(i+1)][0]),rslug = str(request.user.username) + str(items[i].item.title) + str(order.id))
        messages.success(request,'Review added successfully')
        order.reviewed = True
        order.save()
        return redirect('/')
    print(review_exists)
    context = {'form':form,'items':items,'reviews':reviews,'review_exists':review_exists}
    return render(request, 'review.html',context)


@login_required
@permission_required(allowed_roles = ['Manager','StoreKeeper'])
def addIngredient(request):
    form = AddIngredientForm()
    if request.method == 'POST' or None:
        form = AddIngredientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,'You have successfully added the ingredient')
            return redirect('/storekeeper-view')
        else:
            messages.error(request,'Incorrect data provided')
    else:
        form = AddIngredientForm()
        context = {'form':form}
        return render(request,'add_ingredient.html',context)

def createItem(request):
    form1 = AddItemForm()
    OrderFormSet = inlineformset_factory(Item, Item_Ingredient, fields=('ingredient_type','quantity'), extra=10)
    # customer = Customer.objects.get(id=pk)
    formset = OrderFormSet(queryset=Order.objects.none())
    #form = OrderForm(initial={'customer':customer})
    if request.method == 'POST':
        form1 = AddItemForm(request.POST,request.FILES)
        #print('Printing POST:', request.POST)
        #form = OrderForm(request.POST)
        formset = OrderFormSet(request.POST)
        if formset.is_valid() & form1.is_valid():
            item_created = Item.objects.create(**form1.cleaned_data)

            for i in formset.cleaned_data:
                if i != {}:
                    x = Item_Ingredient.objects.create(item_type = item_created, ingredient_type = i.get('ingredient_type'), quantity = i.get('quantity'))
                    ingredient = x.ingredient_type
                    # item_created = (item_created,)
                    ingredient.used_in_item.add(item_created)
                    ingredient.save()
            return redirect('/storekeeper-view')

    context = {'form':formset,'form1':form1}
    return render(request, 'item_ingredient.html', context)


@permission_required(allowed_roles = ['Cook','Manager'])
def CookView(request):
    today = date.today()
    ingredients =  Ingredient.objects.all().order_by('inStock')[:5]
    # orders_today = Order.objects.filter(delivery_date = str(today),status = 'OrderedbutNotDelivered')
    orders_today = Order.objects.filter(status = 'OrderedButNotDelivered')
    print(orders_today)
    print(str(today))
    context = {'allorders':orders_today,'ingredients':ingredients}
    return render(request,'cook_view.html',context)



# @permission_required(allowed_roles = 'Customer')
@login_required
# Need to add a confirmation box
def skip_sub(request,id,sub_id):
    order = Order.objects.get(id = id) 
    subscription = Subscription(id = sub_id)
    last_order = subscription.subscriptions.all().order_by('-delivery_date')[0]
    order.delivery_date = last_order.delivery_date + timedelta(days=1)
    order.save()
    return redirect('/orders')

@login_required
@permission_required(allowed_roles = ['Manager','Storekeeper'])
def CookInfo(request,id):
    cook = CustomUserProfile.objects.get(id = id)
    context = {'cook':cook}
    return render(request,'cook_info.html',context)
@login_required
@permission_required(allowed_roles = ['Manager','Storekeeper'])
def AllIngredientView(request):
    all_ingredients = Ingredient.objects.all()
    myfilter = IngredientFilter(request.GET, queryset = all_ingredients)
    filtered_ingredients =myfilter.qs
    context = {'ingredients':filtered_ingredients,'myfilter':myfilter}
    return render(request,'all_ingredients.html',context)

@login_required
@permission_required(allowed_roles = ['Manager','Storekeeper'])
def ingredient_quantity_update(request,id):
    ingredient = Ingredient.objects.get(id = id)
    form = IngredientUpdateForm(instance = ingredient)
    if request.method == 'POST' or None:
        form = IngredientUpdateForm(request.POST,instance = ingredient)
        if form.is_valid():
            form.save()
            messages.success(request,'You have successfully updated the information')
            return redirect('/')
        else:
            messages.error(request,'Incorrect values provided')
    else:
        form = IngredientUpdateForm(instance=ingredient)
        context = {'form':form}
        return render(request,'update_ingredient_quantity.html',context)

@login_required
def ModifyCustomUserView(request):
    user = request.user
    current_profile = CustomUserProfile.objects.get(user = user)
    form = ModifyCustomUserForm()
    if request.method == 'POST' or None:
        form = ModifyCustomUserForm(request.POST,request.FILES,instance = current_profile)
        if form.is_valid():
            form.save()
            messages.success(request,'Your information has been updated')
            return redirect('/')
        else:
            messages.warning(request,'Incorrect information has been passed')
            return redirect('/')
    else:
        form = ModifyCustomUserForm(instance = current_profile)
        context = {'form':form}
        return render(request,'modify_user.html',context)

def dashboard(request):
    return render(request,'dashboard/dashboard.html',{})

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

@login_required
@permission_required
def manager_view(request):
    Storekeeper = CustomUserProfile.objects.filter(user_type = 'Storekeeper')
    Cooks = CustomUserProfile.objects.filter(user_type = 'Cook')
    context = {'Storekeeper': Storekeeper,'Cooks':Cooks}
    return render(request,'manager_view.html',context) 

def create_employee_form(request):
    form = CustomEmployeeRegister()
    if request.method == 'POST' or None:
        form = CustomEmployeeRegister(request.POST)
        if form.is_valid():
            form.save()
            shop_name = Franchise.objects.get(shop_name = form.cleaned_data.get('shop_name'))
            username = form.cleaned_data.get('username')
            new_user = User.objects.get(username = username)
            username_in = form.cleaned_data.get('username')
            CustomUserProfile.objects.create(user = new_user,user_type = form.cleaned_data.get('user_type'),username_in = username_in,franchise_name = shop_name)
            messages.success(request,"Account created for " + username_in)
    return render(request,'custom_employee_register.html',{'form':form})

def create_user_form(request):
    form = CustomUserRegister()
    if request.method == 'POST' or None:
        form = CustomUserRegister(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            new_user = User.objects.get(username = username)
            username_in = form.cleaned_data.get('username')
            phone_number = form.cleaned_data.get('phoneno')
            CustomUserProfile.objects.create(user = new_user,username_in = username_in,phone_number=phone_number,user_type = 'Customer')
            messages.success(request,"Account created for " + username_in)
            return redirect('/')
    return render(request,'custom_user_register.html',{'form':form})

@login_required
def complete_profile(request):
    form = ProfileForm()
    if request.method == 'POST':
        user_profile = CustomUserProfile.objects.get(user = request.user)
        form = ProfileForm(request.POST,request.FILES,instance = user_profile)
        form.save()
        a = form.cleaned_data
        try:
            Address.objects.create(user = request.user, street_address = a['house_no'],apartment_address = a['sector'], city = a['city'],zip = a['zip_code'],permanent = True,address_type = 'S',default = False)
        except:
            print("object creation failed")
        return redirect('/')
    else:
        form = ProfileForm()
        return render(request,'complete_profile.html',{'form':form})

@login_required
@permission_required(allowed_roles = ["Manager","StoreKeeper"])
def StoreKeeperView(request):
    today = date.today()
    franchise_name = request.user.customuserprofile.franchise_name
    print(franchise_name)
    ingredients =  Ingredient.objects.all().order_by('inStock')[:5]
    #orders_today = Order.objects.filter(ordered_date = str(today),shop_name = franchise_name).exclude(status = 'NotOrdered')
    orders_today = Order.objects.filter(shop_name = franchise_name).exclude(status = 'NotOrdered')
    print(orders_today)
    print(str(today))
    context = {'allorders':orders_today,'ingredients':ingredients}
    return render(request,'storekeeper_view.html',context)

def custom_login(request):
    print(str(request.user))
    if str(request.user) != 'AnonymousUser':
        redirect('/')
    print(request.method)
    if request.method == 'POST' or request.method == 'None':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request,username = username,password = password)
        if user is not None:
            login(request,user)
            return redirect('/')
        else:
            messages.info(request, 'User or Password is Incorrect')
            return render(request,'new_login.html',{})
    else:
        #return HttpResponse("Not working")
        return render(request,'account/login.html',{})


# def products(request):
#     user_membership = request.user.membership.membership_type
#     item_list = Item.objects.all() #list of objects/running on the server
#     for i in item_list:
#         if user_membership == 'None':
#             i.specialprice = -1
#             continue
#         elif user_membership == 'Silver':
#             i.specialprice = 0.9*i.guestprice

#         elif user_membership == 'Gold':
#             i.specialprice = 0.8*i.guestprice
#             # i.save()

#         elif user_membership == 'Platinum':
#             i.specialprice = 0.7*i.guestprice
#     context = {
#         'items': item_list,
#         'user_membership':user_membership
#     }
#     return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


def paymentTrue(request,id):
    order = Order.objects.get(id = id)
    order.payment_status = True
    order.save()
    return redirect('/')

# class CheckoutView(View):
#     def get(self, *args, **kwargs):
#         sub = None
#         try:
#             order = Order.objects.get(user=self.request.user, ordered=False,is_subs_order = True,status = 'NotOrdered')
#             if order.subscription_set.exists():
#                 sub = order.subscription_set.first()
#             form = CheckoutForm()
#             context = {
#                 'form': form,
#                 #'couponform': CouponForm(),
#                 'order': order,
#                 'subscription':sub,
#                 'DISPLAY_COUPON_FORM': True
#             }

#             shipping_address_qs = Address.objects.filter(
#                 user=self.request.user,
#                 address_type='S',
#                 default=True
#             )
#             if shipping_address_qs.exists():
#                 context.update(
#                     {'default_shipping_address': shipping_address_qs[0]})

#             billing_address_qs = Address.objects.filter(
#                 user=self.request.user,
#                 address_type='B',
#                 default=True
#             )
#             if billing_address_qs.exists():
#                 context.update(
#                     {'default_billing_address': billing_address_qs[0]})
#             return render(self.request, "checkout.html", context)
#         except ObjectDoesNotExist:
#             messages.info(self.request, "You do not have an active order")
#             return redirect("shop:checkout")

#     def post(self, *args, **kwargs):
#         form = CheckoutForm(self.request.POST or None)
#         try:
#             order = Order.objects.get(user=self.request.user, ordered=False,is_subs_order = True,status = 'NotOrdered')
#             if form.is_valid():
#                 use_default_shipping = form.cleaned_data.get(
#                     'use_default_shipping')
#                 if use_default_shipping:
#                     print("Using the defualt shipping address")
#                     address_qs = Address.objects.filter(
#                         user=self.request.user,
#                         address_type='S',
#                         default=True
#                     )
#                     if address_qs.exists():
#                         shipping_address = address_qs[0]
#                         order.shipping_address = shipping_address
#                         order.save()
#                     else:
#                         messages.info(
#                             self.request, "No default shipping address available")
#                         return redirect('shop:checkout')
#                 else:
#                     print("User is entering a new shipping address")
#                     shipping_address1 = form.cleaned_data.get(
#                         'shipping_address')
#                     shipping_address2 = form.cleaned_data.get(
#                         'shipping_address2')
#                     shipping_address3 = form.cleaned_data.get('shipping_address3')
#                     shipping_country = form.cleaned_data.get(
#                         'shipping_country')
#                     shipping_zip = form.cleaned_data.get('shipping_zip')

#                     if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
#                         shipping_address = Address(
#                             user=self.request.user,
#                             street_address=shipping_address1,
#                             apartment_address=shipping_address2,
#                             city = shipping_address3,
#                             country=shipping_country,
#                             zip=shipping_zip,
#                             address_type='S'
#                         )
#                         shipping_address.save()

#                         order.shipping_address = shipping_address
#                         order.save()

#                         set_default_shipping = form.cleaned_data.get(
#                             'set_default_shipping')
#                         if set_default_shipping:
#                             shipping_address.default = True
#                             shipping_address.save()

#                     else:
#                         messages.info(
#                             self.request, "Please fill in the required shipping address fields")


#                 payment_option = form.cleaned_data.get('payment_option')

#                 if payment_option == 'S':
#                     return redirect('shop:payment', payment_option='stripe')
#                 elif payment_option == 'P':
#                     return redirect('shop:payment', payment_option='paypal')
#                 else:
#                     messages.warning(
#                         self.request, "Invalid payment option selected")
#                     return redirect('shop:checkout')
#         except ObjectDoesNotExist:
#             messages.warning(self.request, "You do not have an active order")
#             return redirect("shop:order-summary")
class CheckoutView(View):
    def get(self, *args, **kwargs):
        sub = None
        try:
            order = Order.objects.get(user=self.request.user, ordered=False,is_subs_order = True,status = 'NotOrdered')
            if order.subscription_set.exists():
                sub = order.subscription_set.first()
            form = CheckoutForm()
            context = {
                'form': form,
                #'couponform': CouponForm(),
                'order': order,
                'subscription':sub,
                'DISPLAY_COUPON_FORM': True
            }
            shipping_address_permanent = Address.objects.filter(
                user=self.request.user,
                address_type = 'S',
                permanent=True)

            if shipping_address_permanent.exists():
                context.update({'shipping_address_permanent':shipping_address_permanent[0]})

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("shop:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False,is_subs_order = True,status = 'NotOrdered')
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                use_permanent_shipping = form.cleaned_data.get('use_permanent_shipping')

                if use_default_shipping or use_permanent_shipping: 
                    if use_default_shipping:
                        address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                        )
                        print("Using the default shipping address")
                    else:
                        address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        permanent=True
                        )
                        print("using the permanent address")
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        print("No default shipping address available")
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('shop:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_address3 = form.cleaned_data.get('shipping_address3')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            city = shipping_address3,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                            print("done till here")

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")
                print("done until redirect")
                return redirect('shop:payment_razorpay')
                # payment_option = form.cleaned_data.get('payment_option')

                # if payment_option == 'S':
                #     return redirect('shop:payment_razorpay')
                # elif payment_option == 'P':
                #     return redirect('shop:payment_razorpay')
                # else:
                #     messages.warning(
                #         self.request, "Invalid payment option selected")
                #     return redirect('shop:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("shop:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False,is_subs_order = True,status = 'NotOrdered')
        if order.shipping_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
                'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLIC_KEY
            }
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                # fetch the users card list
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = cards['data']
                if len(card_list) > 0:
                    # update the context with the default card
                    context.update({
                        'card': card_list[0]
                    })
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("shop:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False,is_subs_order = True)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(
                        userprofile.stripe_customer_id)
                    customer.sources.create(source=token)

                else:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                    )
                    customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total() * 100)

            try:

                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        source=token
                    )

                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("/")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "Not authenticated")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "Network error")
                return redirect("/")

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request, "Something went wrong. You were not charged. Please try again.")
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed.")
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")


# class HomeView(ListView):
#     model = Item
#     paginate_by = 10
#     template_name = "home.html"
@login_required
@profile_completion
@membership_price
def HomeView(request):
    try: 
        existing_membership = Membership.objects.get(user = request.user)
        remaining_days = existing_membership.ending_date - tz_local.localize(datetime.today())
        remaining_days = remaining_days.days
        if remaining_days < 0:
            existing_membership.membership_type = 'None'
            existing_membership.save()
    
    except:
        pass
    if str(request.user) == "AnonymousUser":
        print('anonymous')
        return redirect("/custom_login")
    user_type = request.user.customuserprofile.user_type
    if user_type == 'Manager':
        return redirect('/manager_view')
    if user_type == 'Cook':
        redirect ('/manager_view')
    # if user_type == 'Storekeeper':
    if user_type == 'StoreKeeper':
        return redirect('/storekeeper-view')
    if user_type == 'Admin':
        return redirect('/admin-view')
    user_membership = request.user.membership.membership_type
    item_list = Item.objects.all()
    for i in item_list:
        if user_membership == 'None':
            i.specialprice = i.guestprice
            continue
        elif user_membership == 'Silver':
            i.specialprice = 0.9*i.guestprice

        elif user_membership == 'Gold':
            i.specialprice = 0.8*i.guestprice
            i.save()

        elif user_membership == 'Platinum':
            i.specialprice = 0.7*i.guestprice
    context = {
        'items': item_list,
        'user_membership':user_membership
    }
    return render(request, "home.html", context)


@login_required
@profile_completion
def SubscriptionSummaryView(request):
    try:    
        existing_membership = Membership.objects.get(user = request.user)
        remaining_days = existing_membership.ending_date - tz_local.localize(datetime.today())
        remaining_days = remaining_days.days
        if remaining_days < 0:
            existing_membership.membership_type = 'None'
            existing_membership.save() 

        user_membership = request.user.membership.membership_type
        order = Order.objects.get(user=request.user,ordered=False,is_subs_order = True,status = 'NotOrdered')
        if not order.items.exists():
            messages.warning(request,"You do not have an active order")
            return redirect("/")

        #We are using the cart order to make the subscription 


        # item_list = 
        # item_lst is list of orderline items

        # item_list = order.items.all()

        # # {% for order_item in order.items.all %}
        # for i in order.items.all():
        #     print('membership is ',user_membership)
        #     if user_membership == 'None':
        #         i.item.specialprice = -1
        #         # i.save()
        #     elif user_membership == 'Silver':
        #         i.item.specialprice = 0.9*i.item.guestprice
        #         # i.save()

        #     elif user_membership == 'Gold':
        #         i.item.specialprice = 0.8*i.item.guestprice
        #         # i.save()

        #     elif user_membership == 'Platinum':
        #         i.item.specialprice = 0.7*i.item.guestprice
        #         print('triggered',i.item.specialprice)
        #         # i.save()  
        form = SubscriptionForm()
        
        subs_true = order.subs_true
        order_id = order.id
        is_subs_order = order.is_subs_order
        context = {
        # 'items': item_list,
        'user_membership':user_membership,
        'form':form,
        'object':order,
        'subs_true': subs_true,
        'order_id':order_id,
        'is_subs_order':is_subs_order}
        if request.method == 'POST' or None:
            form = SubscriptionForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
            Subscription.objects.create(user = request.user, order = order, starting_date = data['starting_date'], duration = data['duration'])

        return render(request,'subscription_summary.html',context)
    except ObjectDoesNotExist:
        messages.warning(request,"You do not have an active order")
        return redirect("/")

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
@login_required
def invoicegenerator(request,id):
    sub = None
    try:
        order_db = Order.objects.get(id=id)
        if order_db.subscription_set.exists():
            sub = order_db.subscription_set.first()
        else:
            pass
    except:
        return HttpResponse("505 Not Found")
    data = {
    'user' :order_db.user,
    'sub' : sub,
    'order_id': order_db.id,
    'transaction_id': order_db.razorpay_payment_id,
    'user_email': order_db.user.email,
    'name': order_db.user.username,
    'order': order_db,
    'items': order_db.items.all(),
    'amount': order_db.get_total(),
    }

    pdf = render_to_pdf('payment/myinvoice.html', data)
    return HttpResponse(pdf, content_type='application/pdf')

@login_required
@manager_required(allowed_roles = ['Manager'])
def manager_view(request , slug=2):
    Storekeeper = CustomUserProfile.objects.filter(user_type = 'Storekeeper')
    Cook = CustomUserProfile.objects.filter(user_type = 'Cook')
    today = date.today()

    d = timedelta(days = int(slug))
    a = today - d
    allitems = []

    pastorders=Order.objects.filter(delivery_date__gte=str(a), delivery_date__lte=str(today)).exclude(status = 'NotOrdered')
    allorders=Order.objects.filter(delivery_date__gte=str(a), delivery_date__lte=str(today)).exclude(status = 'NotOrdered')
    
    if slug == "100":
        pastorders = Order.objects.all()
        allorders = Order.objects.all()

    for d in pastorders:
        for v in d.items.all():
            allitems.append(v)
            
    items_in_decreasing_order = {}
    for singleorderlineitem in allitems:
        itemname = singleorderlineitem.item.title
        itemquantity = singleorderlineitem.quantity
        if itemname in items_in_decreasing_order:
            items_in_decreasing_order[itemname] += itemquantity
        else :
            items_in_decreasing_order[itemname] = itemquantity

    context = {'Storekeepers': Storekeeper,'Cooks':Cook , 'user' : request.user , 'items_in_decreasing_order':items_in_decreasing_order,'allorders':allorders}

    return render(request,'manager_view.html',context) 

class OrdersView(LoginRequiredMixin, View):
    # .order_set.all()
    def get(self, *args, **kwargs):
        try:
            # sub = Subscription.objects.all()
            orders = self.request.user.order_set.all().exclude(status = 'NotOrdered')
            # order = Order.objects.get(user=self.request.user, ordered=False) 
            # datetime.today().strftime('%Y-%m-%d')

            # pastorders=self.request.user.order_set.filter(delivery_date__lte='2021-03-30')
            today = date.today()

            d = timedelta(days = 2)
            a = today + d

            pastorders=self.request.user.order_set.filter(delivery_date__lt=str(today)).exclude(status = 'NotOrdered')
            futureorders=self.request.user.order_set.filter(delivery_date__gt=str(a)).exclude(status = 'NotOrdered')
            nearfutureorders=self.request.user.order_set.filter(delivery_date__gte=str(today), delivery_date__lte=str(a)).exclude(status = 'NotOrdered')
            all_subscriptions = self.request.user.subscription_set.all()
            if list(all_subscriptions) == []:
                all_subscriptions = False
            context = {
                'orders': orders,
                'nearfutureorders' : nearfutureorders,
                'futureorders' : futureorders,
                'pastorders' : pastorders,
                'subscriptions':all_subscriptions 
            }
            return render(self.request, 'allorders.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")            


# class ItemDetailView(DetailView):
#     model = Item
#     template_name = "product.html"


@login_required
@profile_completion
def MembershipView(request):
    membership = request.user.membership
    # print(membership.ending_date- datetime.datetime.now())
    # print(membership.ending_date- datetime.now())
    membership = MembershipPrice.objects.first()
    existing_membership = Membership.objects.get(user=request.user)
    remaining_days = existing_membership.ending_date - tz_local.localize(datetime.today())
    remaining_days = remaining_days.days
    if remaining_days < 0:
        existing_membership.membership_type = 'None'
        existing_membership.save()

    context = {'membership':membership,'existing_membership':existing_membership, 'remaining_days':remaining_days}
    return render(request,'membership2.html',context)

@login_required
@permission_required(allowed_roles = ['Admin'])
def MembershipPriceView(request):
    if request.method == 'POST':
        form = MembershipPriceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,'Membership Prices have been successfully defined')
            return redirect('/')
        else:
            messages.error(request,'Data incorrect')
            return redirect('/admin-view')
    else:
        form = MembershipPriceForm()
        context = {'form':form}
        return render(request,'membership_price.html',context)

@login_required
@profile_completion
def ItemDetailView(request,slug):
    user_membership = request.user.membership.membership_type
    print('slug inside the itemdetialView',slug)
    i = get_object_or_404(Item, slug=slug)
    if user_membership == 'None':
        i.specialprice = i.guestprice
    elif user_membership == 'Platinum':
        i.specialprice = i.platinumprice
    elif user_membership == 'Silver':
        i.specialprice = i.silverprice
    elif user_membership == 'Gold':
        i.specialprice = i.goldprice
    relevant_items = set()
    ingredients = i.item_ingredient_set.all()
    for k in ingredients:
        for j in k.ingredient_type.used_in_item.all():
            if user_membership == 'None':
                j.specialprice = j.guestprice
            elif user_membership == 'Platinum':
                j.specialprice = j.platinumprice
            elif user_membership == 'Silver':
                j.specialprice = j.silverprice
            elif user_membership == 'Gold':
                j.specialprice = j.goldprice
            relevant_items.add(j)
    relevant_items.remove(i)
    context = {
        'object': i,
        'user_membership':user_membership,
        'relevant_items': relevant_items
    }
    return render(request, "product.html", context)


@login_required
@profile_completion
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderLineItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False,
        ordered_copy = False
    )

    # order_item , created = OrderLineItem.objects.filter(
    #     item=item,
    #     user=request.user,
    #     ordered=False
    # )


    order_qs = Order.objects.filter(user=request.user, ordered=False,is_subs_order = True,status = 'NotOrdered')
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("shop:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("shop:order-summary")
    else:
        # ordered_date = datetime.datetime.now()
        ordered_date = datetime.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("shop:order-summary")

@login_required
@permission_required(allowed_roles = ["Manager","Storekeeper"])
def modify_order(request,id,slug):
    current_order = Order.objects.get(id = id)
    current_order.status = slug
    current_order.save()
    return redirect('shop:storekeeper-view')

@login_required
@profile_completion
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False,
        is_subs_order=True,
        status = 'NotOrdered'
    )

    if order_qs.exists() & order_qs[0].items.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderLineItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False,
                ordered_copy = False

            )[0]
            order.items.remove(order_item)
            order_item.delete()
            if order.items.exists() == False:
                return redirect("shop:order-summary")
            messages.info(request, "This item was removed from your cart.")
            return redirect("shop:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("shop:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("shop:product", slug=slug)

@login_required
@profile_completion
def add_subscription(request, slug):
    order_qs = Order.objects.get(
        id = slug
    )
    order_qs.subs_true = True
    order_qs.save()
    print(order_qs.subs_true)
    return redirect('shop:subscription-summary')
    # return HttpResponse("This is a valid page")

@login_required
@profile_completion
def remove_subscription(request, slug):
    order_qs = Order.objects.get(
        id = slug
    )
    order_qs.subs_true = False
    order_qs.save()
    print(order_qs.subs_true,"is false")
    print("Hello world")
    return redirect('shop:subscription-summary')

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False,
        is_subs_order = True,
        status = 'NotOrdered'
    )
    if order_qs.exists() & order_qs[0].items.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderLineItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False,
                ordered_copy = False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("shop:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("shop:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("shop:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("shop:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("shop:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("shop:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("shop:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("shop:request-refund")
