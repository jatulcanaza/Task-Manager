# 📌 Sistema de Gestión de Tareas Distribuido
**Arquitectura de Software – Proyecto Académico Completo**

---

## 📖 Descripción General

Sistema empresarial de **gestión de tareas** basado en una **arquitectura de microservicios distribuida**, desplegado completamente con **contenedores Docker**. Implementa múltiples orígenes de datos (PostgreSQL y MongoDB), mensajería asíncrona (RabbitMQ), comunicación en tiempo real (MQTT y WebSockets) y patrones de diseño avanzados.

El sistema permite:
- **Autenticación segura** con JWT y validación de correos institucionales (@uce.edu.ec)
- **CRUD completo de tareas** con auditoría en MongoDB
- **Comunicación en tiempo real** mediante WebSockets y MQTT
- **Reportes combinados** integrando múltiples bases de datos
- **Integración SSO** con proveedores externos

---

## 🎯 Objetivos del Proyecto

✅ Arquitectura basada en contenedores con Docker Compose  
✅ **Dos orígenes de datos distintos** (PostgreSQL + MongoDB)  
✅ **Patrones de diseño** (Abstract Factory, DAO, DTO, Service Layer)  
✅ **API REST profesional** con FastAPI y validación automática  
✅ **Mensajería asíncrona** con RabbitMQ (eventos distribuidos)  
✅ **Comunicación en tiempo real** con MQTT y WebSockets  
✅ **Interfaz web responsiva** (Frontend + Frontend B para SSO)  
✅ **Portabilidad completa** a cualquier entorno

---

## 🏗️ Arquitectura del Sistema

### Topología de Contenedores

```
┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │  Frontend B     │
│  (Nginx:8080)   │     │  (Nginx:8081)   │
│  Main App       │     │  SSO Dashboard  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼──────────┐
         │   Backend API        │
         │  FastAPI (8000)      │
         │  - Task Manager A    │
         │  - Auth Manager      │
         │  - Report Service    │
         └───────────┬──────────┘
             ┌───────┼───────┬────────┐
             │       │       │        │
    ┌────────▼──┐ ┌──▼──┐ ┌─▼───┐ ┌──▼─────┐
    │PostgreSQL │ │Mongo│ │Rabbit│ │Mosquitto│
    │  (5433)   │ │A B  │ │ MQ   │ │  MQTT   │
    │ Tasks +   │ │ Logs│ │Events│ │ Realtime│
    │ Users     │ │Auth │ │      │ │         │
    └───────────┘ └─────┘ └──────┘ └─────────┘
```

### Descripción de Servicios

| Servicio | Tecnología | Puerto | Función |
|----------|-----------|--------|---------|
| **Frontend** | Nginx + HTML/CSS/JS | 8080 | UI Principal - Gestión de Tareas |
| **Frontend B** | Nginx + HTML/CSS/JS | 8081 | Dashboard SSO - Autenticación |
| **Backend (A)** | FastAPI (Python) | 8000 | API REST - Orquestación Central |
| **PostgreSQL** | PostgreSQL 16 | 5433 | BD Relacional - Usuarios, Tareas |
| **MongoDB A** | MongoDB 7 | 27017 | Logs de Tareas - Auditoría Funcional |
| **MongoDB B** | MongoDB 7 | 27018 | Logs de Acceso - Auditoría Seguridad |
| **RabbitMQ** | RabbitMQ 3 | 5672 | Bus de Eventos - Comunicación Async |
| **Mosquitto** | MQTT Broker | 1883 | Pub/Sub Tiempo Real - WebSockets |

---

## 🗄️ Modelo de Datos

### PostgreSQL - Datos Transaccionales
Almacena entidades de negocio con integridad referencial:

```
┌──────────────┐              ┌──────────────┐
│    USERS     │──────────────│    TASKS     │
├──────────────┤   1:N        ├──────────────┤
│ id (PK)      │              │ id (PK)      │
│ email        │              │ user_id (FK) │
│ password     │              │ title        │
│ name         │              │ description  │
│ created_at   │              │ status       │
│              │              │ created_at   │
│              │              │ updated_at   │
└──────────────┘              └──────────────┘

Justificación:
✓ Relaciones N:1 requieren integridad referencial
✓ Transacciones ACID para consistencia
✓ Consultas complejas con JOINs
✓ Ideal para datos estructurados
```

