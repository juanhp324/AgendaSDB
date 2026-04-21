# AgendaSDB API Documentation

## Overview

AgendaSDB is a management system for Salesian institutions with role-based access control, security features, and comprehensive reporting capabilities.

## Base URL
```
http://localhost:5000
```

## Authentication

The application uses session-based authentication with CSRF protection. All POST/PUT/DELETE/PATCH requests require a valid CSRF token.

### Headers Required for State-Changing Requests:
- `X-CSRF-Token: <csrf_token>` OR include `csrf_token` in form data/json payload

## Security Features

- **Rate Limiting**: 5 requests per minute for login attempts
- **CSRF Protection**: Required for all state-changing requests
- **Session Management**: 30-day persistent sessions
- **Input Validation**: Comprehensive validation on all endpoints
- **Secure Logging**: Credentials are automatically redacted from logs

## API Endpoints

### Authentication Routes (`/Login`, `/logout`, `/get_perfil`, `/update_perfil`)

#### POST `/Login`
Authenticate user and create session.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "remember": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "redirect": "/inicio",
  "user_info": {
    "nombre": "John Doe",
    "avatar": "avatar.jpg",
    "email": "user@example.com"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Invalid credentials
- `404 Not Found`: User not found

#### GET `/logout`
Clear user session and redirect to login.

#### GET `/get_perfil`
Get current user profile information.

**Response (200 OK):**
```json
{
  "success": true,
  "usuario": {
    "_id": "507f1f77bcf86cd799439011",
    "nombre": "John Doe",
    "email": "user@example.com",
    "user": "johndoe",
    "rol": "admin",
    "avatar": "avatar.jpg"
  }
}
```

#### PUT `/update_perfil`
Update current user profile.

**Request Body:**
```json
{
  "nombre": "John Smith",
  "email": "johnsmith@example.com",
  "password": "newpassword123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Perfil actualizado"
}
```

### Casa Management Routes (`/casas`, `/get_casas`, `/create_casa`, etc.)

#### GET `/casas`
Render casas management page (HTML).

#### GET `/casa/<casa_id>`
Render specific casa details page (HTML).

#### GET `/get_casas`
Get all casas with optional filtering.

**Query Parameters:**
- `q` (optional): Search query string
- `tipo` (optional): Filter by type ('masculino', 'femenino', 'todos')

**Response (200 OK):**
```json
{
  "success": true,
  "casas": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "nombre": "Instituto Salesiano",
      "obras": [
        {
          "nombre_obra": "Escuela Primaria",
          "ciudad": "La Vega",
          "telefono": ["809-123-4567"],
          "correo": ["info@escuela.com"]
        }
      ],
      "historia": "Historia del instituto...",
      "tipo": "masculino"
    }
  ]
}
```

#### GET `/get_casa/<casa_id>`
Get specific casa details.

**Response (200 OK):**
```json
{
  "success": true,
  "casa": {
    "_id": "507f1f77bcf86cd799439011",
    "nombre": "Instituto Salesiano",
    "obras": [...],
    "historia": "Historia...",
    "tipo": "masculino"
  }
}
```

#### POST `/upload_logo`
Upload logo file for casa.

**Permissions Required:** `casas:crear`

**Request:** `multipart/form-data` with file field `logo`

**Response (200 OK):**
```json
{
  "success": true,
  "filename": "logo.jpg"
}
```

#### POST `/create_casa`
Create new casa.

**Permissions Required:** `casas:crear`

**Request Body:**
```json
{
  "nombre": "Nuevo Instituto",
  "tipo": "masculino",
  "historia": "Historia del nuevo instituto...",
  "obras": [
    {
      "nombre_obra": "Escuela",
      "ciudad": "Ciudad",
      "telefono": ["809-123-4567"],
      "correo": ["info@escuela.com"]
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Instituto Salesiano creado exitosamente",
  "casa_id": "507f1f77bcf86cd799439011"
}
```

#### PUT `/update_casa/<casa_id>`
Update existing casa.

**Permissions Required:** `casas:editar`

**Request Body:** Same structure as create_casa

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Instituto actualizado exitosamente"
}
```

#### DELETE `/delete_casa/<casa_id>`
Delete casa.

**Permissions Required:** `casas:eliminar`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Instituto eliminado exitosamente"
}
```

