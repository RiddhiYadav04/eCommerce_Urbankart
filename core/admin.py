from django.contrib import admin
from .models import UserProfile, Category, Product, ProductImage

# Register your models here.
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_on_sale', 'discount_price']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(UserProfile)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)