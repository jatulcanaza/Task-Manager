# 📌 Sistema de Gestión de Tareas  
**Arquitectura de Software – Proyecto Académico**

---

## 📖 Descripción general

Este proyecto implementa un **Sistema de Gestión de Tareas** basado en una **arquitectura de software distribuida**, desplegada mediante **contenedores Docker**, que utiliza **dos orígenes de datos diferentes** y aplica los **patrones de diseño Abstract Factory, DAO y DTO**.

El sistema permite a los usuarios autenticarse con un **correo institucional @uce.edu.ec**, gestionar tareas (CRUD) y consultar un **reporte combinado** que integra información proveniente de ambas bases de datos.

---

## 🎯 Objetivos del proyecto

- Implementar una arquitectura basada en contenedores.
- Utilizar **dos bases de datos distintas**, justificando su uso.
- Aplicar patrones de diseño vistos en clase:
  - Abstract Factory
  - DAO (Data Access Object)
  - DTO (Data Transfer Object)
- Exponer un **servicio web** para operaciones CRUD.
- Generar un **reporte combinado** a partir de ambos orígenes de datos.
- Facilitar la portabilidad del sistema a cualquier computador.

---

## 🏗️ Arquitectura del sistema

La arquitectura está compuesta por los siguientes contenedores:

| Contenedor | Tecnología | Función |
|-----------|------------|--------|
| frontend  | Nginx + HTML/CSS/JS | Interfaz web |
| backend   | FastAPI (Python) | API REST |
| postgres  | PostgreSQL | Usuarios y tareas |
| mongo     | MongoDB | Logs e historial |

---

## 🗄️ Orígenes de datos y justificación

### 🐘 PostgreSQL
- Almacena **usuarios y tareas**
- Soporta relaciones, integridad referencial y transacciones ACID
- Ideal para datos estructurados y operaciones CRUD

### 🍃 MongoDB
- Almacena **logs e historial de cambios**
- Maneja documentos flexibles sin esquema rígido
- Ideal para auditoría y crecimiento de registros

---

## 🧩 Patrones de diseño aplicados

### Abstract Factory
Permite instanciar familias de objetos DAO según el origen de datos:
- `PostgresFactory`
- `MongoFactory`

### DAO (Data Access Object)
Encapsula el acceso a datos:
- `UserDAO`, `TaskDAO` (PostgreSQL)
- `LogDAO` (MongoDB)

### DTO (Data Transfer Object)
Define y valida los datos intercambiados:
- `AuthDTO`, `TaskDTO`, `ReportDTO`

---

## 🚀 Funcionalidades principales

- Registro e inicio de sesión con correo institucional
- Gestión de tareas (crear, listar, actualizar, eliminar)
- Autenticación con JWT
- Registro de logs en MongoDB
- Reporte combinado:
  - Tareas (PostgreSQL)
  - Última acción (MongoDB)
- Interfaz web simple para demostración

---

## 📂 Estructura del proyecto

```

task-manager-arch/
├─ docker-compose.yml
├─ Lema_Pilataxi_Tulcanaza.pdf
├─ README.md
├─ .env
├─ .gitignore
├─ frontend/
│  └─ Dockerfile
│  └─ ngnix.conf
│  └─ public/
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
