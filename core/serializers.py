from datetime import date
from rest_framework import serializers
from .models import Project, Task, Tag
 
 
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]
 
 
class TaskSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "project", "title", "description",
            "priority", "status", "due_date", "tags", "created_at",
        ]

    def validate_due_date(self, value):
        if value and value < date.today():
            raise serializers.ValidationError(
                "La fecha límite no puede ser en el pasado."
            )
        return value

    def validate(self, data):
        # Validación existente:
        # una tarea completada debe tener fecha límite.
        if data.get("status") == "completada" and not data.get("due_date"):
            raise serializers.ValidationError(
                "No se puede marcar una tarea como completada "
                "sin fecha límite registrada."
            )

        # Nueva validación:
        # una tarea en progreso necesita que su proyecto
        # tenga al menos una tarea completada.
        if data.get("status") == "en_progreso":
            project = data.get("project")

            # En una actualización parcial (PATCH), el proyecto
            # puede no venir en data. Usamos el proyecto existente.
            if project is None and self.instance is not None:
                project = self.instance.project

            if project is not None:
                tiene_tarea_completada = project.tasks.filter(
                    status="completada"
                ).exists()

                if not tiene_tarea_completada:
                    raise serializers.ValidationError(
                        "No se puede poner una tarea en progreso "
                        "si el proyecto no tiene ninguna tarea completada."
                    )

        return data
 
 
class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
 
    class Meta:
        model = Project
        fields = ["id", "name", "description", "tasks", "created_at"]
