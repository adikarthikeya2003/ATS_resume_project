from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('results/<int:analysis_id>/', views.analysis_results, name='analysis_results'),
    path('update-resume/<int:analysis_id>/', views.update_resume, name='update_resume'),
    path('download/<int:analysis_id>/', views.download_resume, name='download_resume'),
    path('my-analyses/', views.user_analyses, name='user_analyses'),
    path('settings/', views.settings, name='settings'),
    path('api/analyze/', views.api_analyze, name='api_analyze'),
]