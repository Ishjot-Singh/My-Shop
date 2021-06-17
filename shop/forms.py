from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout 
import datetime
from .models import Ingredient,CustomUserProfile,Item,Review,Franchise,MembershipPrice
# from .models import Subscription


# PAYMENT_CHOICES = (
#     ('S', 'Stripe'),
#     ('P', 'PayPal')
# )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = '__all__'
        exclude = ['item','user','rslug','posted_on','star_rating']

class FranchiseForm(forms.ModelForm):
    class Meta:
        model = Franchise
        fields = '__all__'

class SubscriptionForm(forms.Form):
    duration = forms.IntegerField()
    starting_date = forms.DateField(initial = datetime.date.today)

role_types = (('Manager','Manager'),('StoreKeeper','StoreKeeper'),('Cook','Cook'))
# class SubsciptionForm(forms.ModelForm):
#     class Meta:
#         model = Subsciption
#         fields = ''

class CustomEmployeeRegister(UserCreationForm):
    shop_choices = list()
    try:
        shops = Franchise.objects.all()
        for i in shops:
            shop_choices.append((i.shop_name,i.shop_name))
    except:
        pass
    shop_choices = tuple(shop_choices)
    user_type = forms.ChoiceField(
    widget=forms.RadioSelect, choices=role_types)
    shop_name = forms.ChoiceField(
        widget = forms.RadioSelect,choices=shop_choices)
    class Meta:
        model = User
        fields = ['username','email','password1','password2','user_type']

class CustomUserRegister(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email','password1','password2']


def LoginPage(request):
    if request.method == 'POST':
        request.POST.get('username')
        request.POST.get('password')
    
        user = authenticate(request,username = username,password = password)
        if user is not None:
            login(request.user)
            return redirect('home')
        else:
            messages.info(request, 'User or Password is Incorrect')
            return render(request,'login.html',context)


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_address3 = forms.CharField(required = False)
    shipping_country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }))
    shipping_zip = forms.CharField(required=False)

    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }))
    billing_zip = forms.CharField(required=False)

    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)
    use_permanent_shipping = forms.BooleanField(required = False)
    use_permanent_shipping = forms.BooleanField(required = False)

    # payment_option = forms.ChoiceField(
    #     widget=forms.RadioSelect, choices=PAYMENT_CHOICES)


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))


class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()


class PaymentForm(forms.Form):
    stripeToken = forms.CharField(required=False)
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)

class IngredientUpdateForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['title','inStock','low_quantity']

class ModifyCustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUserProfile
        fields = '__all__'
        exclude = ['user','admin_approval','username_in','user_type']

class AddIngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['title','inStock','low_quantity']

class AddItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description', 'guestprice','goldprice','silverprice','platinumprice','labels', 'slug','image']
        # Image field missing

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUserProfile
        fields = ['profile_pic']
    house_no = forms.CharField()
    sector = forms.CharField()
    city = forms.CharField()
    zip_code = forms.CharField()



class MembershipPriceForm(forms.ModelForm):
    class Meta:
        model = MembershipPrice
        fields = '__all__'
        widget ={
    'silver_3m': forms.NumberInput(attrs = {'class':'form-control','placeholder':'Price for 3 months silver membership'}),
    'silver_6m': forms.NumberInput(attrs = {'class':'form-control','placeholder':'Price for 6 months silver membership'}),
    'gold_3m': forms.NumberInput(attrs = {'class':'form-control','placeholder':'Price for 3 months gold membership'}),
    'gold_6m': forms.NumberInput(attrs = {'class':'form-control','placeholder':'Price for 6 month gold membership'}),
    'platinum_3m': forms.NumberInput(attrs = {'class':'form-control','placeholder':'Price for 3 months platinum membership'}),
    'platinum_6m': forms.NumberInput(attrs = {'class':'form-control','placeholder':'Price for 6 months platinum membership'}),
    }
