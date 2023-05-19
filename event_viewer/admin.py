from django.contrib import admin
from .models import EventLogReaderModel


# Register your models here.

class EventLogModel(admin.ModelAdmin):
    list_display = ('the_time', 'etv_id', 'computer_name', 'user_name', 'category', 'event_type', 'created_date')
    list_filter = ('the_time', 'etv_id', 'computer_name', 'user_name', 'category', 'event_type', 'created_date')


admin.site.register(EventLogReaderModel, EventLogModel)
