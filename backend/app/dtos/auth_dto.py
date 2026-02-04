from pydantic import BaseModel, field_validator  # BaseModel para DTOs; field_validator para validaciones por campo (Pydantic v2)
from app.utils.validators import validate_uce_email, validate_password  # Validadores custom (correo institucional y reglas de password)

class RegisterDTO(BaseModel):
    """
    DTO (Data Transfer Object) para el registro de usuario.
    Define la estructura esperada del payload y valida campos antes de llegar a la lógica de negocio.
    """
    email: str     # Email del usuario a registrar
    password: str  # Contraseña en texto plano (se validará aquí; luego se hashea antes de persistir)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        # Valida que el email cumpla el formato/reglas esperadas (por ejemplo, dominio institucional UCE)
        # Debe retornar el valor (posiblemente normalizado) o lanzar excepción si es inválido
        return validate_uce_email(v)

    @field_validator("password")
    @classmethod
    def _pw(cls, v: str) -> str:
        # Valida reglas de contraseña (longitud mínima, complejidad, etc.) según validate_password
        # Debe retornar el valor o lanzar excepción si es inválido
        return validate_password(v)

class LoginDTO(BaseModel):
    """
    DTO para login.
    Define campos requeridos para autenticación.
    Nota: aquí solo se valida el email (según este código); la contraseña se verifica contra el hash en BD.
    """
    email: str     # Email del usuario
    password: str  # Contraseña ingresada (se comparará con el hash almacenado)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        # Reutiliza la misma validación de email institucional
        return validate_uce_email(v)

class TokenDTO(BaseModel):
    """
    DTO de respuesta para entrega de tokens.
    Usualmente se devuelve al hacer login o refresh.
    """
    access_token: str            # JWT generado por el backend
    token_type: str = "bearer"   # Tipo de token usado en Authorization header: "Bearer <token>"
