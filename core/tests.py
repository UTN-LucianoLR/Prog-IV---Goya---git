from datetime import date, timedelta
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Project, ProjectMembership, Task


class TaskFlowClase06And07Tests(APITestCase):
    def setUp(self):
        # Creamos usuarios de prueba
        self.admin_user = User.objects.create_user(
            username="admin_user", email="admin@test.com", password="Password123!"
        )
        self.member_user = User.objects.create_user(
            username="member_user", email="member@test.com", password="Password123!"
        )
        self.outsider_user = User.objects.create_user(
            username="outsider_user", email="outsider@test.com", password="Password123!"
        )

    # ========================================================
    # TESTS CLASE 06: Autenticación, JWT, Registro
    # ========================================================

    def test_unauthenticated_requests_return_401(self):
        """Endpoints protegidos por defecto devuelven 401 si no hay credenciales."""
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_health_check_unauthenticated(self):
        """El endpoint health check responde sin necesidad de autenticación."""
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok", "service": "TaskFlow API"})

    def test_user_registration(self):
        """El registro de usuario crea un nuevo usuario y hashea la contraseña."""
        data = {
            "username": "nuevo_usuario",
            "email": "nuevo@test.com",
            "password": "PasswordValido123!",
        }
        response = self.client.post("/api/register/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("username", response.json())
        self.assertNotIn("password", response.json())

        user = User.objects.get(username="nuevo_usuario")
        self.assertTrue(user.check_password("PasswordValido123!"))

    def test_jwt_obtain_and_refresh(self):
        """Obtener token JWT con credenciales y luego renovarlo con refresh token."""
        # Login
        response = self.client.post(
            "/api/token/",
            {"username": "admin_user", "password": "Password123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens = response.json()
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

        # Refresh
        refresh_response = self.client.post(
            "/api/token/refresh/",
            {"refresh": tokens["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.json())

    # ========================================================
    # TESTS CLASE 07: Roles, Permisos RBAC y Membresías
    # ========================================================

    def test_project_creation_assigns_admin_membership(self):
        """El usuario que crea un proyecto se convierte automáticamente en admin."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/api/projects/",
            {"name": "Proyecto 1", "description": "Desc"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project_id = response.json()["id"]

        membership = ProjectMembership.objects.filter(
            project_id=project_id, user=self.admin_user
        ).first()
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, "admin")

    def test_project_visibility_by_membership(self):
        """Solo los miembros pueden ver el proyecto. Ajenos reciben 404."""
        # Admin crea el proyecto
        project = Project.objects.create(name="Proyecto Privado")
        ProjectMembership.objects.create(
            project=project, user=self.admin_user, role="admin"
        )

        # Admin puede verlo
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/projects/{project.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Outsider no es miembro -> 404
        self.client.force_authenticate(user=self.outsider_user)
        res_outsider = self.client.get(f"/api/projects/{project.id}/")
        self.assertEqual(res_outsider.status_code, status.HTTP_404_NOT_FOUND)

        # Listado de proyectos de outsider no incluye el proyecto
        list_res = self.client.get("/api/projects/")
        self.assertEqual(len(list_res.json()["results"]), 0)

    def test_add_member_action(self):
        """Un admin del proyecto puede agregar miembros con la acción add_member."""
        project = Project.objects.create(name="Proyecto Compartido")
        ProjectMembership.objects.create(
            project=project, user=self.admin_user, role="admin"
        )

        # Admin agrega a member_user como miembro
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.post(
            f"/api/projects/{project.id}/add_member/",
            {"username": "member_user", "role": "miembro"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Ahora member_user puede ver el proyecto
        self.client.force_authenticate(user=self.member_user)
        res_member = self.client.get(f"/api/projects/{project.id}/")
        self.assertEqual(res_member.status_code, status.HTTP_200_OK)

        # Agregar duplicado debe dar 400
        self.client.force_authenticate(user=self.admin_user)
        res_dup = self.client.post(
            f"/api/projects/{project.id}/add_member/",
            {"username": "member_user", "role": "miembro"},
            format="json",
        )
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_task_permissions_admin_vs_member(self):
        """
        Admin puede crear, editar y borrar tareas.
        Miembro solo puede leer (SAFE_METHODS), recibe 403 al intentar crear/editar/borrar.
        """
        project = Project.objects.create(name="Proyecto Demo")
        ProjectMembership.objects.create(
            project=project, user=self.admin_user, role="admin"
        )
        ProjectMembership.objects.create(
            project=project, user=self.member_user, role="miembro"
        )

        due = date.today() + timedelta(days=5)

        # 1. Miembro intenta crear tarea -> 403 Forbidden
        self.client.force_authenticate(user=self.member_user)
        res_member_create = self.client.post(
            "/api/tasks/",
            {"project": project.id, "title": "Tarea de Miembro", "due_date": str(due)},
            format="json",
        )
        self.assertEqual(res_member_create.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Admin crea tarea -> 201 Created
        self.client.force_authenticate(user=self.admin_user)
        res_admin_create = self.client.post(
            "/api/tasks/",
            {"project": project.id, "title": "Tarea de Admin", "due_date": str(due)},
            format="json",
        )
        self.assertEqual(res_admin_create.status_code, status.HTTP_201_CREATED)
        task_id = res_admin_create.json()["id"]

        # 3. Miembro lee la tarea -> 200 OK
        self.client.force_authenticate(user=self.member_user)
        res_member_read = self.client.get(f"/api/tasks/{task_id}/")
        self.assertEqual(res_member_read.status_code, status.HTTP_200_OK)

        # 4. Miembro intenta modificar la tarea -> 403 Forbidden
        res_member_edit = self.client.patch(
            f"/api/tasks/{task_id}/",
            {"title": "Título modificado por miembro"},
            format="json",
        )
        self.assertEqual(res_member_edit.status_code, status.HTTP_403_FORBIDDEN)

        # 5. Miembro intenta borrar la tarea -> 403 Forbidden
        res_member_delete = self.client.delete(f"/api/tasks/{task_id}/")
        self.assertEqual(res_member_delete.status_code, status.HTTP_403_FORBIDDEN)

        # 6. Admin modifica la tarea -> 200 OK
        self.client.force_authenticate(user=self.admin_user)
        res_admin_edit = self.client.patch(
            f"/api/tasks/{task_id}/",
            {"title": "Título actualizado por admin"},
            format="json",
        )
        self.assertEqual(res_admin_edit.status_code, status.HTTP_200_OK)

        # 7. Admin completa la tarea -> 200 OK
        res_complete = self.client.post(f"/api/tasks/{task_id}/complete/")
        self.assertEqual(res_complete.status_code, status.HTTP_200_OK)
        self.assertEqual(res_complete.json()["status"], "completada")

    def test_social_login_jwt_view_authenticated(self):
        """La vista /api/auth/social/jwt/ devuelve access y refresh tokens para el usuario autenticado."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/auth/social/jwt/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.json())
        self.assertIn("refresh", res.json())


class TaskFlowClase08Tests(APITestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.admin_user = User.objects.create_user(
            username="admin_user8", email="admin8@test.com", password="Password123!"
        )
        self.member_user = User.objects.create_user(
            username="member_user8", email="member8@test.com", password="Password123!"
        )

    def test_login_throttling_and_security_log(self):
        """5 intentos fallidos dan 401 y se auditan en SecurityLog; el 6to da 429 Too Many Requests."""
        from core.models import SecurityLog
        SecurityLog.objects.all().delete()

        for _ in range(5):
            res = self.client.post(
                "/api/token/",
                {"username": "admin_user8", "password": "password_incorrecta"},
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # El 6to intento debe ser frenado por el throttle (429)
        res_sixth = self.client.post(
            "/api/token/",
            {"username": "admin_user8", "password": "password_incorrecta"},
            format="json",
        )
        self.assertEqual(res_sixth.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Se deben haber registrado los 5 logins fallidos en SecurityLog
        failed_logs = SecurityLog.objects.filter(action="login_failed")
        self.assertEqual(failed_logs.count(), 5)

    def test_permission_denied_security_log(self):
        """Acciones no autorizadas registran un evento 'permission_denied' en SecurityLog."""
        from core.models import SecurityLog
        SecurityLog.objects.all().delete()

        project = Project.objects.create(name="Proyecto Seguridad")
        ProjectMembership.objects.create(project=project, user=self.admin_user, role="admin")
        ProjectMembership.objects.create(project=project, user=self.member_user, role="miembro")
        task = Task.objects.create(
            project=project,
            title="Tarea de prueba",
            due_date=date.today() + timedelta(days=2),
            owner=self.admin_user,
        )

        # El miembro intenta modificar la tarea
        self.client.force_authenticate(user=self.member_user)
        res = self.client.patch(
            f"/api/tasks/{task.id}/",
            {"title": "Intento no autorizado"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Verificamos que se creó el registro de auditoría
        denied_logs = SecurityLog.objects.filter(action="permission_denied", user=self.member_user)
        self.assertEqual(denied_logs.count(), 1)

    def test_task_description_sanitization(self):
        """La descripción se sanitiza con nh3 eliminando etiquetas HTML y scripts peligrosos."""
        project = Project.objects.create(name="Proyecto Sanitizacion")
        ProjectMembership.objects.create(project=project, user=self.admin_user, role="admin")

        self.client.force_authenticate(user=self.admin_user)
        malicious_desc = "<script>alert('xss')</script>Texto seguro <b>con formato</b>"
        res = self.client.post(
            "/api/tasks/",
            {
                "project": project.id,
                "title": "Tarea Sanitizada",
                "description": malicious_desc,
                "due_date": str(date.today() + timedelta(days=3)),
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.json()["description"], "Texto seguro con formato")

    def test_cors_headers(self):
        """Orígenes autorizados reciben el header Access-Control-Allow-Origin."""
        self.client.force_authenticate(user=self.admin_user)
        res_allowed = self.client.get("/api/projects/", HTTP_ORIGIN="http://localhost:3000")
        self.assertEqual(res_allowed.get("Access-Control-Allow-Origin"), "http://localhost:3000")

        res_disallowed = self.client.get("/api/projects/", HTTP_ORIGIN="http://sitio-malicioso.com")
        self.assertIsNone(res_disallowed.get("Access-Control-Allow-Origin"))


class TaskFlowClase09Tests(APITestCase):
    async def test_websocket_echo_and_rejection(self):
        """Verifica la conexión WebSocket con Daphne/Channels y el rechazo si el proyecto no existe."""
        from channels.testing import WebsocketCommunicator
        from channels.db import database_sync_to_async
        from config.asgi import application

        # 1. Conexión rechazada si el proyecto no existe (Tarea 5.2 de Clase 9)
        comm_reject = WebsocketCommunicator(application, "ws/projects/999999/")
        connected, _ = await comm_reject.connect()
        self.assertFalse(connected)
        await comm_reject.disconnect()

        # 2. Conexión exitosa si el proyecto existe
        project = await database_sync_to_async(Project.objects.create)(name="Proyecto Realtime")
        try:
            comm = WebsocketCommunicator(application, f"ws/projects/{project.id}/")
            connected, _ = await comm.connect()
            self.assertTrue(connected)

            # Enviar mensaje y recibir echo
            await comm.send_json_to({"mensaje": "hola desde el cliente"})
            received = await comm.receive_json_from()
            self.assertEqual(received, {"echo": {"mensaje": "hola desde el cliente"}})

            await comm.disconnect()
        finally:
            await database_sync_to_async(project.delete)()

