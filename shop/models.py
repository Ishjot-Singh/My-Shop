from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db.models import Sum
from django.shortcuts import reverse
from django_countries.fields import CountryField
from django.dispatch import receiver
from copy import deepcopy
from datetime import timedelta
from datetime import datetime
from django.contrib.auth.models import Group
import re
from django.core.validators import RegexValidator


ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)

class Franchise(models.Model):
    shop_name = models.CharField(max_length = 50,default = "",null=True,blank= True)
    sectors = models.TextField(max_length = 200,default = "",null=True,blank= True)
    picture = models.ImageField(null=True,blank = True)

    def __str__(self):
        return self.shop_name


class CustomUserProfile(models.Model):
    role_types = (('Manager','Manager'),('StoreKeeper','StoreKeeper'),('Cook','Cook'),('Customer','Customer'),('Admin','Admin'))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length = 30,choices = role_types)
    username_in = models.CharField(max_length = 150,default = 'not created')
    admin_approval = models.BooleanField(default = False)
    profile_pic = models.ImageField(null=True,blank = True)
    franchise_name = models.ForeignKey(Franchise,on_delete=models.CASCADE,null=True,blank = True)
    phone_number = models.IntegerField(null = True, blank = True)
    def __str__(self):
        return self.username_in


class UserProfile(models.Model):
    user = models.OneToOneField(
    settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
class Address(models.Model):
    # The address class is used to store both shipping address and the billing address
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)

    #Reduce the length as max_length of sector should only contain 3-4 characters
    #Apartment address represents the sector 
    apartment_address_regex = RegexValidator(regex = r'\d{1,3}.?\w{0,1}$',message = "Please enter a valid sector")
    apartment_address = models.CharField(max_length=100,validators=[apartment_address_regex])
    city = models.CharField(max_length = 100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)
    permanent = models.BooleanField(default = False)
    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'Addresses'

class Item(models.Model):
    LABELS = (
        ('Best Selling Foods', 'Best Selling Foods'),
        ('Trending Food', 'Trending Food'),
        ('Spicy Foods🔥', 'Spicy Foods🔥'),
    )   
    title = models.CharField(max_length=150,unique = True)

    # category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    # label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    # slug = models.SlugField()
    # description = models.TextField()
    # image = models.ImageField()
    image=models.ImageField(upload_to='')
    # image = models.ImageField(upload_to="/")
    description = models.CharField(max_length=250,blank=True)
    # price = models.FloatField()
    # price = models.FloatField()
    # special_price = models.FloatField()

    guestprice = models.FloatField() # membership = None
    specialprice = models.FloatField(null=True,blank=True) # To be removed
    silverprice = models.FloatField(null=True,blank=True)
    goldprice = models.FloatField(null=True,blank=True)
    platinumprice = models.FloatField(null=True,blank=True)
    # pieces = 
    # instructions = models.CharField(max_length=250,default="Available")
    # image = models.ImageField(default='default.`g', upload_to='images/')
    labels = models.CharField(max_length=25, choices=LABELS, blank=True)
    # slug = models.SlugField(default="foods")
    slug = models.SlugField()
    # created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


    def get_absolute_url(self):
        return reverse("shop:product", kwargs={
        
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("shop:add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("shop:remove-from-cart", kwargs={
            'slug': self.slug
        })

    
    # def get_add_to_cart_url(self):
    #     return reverse("main:add-to-cart", kwargs={
    #         'slug': self.slug
    #     })

    def get_item_delete_url(self):
        return reverse("shop:item-delete", kwargs={
            'slug': self.slug
        })

    def get_update_item_url(self):
        return reverse("shop:item-update", kwargs={
            'slug': self.slug
        })

# Important
# a[0].ingredient_set.all()
# b[0].used_in_item.all()
# used_in_item = models.ManyToManyField(Item)
# a.ingredient_set.all()
# a = Item.objects.all()

class Ingredient(models.Model):
    title = models.CharField(max_length=150)
    description = models.CharField(max_length=250,blank=True)
    inStock = models.IntegerField()
    slug = models.SlugField()
    used_in_item = models.ManyToManyField(Item)
    low_quantity = models.IntegerField(default = 25)

    def __str__(self):
        return self.title

class Item_Ingredient(models.Model):
    item_type = models.ForeignKey(Item,on_delete=models.CASCADE)
    ingredient_type = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits = 100,decimal_places = 2)

    def __str__(self):
        return '{} - {} - {}'.format(self.item_type,self.ingredient_type,self.quantity)


