from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, ReviewForm
from django.contrib import messages
from core.models import Product, Category, Review
from django.db.models import Q
from django.shortcuts import get_object_or_404
from orders.models import OrderItem
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
def home(request):
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')

    products = Product.objects.all()
    categories = Category.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    return render(request, 'home.html', {
        'products': products,
        'query': query,
        'categories': categories,
        'selected_category': category_slug,
    })

# Register
def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Hash password
            user.save()
            messages.success(request, 'Account created successfully!')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


# Login
def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            password = form.cleaned_data['password']

            # Try authenticating using username first
            user = authenticate(request, username=identifier, password=password)

            # If failed, try to get user by email and authenticate with username
            if user is None:
                try:
                    from django.contrib.auth.models import User
                    user_obj = User.objects.get(email=identifier)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid username/email or password.')
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})

# Logout
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# Profile
@login_required
def user_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.userprofile, user=request.user)
    return render(request, 'profile.html', {'form': form})

# Product Details
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    images = product.images.all()
    return render(request, 'product_detail.html', {
        'product': product,
        'images': images,
    })

@login_required
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    reviews = product.reviews.all()
    user_review = product.reviews.filter(user=request.user).first()

    # This checks if the user has purchased this product
    has_delivered_order = OrderItem.objects.filter(
        product=product,
        order__user=request.user,
        order__shipping_status='Delivered' 
    ).exists()

    if request.method == 'POST' and has_delivered_order:
        form = ReviewForm(request.POST, instance=user_review or None)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            messages.success(request, "Review submitted!")
            return redirect('product_detail', slug=slug)
    else:
        form = ReviewForm(instance=user_review or None)

    return render(request, 'product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form,
        'can_review': has_delivered_order,
        'user_review': user_review,
    })

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product = review.product
    review.delete()
    messages.success(request, "Your review has been deleted.")
    return redirect('product_detail', slug=product.slug)

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product = review.product

    has_delivered_order = OrderItem.objects.filter(
        product=product,
        order__user=request.user,
        order__shipping_status='Delivered'
    ).exists()

    if not has_delivered_order:
        messages.error(request, "You can only edit reviews after delivery.")
        return redirect('product_detail', slug=product.slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated!")
            return redirect('product_detail', slug=product.slug)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'edit_review.html', {
        'form': form,
        'product': product,
    })

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        user = form.save()  # This saves the new password to the DB
        return super().form_valid(form)
    
def error_404_view(request, exception):
    return render(request, 'core/404.html', status=404)

def about_us(request):
    return render(request, 'about_us.html')

def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Optional: Send email
        send_mail(
            subject=f"Contact Form Submission from {name}",
            message=message,
            from_email=email,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
        )
        messages.success(request, "Your message has been sent successfully!")
    return render(request, 'contact_us.html')