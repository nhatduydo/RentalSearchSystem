from django.contrib import admin
from django import forms
from accommodationSearch.models import User,Motel

class MotelForm(forms.ModelForm):
    class Meta:
        model = Motel
        fields = '__all__'

class MyMotelAdmin(admin.ModelAdmin):
    list_display = ['id', 'motel_name', 'created_date', 'address', 'active']
    form = MotelForm  

class MyAdminSite(admin.AdminSite):
    site_header = 'HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ'

admin_site = MyAdminSite(name = 'accommodationSearchApp')
admin_site.register(User)
admin_site.register(Motel, MyMotelAdmin)