### MongoDB A - Logs de Tareas
Auditoría flexible de eventos de negocio:

```json
{
  "_id": ObjectId,
  "task_id": UUID,
  "event_type": "created|updated|deleted",
  "old_values": { ... },
  "new_values": { ... },
  "timestamp": ISODate,
  "user_id": UUID
}
```

### MongoDB B - Logs de Acceso
Auditoría de seguridad y autenticación:

```json
{
  "_id": ObjectId,
  "user_id": UUID,
  "action": "login|logout|token_issued",
  "ip_address": "xxx.xxx.xxx.xxx",
  "timestamp": ISODate,
  "sso_provider": "google|okta|...",
  "token_hash": "..."
}
```

**Justificación de dos MongoDB:**
- Separación de concernencias (funcional vs. seguridad)
- Escalado independiente de logs
- Políticas de retención diferentes
- Acceso diferenciado (seguridad vs. operaciones)

---

## 🧩 Patrones de Diseño Implementados

### 1️⃣ Abstract Factory
Abstraer la creación de familias de DAOs según la BD:

```python
# Uso en rutas
postgres_factory = PostgresFactory(db_session)  
mongo_factory = MongoFactory(mongo_db)

# Se crean diferentes DAOs sin acoplamiento
user_dao = postgres_factory.create_user_dao()      # UserDAO PostgreSQL
task_dao = postgres_factory.create_task_dao()      # TaskDAO PostgreSQL
log_dao = mongo_factory.create_log_dao()           # LogDAO MongoDB
```

### 2️⃣ DAO (Data Access Object)
Encapsular acceso a datos de forma agnóstica:

```python
class UserDAO:
    def get_by_email(self, email: str) → User | None
    def create(self, user_data: dict) → User
    def update(self, user_id: UUID, data: dict) → User
    def delete(self, user_id: UUID) → bool

class TaskDAO:
    def get_user_tasks(self, user_id: UUID) → List[Task]
    def create_task(self, data: dict) → Task
    def update_status(self, task_id: UUID, status: str) → Task
```

### 3️⃣ DTO (Data Transfer Object)
Validación automática de entrada/salida con Pydantic:

```python
class TaskCreateDTO(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., max_length=1000)
    priority: TaskPriority = TaskPriority.MEDIUM

class TaskOutDTO(BaseModel):
    id: UUID
    title: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime | None
```

### 4️⃣ Service Layer
Orquestación de lógica de negocio:

```python
class TaskService:
    def __init__(self, pg_factory: PostgresFactory, 
                 mongo_factory: MongoFactory):
        self.pg_factory = pg_factory
        self.mongo_factory = mongo_factory
    
    async def create_task(self, user_id: UUID, 
                         dto: TaskCreateDTO) → TaskOutDTO:
        # Lógica de validación
        # Persistencia en PostgreSQL
        # Auditoría en MongoDB
        # Publicación de evento
```

### 5️⃣ Publisher-Subscriber
Bus de eventos asíncrono con RabbitMQ:

```
Eventos publicados:
├── task.created    → puente → MQTT → WebSocket → Dashboard
├── task.updated    → análisis → reportes
├── task.deleted    → auditoría → logs
└── user.logged_in  → seguridad → Mongo B
```

---

## 📂 Estructura del Proyecto

