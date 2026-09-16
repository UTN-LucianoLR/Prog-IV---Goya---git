from django.urls import include, path
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"projects", views.ProjectViewSet, basename="project")
router.register(r"tasks", views.TaskViewSet, basename="task")

urlpatterns = [
    # path("projects/", views.project_list, name="project_list"),
    # path("tasks/", views.task_list, name="task_list"),
    path("", include(router.urls)),
]
