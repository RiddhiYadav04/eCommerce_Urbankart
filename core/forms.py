from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile, Review
from django.contrib.auth.password_validation import password_validators_help_text_html
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput, 
        label="Password", 
        help_text=password_validators_help_text_html()
    )
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')

        if password != confirm:
            raise ValidationError("Passwords do not match.")
        return cleaned_data


class UserLoginForm(forms.Form):
    identifier = forms.CharField(
        label="Email or Username",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Password"
    )

    def clean(self):
        identifier = self.cleaned_data.get('identifier')
        password = self.cleaned_data.get('password')
        if not identifier or not password:
            raise ValidationError("Both fields are required.")
        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=False, label="First Name")
    last_name = forms.CharField(max_length=50, required=False, label="Last Name")
    username = forms.CharField(disabled=True, label="Username")
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'city', 'state', 'postal_code', 'profile_image']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(UserProfileForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email
            self.user_instance = user

        self.fields['first_name'].widget.attrs.update({'placeholder': 'e.g. John'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'e.g. Doe'})
        self.fields['username'].widget.attrs.update({'placeholder': 'Your username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'e.g. john@example.com'})
        self.fields['phone'].widget.attrs.update({'placeholder': 'e.g. +919876543210'})
        self.fields['address'].widget.attrs.update({'placeholder': 'e.g. 123 Street Name'})
        self.fields['city'].widget.attrs.update({'placeholder': 'e.g. Mumbai'})
        self.fields['state'].widget.attrs.update({'placeholder': 'e.g. Maharashtra'})
        self.fields['postal_code'].widget.attrs.update({'placeholder': 'e.g. 400001'})

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            user = self.user_instance
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
        return profile


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }