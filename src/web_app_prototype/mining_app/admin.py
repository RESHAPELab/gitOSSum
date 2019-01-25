from django.contrib import admin

# Register your models here.
from .models import RestaurantLocation, MiningRequest

admin.site.register(RestaurantLocation)
admin.site.register(MiningRequest)