from django.urls import path
from backend_app.views import TaskListCreateView, TaskUpdateDeleteView

urlpatterns = [
    path('tasks/', TaskListCreateView.as_view()),
    path('tasks/<str:pk>/', TaskUpdateDeleteView.as_view()),
]