```
task-manager-arch/
│
├── docker-compose.yml          # Orquestación de contenedores
├── mosquitto/
│   └── mosquitto.conf          # Configuración MQTT broker
│
├── backend/
│   ├── Dockerfile              # Imagen FastAPI
│   ├── requirements.txt         # Dependencias Python
│   │
│   └── app/
│       ├── main_a.py           # ✨ APP PRINCIPAL (Tasks)
│       ├── main_auth.py        # ✨ APP Gestión de Autenticación
│       ├── main_b.py           # ✨ APP B (Potencial - SSO)
│       │
│       ├── core/               # Configuración central
│       │   ├── config.py       # Settings desde variables de entorno
│       │   ├── dependencies.py # Inyección de dependencias FastAPI
│       │   ├── security.py     # JWT, validación, hashing
│       │   ├── errors.py       # Excepciones personalizadas
│       │   ├── event_publisher.py    # Publicador RabbitMQ
│       │   ├── bridge_consumer.py    # Consumer: RabbitMQ → MQTT
│       │   ├── mqtt_listener.py      # Listener MQTT adicional
│       │   └── ws_manager.py         # Gestor de WebSockets
│       │
│       ├── db/                 # Conexiones a bases de datos
│       │   ├── postgres.py     # Engine y sesiones SQLAlchemy
│       │   └── mongo.py        # Clientes MongoDB (A y B)
│       │
│       ├── models/             # Modelos ORM SQLAlchemy
│       │   └── postgres_models.py
│       │       ├── User
│       │       └── Task
│       │
│       ├── daos/               # Data Access Objects
│       │   ├── interfaces/
│       │   │   ├── user_dao.py         # Interfaz abstracta
│       │   │   ├── task_dao.py         # Interfaz abstracta
│       │   │   └── log_dao.py          # Interfaz abstracta
│       │   ├── postgres/
│       │   │   ├── user_dao_pg.py      # Implementación PG
│       │   │   └── task_dao_pg.py      # Implementación PG
│       │   └── mongo/
│       │       ├── log_dao_mongo.py    # Implementación Mongo
│       │       └── access_log_dao.py   # Logs de acceso
│       │
│       ├── factories/          # Abstract Factory Pattern
│       │   ├── abstract_factory.py     # Interfaz base
│       │   ├── postgres_factory.py     # Crea DAOs PostgreSQL
│       │   └── mongo_factory.py        # Crea DAOs MongoDB
│       │
│       ├── dtos/               # Data Transfer Objects (Validación)
│       │   ├── auth_dto.py     # Login, Register
│       │   ├── task_dto.py     # TaskCreate, TaskUpdate, TaskOut
│       │   └── report_dto.py   # Datos para reportes combinados
│       │
│       ├── services/           # Capa de Lógica de Negocio
│       │   ├── auth_service.py        # Registro, login, JWT
│       │   ├── task_service.py        # CRUD + eventos
│       │   └── report_service.py      # Reportes multi-BD
│       │
│       └── routes/             # Endpoints API (Controllers)
│           ├── auth_routes.py         # /auth/*
│           ├── task_routes.py         # /tasks/*
│           ├── report_routes.py       # /reports/*
│           ├── sso_routes.py          # /sso/*
│           └── ws_routes.py           # WebSocket /ws
│
├── frontend/                   # ✨ APP PRINCIPAL
│   ├── Dockerfile
│   ├── nginx.conf
│   └── public/
│       ├── index.html          # HTML principal
│       ├── app.js              # JS - Lógica de tareas
│       └── styles.css          # Estilos
│
├── frontend_b/                 # ✨ DASHBOARD SSO
│   ├── Dockerfile
│   ├── nginx.conf
│   └── public/
│       ├── login.html          # Página de login
│       ├── sso.html            # Integración SSO
│       ├── dashboard.html      # Dashboard con WebSocket
│       ├── b.js                # JS tiempo real
│       └── styles.css          # Estilos
│
├── backups/                    # Respaldos de datos
│   ├── mongo_dump.archive      # Dump MongoDB
│   ├── postgres_dump.sql       # Dump PostgreSQL
│   ├── restore_mongo.sh        # Script restauración Mongo
│   └── restore_postgres.sh     # Script restauración PG
│
└── diagrams/                   # Diagramas de arquitectura

```

---

## 🚀 Funcionalidades Principales

### Autenticación y Usuarios
- ✅ **Registro** con validación de formato de email
- ✅ **Login** con generación de JWT (expira en 60 min)
- ✅ **Validación de credenciales** con bcrypt
- ✅ **Refresh tokens** para mantener sesiones
- ✅ **SSO** (integración con proveedores externos)
- ✅ **Auditoría de acceso** en MongoDB B

