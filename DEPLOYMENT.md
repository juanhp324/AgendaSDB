# Guía de Despliegue - AgendaSDB

## Overview

AgendaSDB es un sistema de gestión institucional para la Inspectoría Salesiana de las Antillas. Esta guía cubre el despliegue en producción usando Render.com.

## Requisitos Previos

### Software Necesario
- Python 3.11+
- MongoDB Atlas (base de datos)
- Redis (para rate limiting y cache)
- Git (para control de versiones)

### Servicios Externos
- **MongoDB Atlas**: Base de datos NoSQL
- **Redis**: Para rate limiting, cache y blacklist de tokens
- **Render.com**: Plataforma de despliegue (recomendada)

## Configuración de Variables de Entorno

### 1. Copiar `.env.example` a `.env`

```bash
cp .env.example .env
```

### 2. Configurar variables obligatorias

```bash
# Generar claves seguras
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')

# Editar .env
nano .env
```

### 3. Variables de entorno requeridas

```bash
# Configuración básica
SECRET_KEY=tu_clave_secreta_generada
FLASK_ENV=production
DATABASE_NAME=AgendaSDB

# Base de datos
MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/AgendaSDB

# Redis (obligatorio para rate limiting)
REDIS_URL=redis://usuario:password@host:puerto

# Monitoreo (recomendado para producción)
SENTRY_DSN=https://tu_dsn@sentry.io/project_id

# Encriptación (para 2FA secrets)
ENCRYPTION_KEY=tu_clave_encripcion_generada
```

## Despliegue en Render.com

### 1. Preparar el Repositorio

```bash
# Asegurarse que .env está en .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore

# Commit de cambios
git add .
git commit -m "Add security enhancements and deployment config"
git push origin main
```

### 2. Configurar en Render

