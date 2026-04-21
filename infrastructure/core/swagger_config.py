from flask import Blueprint
from flasgger import Swagger
from infrastructure.core.safety import SecureLogger

class SwaggerConfig:
    """
    Configuración de Swagger/OpenAPI para documentación automática de API
    """
    
    def __init__(self):
        self.config = {
            "headers": [],
            "specs": [
                {
                    "endpoint": 'apispec_1',
                    "route": '/apispec_1.json',
                    "rule_filter": lambda rule: True,
                    "model_filter": lambda tag: True,
                }
            ],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/apidocs/",
            "swagger_url": "/apidocs/",
            "openapi": "3.0.2",
            "swagger": {
                "title": "AgendaSDB API Documentation",
                "version": "1.0.0",
                "description": """
                ## Agenda Salesiana SDB API
                
                Sistema de Gestión Institucional para la Inspectoría de las Antillas
                
                ### Autenticación
                La API soporta dos métodos de autenticación:
                1. **Sesión tradicional** - Para uso con frontend web
                2. **JWT Tokens** - Para aplicaciones móviles y APIs externas
                
                ### Seguridad
                - Rate limiting en todos los endpoints de autenticación
                - Tokens JWT con expiración de 15 minutos
                - Soporte para 2FA (Two-Factor Authentication)
                - Encriptación de secrets sensibles
                - Headers de seguridad HTTP
                
                ### Errores
                La API utiliza códigos de estado HTTP estándar:
                - `200` - Éxito
                - `201` - Recurso creado
                - `400` - Solicitud inválida
                - `401` - No autorizado
                - `403` - Prohibido
                - `404` - No encontrado
                - `429` - Demasiadas solicitudes (Rate limiting)
                - `500` - Error del servidor
                
                ### Formato de Respuesta
                ```json
                {
                  "success": true|false,
                  "message": "Mensaje descriptivo",
                  "data": {} // Opcional
                }
                ```
                """,
                "termsOfService": "/tos",
                "contact": {
                    "name": "API Support",
                    "url": "https://salesianos.com/support",
                    "email": "support@salesianos.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                },
                "servers": [
                    {
                        "url": "http://localhost:5000",
                        "description": "Development server"
                    },
                    {
                        "url": "https://agendasdb.onrender.com",
                        "description": "Production server"
                    }
                ],
                "components": {
                    "securitySchemes": {
                        "SessionAuth": {
                            "type": "apiKey",
                            "in": "cookie",
                            "name": "session",
                            "description": "Autenticación por sesión Flask"
                        },
                        "BearerAuth": {
                            "type": "http",
                            "scheme": "bearer",
                            "bearerFormat": "JWT",
                            "description": "Autenticación JWT Bearer Token"
                        }
                    },
                    "schemas": {
                        "User": {
                            "type": "object",
                            "properties": {
                                "_id": {
                                    "type": "string",
                                    "description": "ID único del usuario"
                                },
                                "nombre": {
                                    "type": "string",
                                    "description": "Nombre completo del usuario"
                                },
                                "email": {
                                    "type": "string",
                                    "format": "email",
                                    "description": "Correo electrónico"
                                },
                                "user": {
                                    "type": "string",
                                    "description": "Nombre de usuario"
                                },
                                "rol": {
                                    "type": "string",
                                    "enum": ["user", "admin", "superadmin"],
                                    "description": "Rol del usuario"
                                },
                                "avatar": {
                                    "type": "string",
                                    "description": "URL del avatar"
                                },
                                "activo": {
                                    "type": "boolean",
                                    "description": "Estado del usuario"
                                },
                                "2fa_enabled": {
                                    "type": "boolean",
                                    "description": "2FA habilitado"
                                }
                            }
                        },
                        "LoginRequest": {
                            "type": "object",
                            "required": ["email", "password"],
                            "properties": {
                                "email": {
                                    "type": "string",
                                    "format": "email",
                                    "description": "Correo electrónico"
                                },
                                "password": {
                                    "type": "string",
                                    "minLength": 6,
                                    "description": "Contraseña"
                                },
                                "remember": {
                                    "type": "boolean",
                                    "description": "Recordar sesión"
                                }
                            }
                        },
                        "JWTLoginRequest": {
                            "type": "object",
                            "required": ["email", "password"],
                            "properties": {
                                "email": {
                                    "type": "string",
                                    "format": "email",
                                    "description": "Correo electrónico"
                                },
                                "password": {
                                    "type": "string",
                                    "minLength": 6,
                                    "description": "Contraseña"
                                }
                            }
                        },
                        "JWTLoginResponse": {
                            "type": "object",
                            "properties": {
                                "success": {
                                    "type": "boolean"
                                },
                                "access_token": {
                                    "type": "string",
                                    "description": "JWT Access Token (15 min)"
                                },
                                "refresh_token": {
                                    "type": "string",
                                    "description": "JWT Refresh Token (30 días)"
                                },
                                "token_type": {
                                    "type": "string",
                                    "enum": ["Bearer"]
                                },
                                "expires_in": {
                                    "type": "integer",
                                    "description": "Tiempo de expiración en segundos"
                                }
                            }
                        },
                        "ErrorResponse": {
                            "type": "object",
                            "properties": {
                                "success": {
                                    "type": "boolean",
                                    "enum": [false]
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Mensaje de error"
                                }
                            }
                        },
                        "TwoFactorSetup": {
                            "type": "object",
                            "properties": {
                                "success": {
                                    "type": "boolean"
                                },
                                "qr_code": {
                                    "type": "string",
                                    "description": "QR Code en base64"
                                },
                                "secret": {
                                    "type": "string",
                                    "description": "Secret TOTP (mostrado solo una vez)"
                                },
                                "message": {
                                    "type": "string"
                                }
                            }
                        },
                        "Casa": {
                            "type": "object",
                            "properties": {
                                "_id": {
                                    "type": "string"
                                },
                                "nombre": {
                                    "type": "string",
                                    "description": "Nombre de la casa/institución"
                                },
                                "ciudad": {
                                    "type": "string",
                                    "description": "Ciudad"
                                },
                                "pais": {
                                    "type": "string",
                                    "description": "País"
                                },
                                "tipo": {
                                    "type": "string",
                                    "enum": ["colegio", "parroquia", "centro_juvenil", "otro"],
                                    "description": "Tipo de institución"
                                },
                                "activo": {
                                    "type": "boolean",
                                    "description": "Estado de la casa"
                                },
                                "obras": {
                                    "type": "array",
                                    "items": {
                                        "$ref": "#/components/schemas/Obra"
                                    }
                                }
                            }
                        },
                        "Obra": {
                            "type": "object",
                            "properties": {
                                "nombre_obra": {
                                    "type": "string",
                                    "description": "Nombre de la obra"
                                },
                                "ciudad": {
                                    "type": "string",
                                    "description": "Ciudad de la obra"
                                },
                                "tipo": {
                                    "type": "string",
                                    "description": "Tipo de obra"
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def init_app(self, app):
        """Inicializar Swagger con la aplicación Flask"""
        try:
            Swagger(app, config=self.config)
            SecureLogger.safe_log("Swagger/OpenAPI documentation initialized")
            SecureLogger.safe_log("API docs available at /apidocs/")
        except Exception as e:
            SecureLogger.safe_log(f"Error initializing Swagger: {str(e)}", "ERROR")

# Instancia global
swagger_config = SwaggerConfig()

def init_swagger(app):
    """Inicializar documentación Swagger"""
    swagger_config.init_app(app)
    return swagger_config