### Gestión de Tareas
- ✅ **CRUD completo** (Create, Read, Update, Delete)
- ✅ **Asignación a usuarios** (relación 1:N)
- ✅ **Estados** (pendiente, en progreso, completada)
- ✅ **Prioridades** (baja, media, alta)
- ✅ **Fechas** (creación, último cambio)
- ✅ **Filtros avanzados** (por estado, usuario, fecha)

### Reportes
- ✅ **Reporte combinado** (Postgres + MongoDB A)
- ✅ **Últimas acciones** (desde logs en Mongo)
- ✅ **Resumen por usuario** (tareas + actividad)
- ✅ **Exportación de datos** (JSON, CSV - potencial)

### Tiempo Real
- ✅ **WebSockets** para actualizaciones en vivo
- ✅ **MQTT pub/sub** para comunicación descentralizada
- ✅ **Bridge RabbitMQ → MQTT** (desacoplamiento)
- ✅ **Dashboard dinámico** (Frontend B)

### Integración de Servicios
- ✅ **RabbitMQ** para eventos asíncronos distribuidos
- ✅ **MQTT** para IoT/tiempo real
- ✅ **Publicación de eventos** (task.created, task.updated, task.deleted)
- ✅ **Consumidor puente** (Consumer → Publisher MQTT)
- ✅ **Email** (potencial - aiosmtplib ya en requirements)

---

## 📊 Tecnologías y Dependencias

### Backend (Python FastAPI)
```
fastapi==0.115.6              → Framework web asíncrono
uvicorn[standard]==0.34.0     → Servidor ASGI de alto rendimiento
pydantic==2.10.4              → Validación de datos automática
pydantic-settings==2.7.1      → Configuración desde variables de entorno
SQLAlchemy==2.0.36            → ORM para PostgreSQL
psycopg2-binary==2.9.10       → Driver de PostgreSQL
pymongo==4.10.1               → Cliente oficial de MongoDB
python-jose==3.3.0            → Manejo de JWT (autenticación)
bcrypt==4.1.3                 → Hashing seguro de contraseñas
aio-pika==9.4.3               → Cliente AMQP asíncrono (RabbitMQ)
paho-mqtt==2.1.0              → Cliente MQTT
aiosmtplib==3.0.2             → Envío de emails asíncrono
```

### Frontend
- **Nginx** - Servidor web estático
- **HTML5** - Estructura
- **CSS3** - Estilos responsivos
- **JavaScript vanilla** - Lógica (sin frameworks)
- **WebSocket API** - Comunicación en tiempo real
- **MQTT.js** - Cliente JavaScript para MQTT

### Infraestructura
- **Docker** - Containerización
- **Docker Compose** - Orquestación
- **PostgreSQL 16** - BD relacional
- **MongoDB 7** - BD NoSQL (x2)
- **RabbitMQ 3** - Broker de mensajes
- **Mosquitto 2** - Broker MQTT

---

## 🛠️ Cómo Ejecutar el Proyecto

### Prerequisitos
```bash
git clone <repositorio>
cd task-manager-arch

# Asegurar Docker y Docker Compose instalados
docker --version
docker-compose --version
```

### Variables de Entorno
Crear archivo `.env` en la raíz:
```env
# PostgreSQL
POSTGRES_USER=taskmanager
POSTGRES_PASSWORD=SecurePass123
POSTGRES_DB=task_manager
POSTGRES_HOST=postgres_a
POSTGRES_PORT=5432

# MongoDB A (task_logs)
MONGO_A_INITDB_ROOT_USERNAME=root
MONGO_A_INITDB_ROOT_PASSWORD=example
MONGO_A_HOST=mongo_a
MONGO_A_PORT=27017
MONGO_A_DB=task_logs

# MongoDB B (access_logs)
MONGO_B_INITDB_ROOT_USERNAME=root
MONGO_B_INITDB_ROOT_PASSWORD=example
MONGO_B_HOST=mongo_b
MONGO_B_PORT=27017
MONGO_B_DB=access_logs

# JWT
JWT_SECRET=tu_clave_super_secreta_aqui_minimo_32_caracteres
JWT_EXPIRES_MIN=60

# RabbitMQ
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# CORS
CORS_ORIGINS=http://localhost:8080,http://localhost:8081,http://127.0.0.1:8080
```