1. **Crear cuenta en [Render.com](https://render.com)**
2. **Conectar repositorio GitHub**
3. **Crear Web Service**:
   - **Name**: `agenda-sdb`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free` (para empezar)

### 3. Configurar Variables de Entorno en Render

En el dashboard de Render, ir a `Environment` y agregar:

```bash
PYTHON_VERSION=3.11.0
MONGODB_URI=tu_mongodb_uri
DATABASE_NAME=AgendaSDB
SECRET_KEY=tu_clave_secreta
REDIS_URL=tu_redis_url
FLASK_ENV=production
SENTRY_DSN=tu_sentry_dsn (opcional)
ENCRYPTION_KEY=tu_clave_encripcion
```

### 4. Agregar Redis Addon

1. En el dashboard del servicio, ir a `Add-ons`
2. Buscar `Redis`
3. Seleccionar plan `Free` o `Starter`
4. Render agregará automáticamente `REDIS_URL`

### 5. Configurar MongoDB Atlas

1. **Crear cuenta en [MongoDB Atlas](https://cloud.mongodb.com)**
2. **Crear cluster** (M0 Free es suficiente para empezar)
3. **Configurar Network Access**:
   - Agregar IP: `0.0.0.0/0` (permitir acceso desde cualquier lugar)
4. **Crear usuario de base de datos**:
   - Username: `agenda_user`
   - Password: contraseña segura
5. **Obtener Connection String**:
   - Click en `Connect` > `Connect your application`
   - Copiar el URI (reemplazar `<password>`)

### 6. Configurar Sentry (Opcional pero recomendado)

1. **Crear cuenta en [Sentry.io](https://sentry.io)**
2. **Crear nuevo proyecto**: `Flask`
3. **Obtener DSN** desde settings del proyecto
4. **Configurar `SENTRY_DSN`** en variables de entorno

## Verificación del Despliegue

### 1. Verificar que la aplicación está corriendo

```bash
# Test local
curl http://localhost:5000/health

# Test producción
curl https://tu-app.onrender.com/health
```

### 2. Verificar endpoints críticos

```bash
# Health check
curl https://tu-app.onrender.com/health

# API docs
curl https://tu-app.onrender.com/apidocs/

# Test login
curl -X POST https://tu-app.onrender.com/Login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass"}'
```

### 3. Verificar logs

En el dashboard de Render:
- Ir a `Logs`
- Buscar errores o advertencias
- Verificar que no haya claves secretas en los logs

## Monitoreo y Mantenimiento

### 1. Health Checks

La aplicación incluye un endpoint `/health` que retorna:
- Status de la aplicación
- Conexión a MongoDB
- Conexión a Redis
- Versión

### 2. Logs y Monitoreo

- **Render Logs**: Disponibles en el dashboard
- **Sentry**: Si está configurado, captura errores automáticamente
- **Rate Limiting**: Monitorear intentos de login fallidos

### 3. Backups

- **MongoDB**: Atlas incluye backups automáticos
- **Redis**: Render maneja persistencia
- **Código**: Versionado en Git

## Configuración de Seguridad

### 1. Headers de Seguridad

La aplicación incluye automáticamente:
- Content Security Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- Strict-Transport-Security (en producción)

### 2. Rate Limiting

- **Login**: 5 intentos por minuto
- **JWT Refresh**: 10 intentos por minuto
- **2FA**: 3 intentos por sesión

### 3. Autenticación

- **JWT Tokens**: 15 minutos de expiración
- **Refresh Tokens**: 30 días de expiración
- **2FA**: Opcional pero recomendado para admin

## Troubleshooting

### Problemas Comunes

#### 1. Error de conexión a MongoDB
```bash
# Verificar URI
echo $MONGODB_URI

# Test conexión
python -c "
from pymongo import MongoClient
client = MongoClient('$MONGODB_URI')
client.admin.command('ping')
print('MongoDB OK')
"
```

#### 2. Error de conexión a Redis
```bash
# Test conexión
python -c "
import redis
r = redis.from_url('$REDIS_URL')
r.ping()
print('Redis OK')
"
```

#### 3. Error de SECRET_KEY
```bash
# Verificar que no sea el default
if [ "$SECRET_KEY" = "agenda_secret_key_2024" ]; then
  echo "ERROR: Usando SECRET_KEY por defecto"
fi
```

#### 4. Error de permisos
```bash
# Verificar que el usuario tiene permisos en MongoDB
mongosh "$MONGODB_URI" --eval "
db.usuarios.find().limit(1)
"
```

### Logs Útiles

```bash
# Logs de aplicación
tail -f logs/app.log

# Logs de errores
tail -f logs/error.log

# Logs de seguridad
grep "SECURITY_EVENT" logs/app.log
```

## Escalado

### 1. Vertical Scaling

En Render:
- Cambiar a `Starter` o `Standard` instance
- Más RAM y CPU

### 2. Horizontal Scaling

- Render maneja automáticamente múltiples instancias
- Redis compartido entre instancias
- MongoDB Atlas escala automáticamente

### 3. Performance

- Habilitar cache en Redis
- Optimizar queries de MongoDB
- Usar CDN para assets estáticos

## Backup y Recovery

### 1. MongoDB

```bash
# Exportar datos
mongodump --uri="$MONGODB_URI" --out=backup/

# Importar datos
mongorestore --uri="$MONGODB_URI" backup/
```

### 2. Configuración

```bash
# Backup de variables de entorno
env | grep -E "^(SECRET|MONGODB|REDIS|SENTRY)" > env.backup

# Restaurar
source env.backup
```

## Soporte

### 1. Documentación

- **API Docs**: `/apidocs/`
- **README.md**: Información general
- **SECURITY_IMPLEMENTATION_SUMMARY.md**: Detalles de seguridad

### 2. Contacto

- **Issues**: GitHub Issues
- **Email**: support@salesianos.com
- **Discord**: Canal de soporte técnico

## Checklist de Despliegue

- [ ] Generar claves seguras (SECRET_KEY, ENCRYPTION_KEY)
- [ ] Configurar MongoDB Atlas
- [ ] Configurar Redis addon
- [ ] Configurar variables de entorno
- [ ] Verificar health check
- [ ] Testear endpoints críticos
- [ ] Configurar Sentry (opcional)
- [ ] Verificar logs
- [ ] Testear rate limiting
- [ ] Documentar acceso admin

## Actualizaciones

### 1. Actualizar dependencias

```bash
pip install --upgrade -r requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```

### 2. Actualizar configuración

```bash
# Editar variables de entorno en Render
# Deploy automático con cada push
```

### 3. Rollback

```bash
# Revertir a commit anterior
git revert HEAD
git push origin main
```

---

**Nota**: Esta guía asume que estás usando Render.com. Para otros proveedores (AWS, GCP, Azure), los pasos pueden variar. Consulta la documentación específica de tu proveedor.
