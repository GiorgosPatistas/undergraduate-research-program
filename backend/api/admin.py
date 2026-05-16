from django.contrib import admin
from .models import Prediction, Appointment, Article, Vote


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display  = ('user', 'prediction', 'probability', 'created_at')
    list_filter   = ('prediction',)
    search_fields = ('user__username',)
    readonly_fields = ('input_data', 'shap_values', 'created_at')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ('patient', 'doctor', 'date', 'time', 'status')
    list_filter   = ('status', 'date')
    search_fields = ('patient__username', 'doctor__username')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display  = ('title', 'author', 'created_at')
    search_fields = ('title', 'author__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'direction', 'created_at')
    list_filter  = ('direction',)