### Iniciar los Servicios
```bash
# Construir y arrancar todos los contenedores
docker-compose up -d

# Verificar estado
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f backend
docker-compose logs -f mongo_a
docker-compose logs -f postgres_a
```

### Acceso a Interfaces

| Interfaz | URL | Descripción |
|----------|-----|-------------|
| **Frontend A** | http://localhost:8080 | App principal - Gestión de tareas |
| **Frontend B** | http://localhost:8081 | Dashboard SSO |
| **API Docs** | http://localhost:8000/docs | Swagger interactivo |
| **API ReDoc** | http://localhost:8000/redoc | ReDoc alternativo |
| **RabbitMQ** | http://localhost:15672 | Management (guest/guest) |
| **MongoDB A** | mongodb://root:example@localhost:27017/task_logs | Logs de tareas |
| **MongoDB B** | mongodb://root:example@localhost:27018/access_logs | Logs de acceso |
| **PostgreSQL** | postgresql://taskmanager:SecurePass123@localhost:5433/task_manager | BD relacional |

### Detener Servicios
```bash
docker-compose down          # Detiene sin eliminar volúmenes
docker-compose down -v       # Detiene y elimina volúmenes
```

---

## 📡 Endpoints API

### Autenticación
```
POST   /auth/register      → Registro de usuario
POST   /auth/login         → Iniciar sesión (retorna JWT)
POST   /auth/logout        → Cerrar sesión (auditoría)
POST   /auth/refresh       → Renovar token JWT
GET    /auth/me            → Datos del usuario autenticado
```

### Tareas
```
GET    /tasks              → Listar tareas del usuario (con filtros)
GET    /tasks/{task_id}    → Obtener detalle de tarea
POST   /tasks              → Crear nueva tarea
PUT    /tasks/{task_id}    → Actualizar tarea
DELETE /tasks/{task_id}    → Eliminar tarea
POST   /tasks/{task_id}/status → Cambiar estado
```

### Reportes
```
GET    /reports/summary    → Resumen de tareas + últimas acciones
GET    /reports/user/{user_id} → Reporte por usuario
GET    /reports/combined   → Datos combinados Postgres + Mongo
```

### SSO
```
GET    /sso/providers      → Listar proveedores disponibles
POST   /sso/authorize      → Iniciar flujo OAuth
GET    /sso/callback       → Callback del proveedor
```

### WebSocket
```
WS     /ws                 → Conexión WebSocket para tiempo real
```

---

## 🔄 Flujo de Comunicación

### Crear una Tarea (Arquitectura Completa)

```
1. Cliente (Frontend)
   └─> POST /tasks { title, description }
       ↓
2. Backend - route/task_routes.py
   └─> Validación DTO
       ↓
3. Service Layer - services/task_service.py
   ├─> PostgreSQL Factory → TaskDAO.create()
   │   └─> Persiste en USERS.TASKS
   │
   ├─> MongoDB Factory → LogDAO.create_log()
   │   └─> Auditoría en MongoDB A
   │
   └─> Event Publisher.publish("task.created")
       ↓
4. RabbitMQ (Exchange: events, Type: TOPIC)
   └─> Patrón: "task.*"
       ↓
5. Bridge Consumer (core/bridge_consumer.py)
   ├─> Consume el evento
   └─> Publisher → MQTT (topic: tasks/created)
       ↓
6. Mosquitto MQTT Broker
   └─> Distribuye a suscriptores
       ↓
7. Frontend B (WebSocket)
   └─> Recibe actualización en tiempo real
       └─> Dashboard se actualiza automáticamente
```

### Flujo de Autenticación