### User Management Routes (`/usuarios`, `/get_usuarios`, `/create_usuario`, etc.)

#### GET `/usuarios`
Render user management page (HTML).

**Permissions Required:** `admin` or `superadmin` role

#### GET `/get_usuarios`
Get all users with role-based filtering.

**Permissions Required:** `usuarios:ver`

**Response (200 OK):**
```json
{
  "success": true,
  "usuarios": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "nombre": "John Doe",
      "email": "john@example.com",
      "user": "johndoe",
      "rol": "user",
      "avatar": "avatar.jpg",
      "activo": true
    }
  ]
}
```

#### POST `/create_usuario`
Create new user.

**Permissions Required:** `usuarios:crear`

**Request Body:**
```json
{
  "nombre": "Jane Doe",
  "email": "jane@example.com",
  "user": "janedoe",
  "password": "password123",
  "rol": "user"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Usuario creado",
  "usuario_id": "507f1f77bcf86cd799439011"
}
```

#### PUT `/update_usuario/<user_id>`
Update existing user.

**Permissions Required:** `usuarios:editar`

**Request Body:** Same structure as create_usuario (all fields optional)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Usuario actualizado"
}
```

#### DELETE `/delete_usuario/<user_id>`
Delete user.

**Permissions Required:** `usuarios:eliminar`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Usuario eliminado"
}
```

### Dashboard Routes (`/inicio`)

#### GET `/inicio`
Render main dashboard page (HTML).

### Reporting Routes

#### GET `/reporte_casas`
Generate PDF report of all casas grouped by type.

**Response:** PDF file download

#### GET `/reporte_casa/<casa_id>`
Generate PDF report for specific casa.

**Response:** PDF file download

#### GET `/reporte_obra/<casa_id>/<obra_id>`
Generate PDF report for specific obra.

**Response:** PDF file download

#### GET `/reporte_casas_word`
Generate Word document report of all casas.

**Response:** Word document download

#### GET `/reporte_casa_word/<casa_id>`
Generate Word document report for specific casa.

**Response:** Word document download

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "message": "Error description"
}
```

Common HTTP Status Codes:
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Authentication required/failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

- **Login endpoint**: 5 attempts per minute per IP
- **Rate limiter**: Redis-based with fallback to in-memory
- **Headers**: Rate limit information included in response headers

## CSRF Protection

All state-changing requests (POST, PUT, DELETE, PATCH) must include a valid CSRF token:

1. Token is automatically injected into templates as `csrf_token`
2. Include in requests as:
   - Form field: `csrf_token=<token>`
   - Header: `X-CSRF-Token: <token>`
   - JSON payload: `{"csrf_token": "<token>"}`

## Permission System

The application uses a role-based permission system:

### Roles:
- `user`: Basic user access
- `admin`: Administrative access (limited)
- `superadmin`: Full administrative access

### Permissions:
- `casas:ver`, `casas:crear`, `casas:editar`, `casas:eliminar`
- `usuarios:ver`, `usuarios:crear`, `usuarios:editar`, `usuarios:eliminar`

## Data Validation

All input data is validated using domain validators. Common validation rules:

- **Email**: Valid email format
- **Passwords**: Minimum length requirements
- **Required Fields**: All required fields must be present
- **Data Types**: Proper data type validation
- **SQL Injection**: Protection through parameterized queries

## Security Headers

The application implements several security measures:
- Secure session configuration
- CSRF token validation
- Input sanitization
- Rate limiting
- Secure logging (credential redaction)

## Environment Configuration

Required environment variables:
- `SECRET_KEY`: Application secret key (must be secure, not default)
- `MONGODB_URI`: MongoDB connection string
- `DATABASE_NAME`: MongoDB database name
- `REDIS_URL` (optional): Redis connection URL for rate limiting

## Development vs Production

### Development:
- Debug mode disabled (`debug=False`)
- Detailed error messages
- Development database

### Production:
- Debug mode disabled
- Error logging without sensitive data
- Redis rate limiting
- Secure session configuration

## Testing

Run automated tests:
```bash
pytest tests/ --cov=. --cov-report=html
```

Test coverage includes:
- Security features
- Rate limiting
- CSRF protection
- Input validation
- Permission system
