from django.urls import path
from .views import (
    PredictView,
    PredictionListView,
    AppointmentListCreateView,
    AppointmentStatusView,
    ArticleListCreateView,
    ArticleVoteView,
)

urlpatterns = [
    path('predict/',                        PredictView.as_view(),               name='predict'),
    path('predictions/',                    PredictionListView.as_view(),         name='predictions'),
    path('appointments/',                   AppointmentListCreateView.as_view(),  name='appointments'),
    path('appointments/<int:pk>/status/',   AppointmentStatusView.as_view(),      name='appointment_status'),
    path('blog/',                           ArticleListCreateView.as_view(),      name='blog'),
    path('blog/<int:pk>/vote/',             ArticleVoteView.as_view(),            name='article_vote'),
]