```
1. Usuario ingresa credenciales (Frontend A, login.html)
   └─> POST /auth/login { email, password }
       ↓
2. Backend - routes/auth_routes.py
   └─> Service Layer: auth_service.py
       ├─> UserDAO.get_by_email() → PostgreSQL
       ├─> bcrypt.verify(password, hash)
       ├─> Log en MongoDB B (access_logs)
       └─> JWT.create(user_id, exp=60min)
           ↓
3. Backend retorna { access_token, token_type }
   └─> Frontend almacena en localStorage
       ├─> Envía header: "Authorization: Bearer <token>"
       └─> Acceso a /tasks, /reports, etc.
```

---

## 🔐 Seguridad

### Implementado
- ✅ **JWT con expiración** (60 minutos configurables)
- ✅ **Validación de CORS** (orígenes permitidos)
- ✅ **Hashing de contraseñas** (bcrypt)
- ✅ **Inyección de dependencias** (validación en cada request)
- ✅ **Auditoría de acceso** (MongoDB B)
- ✅ **Validación de DTOs** (Pydantic con tipos fuertes)

### Recomendaciones para Producción
- 🔒 Usar HTTPS/TLS
- 🔒 Implementar rate limiting
- 🔒 Refresh tokens en base de datos
- 🔒 Logs de seguridad cifrados
- 🔒 Variables de entorno en secretos (Kubernetes, AWS)
- 🔒 Validación de email confirmado

---

## 📊 Volúmenes Docker (Persistencia)

```
pgdata_a        → Datos PostgreSQL
mongodata_a     → Datos MongoDB A (task_logs)
mongodata_b     → Datos MongoDB B (access_logs)
mosquitto_data  → Configuración MQTT
mosquitto_log   → Logs MQTT
```

Datos persistentes se guardan automáticamente en disco del sistema.

---

## 🐛 Troubleshooting

### Puerto ya en uso
```bash
# Cambiar puerto en docker-compose.yml
# Buscar el puerto usado
netstat -ano | findstr :8000

# Detener contenedor anterior
docker stop <container_id>
docker rm <container_id>
```

### MongoDB no conecta
```bash
# Verificar credenciales
docker exec taskmanager-mongo-a mongosh -u root -p example --authenticationDatabase admin

# Limpiar volumen
docker volume rm taskmanager_mongodata_a
docker-compose up -d mongo_a
```

### Backend no arranca
```bash
# Ver logs detallados
docker-compose logs backend

# Reconstruir imagen
docker-compose build --no-cache backend
docker-compose up -d backend
```

### WebSocket no conecta
```bash
# Verificar WebSocket está habilitado en FastAPI
# GET /docs → /ws debe aparecer como endpoint

# Verificar CORS en config
# Comprobar que Frontend está en CORS_ORIGINS
```

---

## 📝 Convenciones y Estándares

### Nombres de Variables
```python
# DAO: Singular, interfaz clara
user_dao: UserDAO              ✅
task_dao: TaskDAO              ✅

# DTO: Sufijo DTO, clara intención
TaskCreateDTO                  ✅
TaskOutDTO                     ✅

# Services: Sufijo Service
TaskService                    ✅
AuthService                    ✅

# Routers: Router con prefijo
router = APIRouter(prefix="/tasks")
```