# //following model seems waste
class CartItems(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    quantity = models.IntegerField(default=1)
    ordered_date = models.DateField(auto_now_add=True)
    # ordered_date = models.DateField(default=datetime.now)
    # status = models.CharField(max_length=20, choices=ORDER_STATUS, default='Active')
    # delivery_date = models.DateField(default=datetime.now)
    delivery_date = models.DateField(auto_now_add=True)


    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return self.item.title
    
    def get_remove_from_cart_url(self):
        return reverse("main:remove-from-cart", kwargs={
            'pk' : self.pk
        })

    def update_status_url(self):
        return reverse("main:update_status", kwargs={
            'pk' : self.pk
        })
    


# class Question(models.Model):
#     question_text = models.CharField(max_length=200)
#     pub_date = models.DateTimeField('date published')


# class Choice(models.Model):
#     question = models.ForeignKey(Question, on_delete=models.CASCADE)
#     choice_text = models.CharField(max_length=200)
#     votes = models.IntegerField(default=0)


class OrderLineItem(models.Model):
    # user_id = models.ForeignKey(User,on_delete=models.CASCADE, related_name="following" )

    # following_user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    # user_id = models.ForeignKey(User,on_delete=models.CASCADE, related_name="following" )
    ordered_copy = models.BooleanField(default = False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE ,null=True)
    # order = models.ForeignKey(Order,on_delete=models.CASCADE, related_name="orders" )

    ordered = models.BooleanField(default=False)
    fulfilled = models.BooleanField(default=False)
    # item = models.ForeignKey(Item, on_delete=models.CASCADE)

   
    item = models.ForeignKey(Item,on_delete=models.CASCADE, related_name="items" ,null=True)

    # order = models.ForeignKey(Order, null=False)


    # product = models.ForeignKey(Item, null=False)
    quantity = models.IntegerField(default=1)

    # def __str__(self):
    #     return "{0} {1} @ {2}".format(
    #     self.quantity, self.product.name, self.product.price)
    def ingredient_quantity(self):
        quant = self.quantity 
        item = self.item #Milkshake
        a = item.ingredient_set.all() #[Milk]
        data = Item_Ingredient.objects.all() # [Milk, Water]
        for i in data:
            for j in a:
                if i.ingredient_type.title == j.title:
                    c = Ingredient.objects.get(title=i.ingredient_type.title)
                    c.inStock = c.inStock - quant*i.quantity
                    c.save()

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.guestprice

    def get_total_discount_item_price(self):
        user_membership = self.user.membership.membership_type
        if user_membership == 'None':
            return self.quantity * self.item.guestprice
        elif user_membership == 'Silver':
            return self.quantity * self.item.silverprice
        elif user_membership == 'Gold':
            return self.quantity * self.item.goldprice
        elif user_membership == 'Platinum':
            return self.quantity * self.item.platinumprice

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    # following function will be changed
    def get_final_price(self):
        return self.get_total_discount_item_price()

class Order(models.Model):
    class Meta:
        ordering = ['delivery_date']
    ORDER_STATUS = (
        ('Ordered', 'Ordered'),
        ('OrderedbutNotDelivered', 'OrderedbutNotDelivered'),
        ('Delivered', 'Delivered'),
        ('NotOrdered', 'NotOrdered'),
    )
    Subscription_name = models.ForeignKey(
        'Subscription',
        related_name = 'subscriptions',
        on_delete=models.CASCADE,
        blank = True, null = True
    )
    order_bill = models.DecimalField(max_digits = 20, decimal_places=2,blank = True, null = True)
    #Ordered - Payment status = Ordered - payment status = COD or true
    #OrderedButNotDelivered - Accepted 
    #Delivered = True 
    #NOt Ordered - Rejected
    reviewed=models.BooleanField(default = False)
    payment_status = models.BooleanField(default = False)
    is_subs_order = models.BooleanField(default = True)
    subs_true = models.BooleanField(default = False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    shop_name = models.ForeignKey(Franchise,on_delete = models.CASCADE,null=True)
    ordered_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=50, choices=ORDER_STATUS, default='NotOrdered')
    # delivery_date = models.DateField(default=datetime.now)
    delivery_date = models.DateField(auto_now_add=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    
    items = models.ManyToManyField(OrderLineItem)
    # start_date = models.DateTimeField(auto_now_add=True)
    
    ordered = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    # billing_address = models.ForeignKey(
    #     'Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)

    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)

    razorpay_order_id = models.CharField(max_length=500, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=500, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=500, null=True, blank=True)
    datetime_of_payment = models.DateTimeField(null = True, blank = True)
    # user = models.ForeignKey(User, on_delete=models.CASCADE)  
    # ref_code = models.CharField(max_length=20, blank=True, null=True)
    # country = models.CharField(max_length=40, blank=False)
    # postcode = models.CharField(max_length=20, blank=True)
    # town_or_city = models.CharField(max_length=40, blank=False)
    # street_address1 = models.CharField(max_length=40, blank=False)
    # street_address2 = models.CharField(max_length=40, blank=False)
    # county = models.CharField(max_length=40, blank=False)
    # ordered_date = models.DateField()    

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total

    def update_quantity(self):
        item_list = self.items.all()
        for i in item_list:
            i.ingredient_quantity()
            i.fulfilled = True
            i.save()

class Subscription(models.Model):
    # Daily subscription only
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    order = models.ForeignKey(Order,on_delete = models.CASCADE)
    starting_date = models.DateTimeField(auto_now_add=True)
    # ending_date = models.DateTimeField(default=datetime.now)
    ending_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.BooleanField(default = False)
    duration = models.IntegerField(default =0)
    payment_status = models.BooleanField(default = False)
    total_bill = models.IntegerField(default = 0)
    #for subscription payments
    razorpay_order_id = models.CharField(max_length=500, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=500, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=500, null=True, blank=True)
    datetime_of_payment = models.DateTimeField(null = True, blank = True)

    def __str__(self):
        return self.user.username + " " + str(self.duration)

    def total_subscription_price(self):
        return self.order.get_total() * self.duration

#One time only, needs to be created by admin to set the prices of membership
class MembershipPrice(models.Model):
    silver_3m = models.IntegerField(default = 0)
    silver_6m = models.IntegerField(default = 0)
    gold_3m = models.IntegerField(default = 0)
    gold_6m = models.IntegerField(default = 0)
    platinum_3m = models.IntegerField(default = 0)
    platinum_6m = models.IntegerField(default = 0)


class Membership(models.Model):
    TYPES= (
        ('Silver', 'Silver'),
        ('Platinum', 'Platinum'),
        ('Gold', 'Gold'),
        ('None','None'),
    )
    ending_date = models.DateTimeField(default=datetime.now())
    # remaining_days = models.IntegerField(datetime(ending_date) - datetime(starting_date))
    membership_request = models.IntegerField(default = 0)
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    # payment_status = models.BooleanField(default = False)
    membership_type = models.CharField(max_length=50, choices=TYPES, default='None')
    amount = models.IntegerField(default = 0)
    razorpay_order_id = models.CharField(max_length=500, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=500, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return str(self.user.username) + str(self.ending_date) 
"""
class Ingredient(models.Model):
    title = models.CharField(max_length=150)
    description = models.CharField(max_length=250,blank=True)
    inStock = models.IntegerField()
    slug = models.SlugField()
    # created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.title    
"""
# //s.order_set.all()
    



    # being_delivered = models.BooleanField(default=False)
    # received = models.BooleanField(default=False)
    # refund_requested = models.BooleanField(default=False)
    # refund_granted = models.BooleanField(default=False)

    # '''
    # 1. Item added to cart
    # 2. Adding a billing address
    # (Failed checkout)
    # 3. Payment
    # (Preprocessing, processing, packaging etc.)
    # 4. Being delivered
    # 5. Received
    # 6. Refunds
    # '''





    # class Meta:
    #     verbose_name = 'Cart Item'
    #     verbose_name_plural = 'Cart Items'

    # def __str__(self):
    #     return self.item.title
    
    # def get_remove_from_cart_url(self):
    #     return reverse("main:remove-from-cart", kwargs={
    #         'pk' : self.pk
    #     })

    # def update_status_url(self):
    #     return reverse("main:update_status", kwargs={
    #         'pk' : self.pk
    #     })
    

# class Order(models.Model):
#         ORDER_STATUS = (
#         ('Active', 'Active'),
#         ('Delivered', 'Delivered')
#     )
#     client = models.ForeignKey(User, on_delete=models.CASCADE)
#     country = models.CharField(max_length=40, blank=False)
#     postcode = models.CharField(max_length=20, blank=True)
#     town_or_city = models.CharField(max_length=40, blank=False)
#     street_address1 = models.CharField(max_length=40, blank=False)
#     street_address2 = models.CharField(max_length=40, blank=False)
#     county = models.CharField(max_length=40, blank=False)
#     date = models.DateField()    
#     status = models.CharField(max_length=20, choices=ORDER_STATUS, default='Active')



class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

# class Order(models.Model):
#     full_name = models.CharField(max_length=50, blank=False)
#     phone_number = models.CharField(max_length=20, blank=False)
#     country = models.CharField(max_length=40, blank=False)
#     postcode = models.CharField(max_length=20, blank=True)
#     town_or_city = models.CharField(max_length=40, blank=False)
#     street_address1 = models.CharField(max_length=40, blank=False)
#     street_address2 = models.CharField(max_length=40, blank=False)
#     county = models.CharField(max_length=40, blank=False)
#     date = models.DateField()

#     def __str__(self):
#         return "{0}-{1}-{2}".format(self.id, self.date, self.full_name)

class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code



class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"

# class Review(models.Model):
#     user = models.ForeignKey(User, on_delete = models.CASCADE)
#     order = models.OneToOneField(Order, on_delete = models.CASCADE)
#     rslug = models.SlugField()
#     feedback = models.TextField()
#     posted_on = models.DateField(default=datimetime.now)

class Review(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    item = models.ForeignKey(Item, on_delete = models.CASCADE)
    rslug = models.SlugField(blank = True, null = True)
    feedback = models.TextField(blank = True, null = True)
    # posted_on = models.DateTimeField(default=datetime.now)
    posted_on = models.DateTimeField(auto_now_add=True)
    star_rating = models.PositiveIntegerField(default = 0)

    def __str__(self):
        return self.rslug

def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance)


post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)

@receiver(post_save, sender=Order)
def modify_quantity(sender, instance, created, **kwargs):
    if instance.status == 'Ordered':
        instance.update_quantity()



#Doesn't work properly
# @receiver(post_save,sender = User)
# def add_to_group(sender, instance, created, *args,**kwargs):
#     if created:
#         print(type(instance))
#         current_group = instance.customuserprofile.user_type
#         required_group = Group.objects.get(current_group)
#         required_group.user_set.add(instance)


@receiver(post_save,sender = CustomUserProfile)
def add_to_group(sender,instance,created,*args,**kwargs):
    if created:
        user_type = instance.user_type
        required_group,created = Group.objects.get_or_create(name = user_type)
        required_group.user_set.add(instance.user)

@receiver(post_save,sender = CustomUserProfile)
def default_membership(sender,instance,created,*args,**kwargs):
    if created:
        user = instance.user
        Membership.objects.create(user=user)

@receiver(post_save,sender = User)
def admin_customer_profile(sender,instance,created,*args,**kwags):
    if created:
        if instance.is_superuser:
            CustomUserProfile.objects.create(user = instance,user_type = 'Admin',username_in = instance.username,admin_approval=True)

@receiver(post_save,sender = Subscription)
#new subscription copy, old subscription clear, cart clear, and subscription is linked to new order.
def sub_to_order(sender,instance,created,*args,**kwargs):
    if created:
        instance.total_bill = instance.total_subscription_price()
        instance.save()
    if instance.payment_status & (instance.order.status == 'NotOrdered'):
        user = instance.user
        duration = instance.duration
        order = instance.order
        starting_date = instance.starting_date
        ordered_date = order.ordered_date
        items = order.items 
        new_sub = None
        for i in range(0,duration):
            item_list = []
            for j in items.all():
                a = OrderLineItem.objects.create(user = user,ordered_copy = True,item = j.item,quantity = j.quantity)   
                a.save()
                item_list.append(a)
            item_list = tuple(item_list)
            b = Order.objects.create(user = user,is_subs_order = False,ordered_date= ordered_date,delivery_date=starting_date + timedelta(i),status = 'Ordered',payment_status = True)
            b.items.set(item_list)
            b.datetime_of_payment = instance.datetime_of_payment
            b.shipping_address = order.shipping_address
            b.save()
            if i == 0:
                new_sub = Subscription.objects.create(user = user,order = b,starting_date = instance.starting_date,ending_date = instance.ending_date,payment_status = True, duration = instance.duration,razorpay_signature=order.razorpay_signature, razorpay_order_id=order.razorpay_order_id, razorpay_payment_id = order.razorpay_payment_id)
            new_sub.subscriptions.add(b)
            new_sub.save()
        for j in order.items.all():
            j.delete()
        sub_set = order.subscription_set.all()
        for i in sub_set:
            i.delete()
# @receiver(post_save,sender = Subscription)
# def sub_to_order(sender,instance,created,*args,**kwargs):
#     if created:
#         instance.total_bill = instance.total_subscription_price()
#         instance.save()
#     if instance.payment_status:
#         if instance.subscriptions.count() == 0:
#             user = instance.user
#             duration = instance.duration
#             order = instance.order
#             starting_date = instance.starting_date
#             ordered_date = order.ordered_date
#             items = order.items 
#             for i in range(0,duration):
#                 item_list = []
#                 for j in items.all():
#                     a = OrderLineItem.objects.create(user = user,ordered_copy = True,item = j.item,quantity = j.quantity)   
#                     a.save()
#                     j.delete()
#                     item_list.append(a)
#                 item_list = tuple(item_list)
#                 b = Order.objects.create(user = user,is_subs_order = False,ordered_date= ordered_date,delivery_date=starting_date + timedelta(i),status = 'Ordered')
#                 b.items.set(item_list)
#                 b.save()
#                 instance.subscriptions.add(b)
#                 instance.save()
#             sub_set = order.subscription_set.all()
#             for i in sub_set:
#                 i.remove()
#             # instance.order = b
#             # instance.save()


@receiver(post_save,sender = Order)
def address_associate(sender,instance,created,*args,**kwargs):
    if instance.shop_name:
        return None
    if instance.shipping_address:
        shop_sector = instance.shipping_address.apartment_address
        sector = int(re.findall('[0-9]+',shop_sector)[0]) 
        shops = Franchise.objects.all()
        for x in shops:
            i = x.sectors.split(',')
            for j in i:
                if int(j) == sector:
                    instance.shop_name = x
                    instance.save()
                    return None
# @receiver(post_save,sender = Order)
# def order_copy(sender,instance,created,*args,**kwargs):
#     # This condition ensures that only cart order is replicated, not the orders created using subscription
#     if instance.payment_status & (instance.status == 'NotOrdered'):
#         ordered_date = instance.ordered_date
#         user = instance.user
#         delivery_date = instance.delivery_date
#         items = instance.items
#         item_list = []
#         for j in items.all():
#             a = OrderLineItem.objects.create(user = user,ordered_copy = True,item = j.item,quantity = j.quantity)   
#             a.save()
#             j.delete()
#             item_list.append(a)
#         instance.payment_status = False
#         item_list = tuple(item_list)
#         b = Order.objects.create(user = user,is_subs_order = False,ordered_date= ordered_date,delivery_date=delivery_date,status = 'Ordered',payment_status = True,shop_name = instance.shop_name)
#         b.items.set(item_list)
#         sa = Address.objects.create(user = user, street_address = instance.shipping_address.street_address, apartment_address = instance.shipping_address.apartment_address,city = instance.shipping_address.city, country = instance.shipping_address.country, zip = instance.shipping_address.zip, address_type = instance.shipping_address.address_type)
#         b.shipping_address = sa
#         b.save()
#         instance.save()

@receiver(post_save,sender = Order)
def order_copy(sender,instance,created,*args,**kwargs):
    # This condition ensures that only cart order is replicated, not the orders created using subscription
    if instance.payment_status & (instance.status == 'NotOrdered'):
        ordered_date = instance.ordered_date
        user = instance.user
        delivery_date = instance.delivery_date
        items = instance.items
        item_list = []
        for j in items.all():
            a = OrderLineItem.objects.create(user = user,ordered_copy = True,item = j.item,quantity = j.quantity)   
            a.save()
            # j.delete()
            item_list.append(a)
        item_list = tuple(item_list)    
        b = Order.objects.create(user = user,is_subs_order = False,ordered_date= ordered_date,delivery_date=delivery_date,status = 'Ordered',razorpay_order_id = instance.razorpay_order_id,razorpay_payment_id=instance.razorpay_payment_id,razorpay_signature = instance.razorpay_signature,payment_status = True,datetime_of_payment = instance.datetime_of_payment)
        b.items.set(item_list)
        sa = Address.objects.create(user = user, street_address = instance.shipping_address.street_address, apartment_address = instance.shipping_address.apartment_address,city = instance.shipping_address.city, country = instance.shipping_address.country, zip = instance.shipping_address.zip, address_type = instance.shipping_address.address_type)
        b.shipping_address = sa
        b.order_bill = b.get_total()
        print("Order replication",b.order_bill)
        b.save()
        instance.payment_status = False
        for i in items.all():
            i.delete()
        sub_set = instance.subscription_set.all()
        for i in sub_set:
            i.delete()
        instance.payment_status = False
        instance.shop_name = None
        instance.razorpay_order_id = None
        instance.razorpay_signature = None
        instance.razorpay_payment_id = None
        instance.save()

# @receiver(post_save,sender = Item)
# def image_resize(sender,instance,created,*args,**kwargs):
#     if created:
#         image = instance.image
#         im = Image.open(image.path)
#         im.resize((150,150))
#         im.save(image.path)
#         instance.image.path = 
#         # im.thumbnail(200,200)
#         # im