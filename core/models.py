from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User
from django.utils.text import slugify

# Create your models here.
# 1. Extend User model with profile info
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    profile_image = models.ImageField(upload_to='profile/', blank=True, null=True)

    def __str__(self):
        return self.user.username


# 2. Category model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


# 3. Product model
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_on_sale = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

        # Auto-clear discount_price if not on sale
        if not self.is_on_sale:
            self.discount_price = None

    def __str__(self):
        return self.name

    def get_display_price(self):
        return self.discount_price if self.is_on_sale and self.discount_price else self.price


# 4. Product Images
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='media/product_images/')

    def __str__(self):
        return f"Image for {self.product.name} Image"

# 5. Review   
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # One review per user per product

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating})"
    
    def average_rating(self):
        return self.reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    Product.average_rating = average_rating