### Estructura de Respuesta API
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2024-02-08T10:30:00Z"
}
```

### Eventos RabbitMQ
- `task.created`
- `task.updated`
- `task.deleted`
- `user.logged_in`
- `user.logged_out`

---

## 👨‍💼 Autores y Contribuidores

Proyecto académico de **Arquitectura de Software**
Autores: [Tus nombres aquí]

---

## 📄 Licencia

[Especificar licencia si aplica]

---

## 📚 Referencias y Documentación

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [MongoDB Docs](https://docs.mongodb.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/tutorials)
- [MQTT Specification](https://mqtt.org/)
- [JWT.io](https://jwt.io/)

---

**Última actualización:** 8 de febrero de 2026
│     ├─ index.html
│     ├─ styles.css
│     └─ app.js
|     
├─ backend/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ app/
│     ├─ main.py
│     ├─ factories/
│     ├─ daos/
│     ├─ dtos/
│     ├─ services/
│     ├─ routes/
│     └─ models/
│     └─ core/
│     └─ db/
│     └─ utils/
├─ backups/
│  ├─ postgres_dump.sql
│  └─ mongo_dump.archive
│  └─ restore_mongo.ssh
│  └─ restore_postgres.sh
└─ diagrams/
├─ Diagrams - ArquitecturaCapas.png
└─ Diagrams - Docker-Based-Deployment.png
└─ Diagrams - Login-Process-Flow.png
└─ Diagrams - Task-Management-Process-Flow.png
└─ Diagrams -Components.png


````

---

## ⚙️ Requisitos del sistema

- Docker
- Docker Compose
- Navegador web moderno

---

## 🔐 Variables de entorno

Crear un archivo `.env` a partir de `.env.example`:

```env
POSTGRES_USER=appuser
POSTGRES_PASSWORD=apppass
POSTGRES_DB=taskdb
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

MONGO_INITDB_ROOT_USERNAME=root
MONGO_INITDB_ROOT_PASSWORD=example
MONGO_HOST=mongo
MONGO_PORT=27017
MONGO_DB=tasklogs

JWT_SECRET=super_secret_key
JWT_EXPIRES_MIN=60
CORS_ORIGINS=http://localhost:8080
````

---

## ▶️ Ejecución del proyecto (Portabilidad con Docker Hub)

Para garantizar portabilidad, las imágenes del sistema fueron publicadas en **Docker Hub**:

* `juantulcanaza/taskmanager-backend:latest`
* `juantulcanaza/taskmanager-frontend:latest`

### 1) Crear el archivo `.env`

Desde la raíz del proyecto:

**Windows (PowerShell):**

```powershell
copy .env.example .env
```

**Linux/Mac:**

```bash
cp .env.example .env
```

### 2) Descargar imágenes desde Docker Hub

```bash
docker compose pull
```

### 3) Levantar el sistema

```bash
docker compose up -d
```

### 4) Verificar contenedores activos

```bash
docker compose ps
```

Servicios disponibles:

* Frontend: [http://localhost:8080](http://localhost:8080)
* Backend (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

### 5) Detener el sistema

```bash
docker compose down
```

---

## 🧪 Pruebas del sistema

### 1. Registro / Login

* Endpoint: `POST /auth/register`
* Endpoint: `POST /auth/login`
* Requiere correo `@uce.edu.ec`

### 2. CRUD de tareas

* `POST /tasks`
* `GET /tasks`
* `PUT /tasks/{id}`
* `DELETE /tasks/{id}`

### 3. Reporte combinado

* `GET /reports/tasks-with-last-change`

---

## 📊 Reporte combinado

El reporte combina:

* Datos de tareas almacenadas en PostgreSQL
* Última acción registrada en MongoDB

Este reporte demuestra el uso simultáneo de múltiples orígenes de datos.

---

## 💾 Respaldos de bases de datos

Los respaldos se encuentran en la carpeta `backups/`.

### Generar dump de PostgreSQL

```bash
docker compose exec -T postgres pg_dump -U appuser taskdb > backups/postgres_dump.sql
```

### Generar dump de MongoDB

```bash
docker compose exec -T mongo mongodump --archive > backups/mongo_dump.archive
```

### Restaurar PostgreSQL

```bash
docker compose exec -T postgres psql -U appuser -d taskdb < backups/postgres_dump.sql
```

### Restaurar MongoDB

```bash
docker compose exec -T mongo mongorestore --archive < backups/mongo_dump.archive
```

---

## 🧹 Consideraciones finales

* El proyecto **no incluye** dependencias descargables (`node_modules`, `.venv`, etc.).
* El sistema es portable mediante Docker y Docker Hub.
* Cumple con los requisitos establecidos en el enunciado.

---

## 👨‍💻 Autores

* Diego Lema
* Jefferson Pilataxi
* Juan Tulcanaza

Proyecto desarrollado con fines académicos
Materia: **Arquitectura de Software**
