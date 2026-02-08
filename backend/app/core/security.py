from datetime import datetime, timedelta
# datetime:
#   - Se usa para timestamps de emisión (iat) y expiración (exp)
# timedelta:
#   - Permite calcular tiempos relativos (ej. +60 minutos)

from jose import jwt, JWTError
# jwt:
#   - Librería JOSE para crear y validar JWT (JSON Web Tokens)
# JWTError:
#   - Excepción base para errores de firma, expiración o claims inválidos

import bcrypt
# bcrypt:
#   - Algoritmo de hashing adaptativo y resistente a fuerza bruta
#   - Incluye salt automáticamente
#   - Estándar recomendado para almacenamiento de contraseñas

from app.core.config import settings
# settings:
#   - Acceso centralizado a secretos y parámetros (JWT_SECRET, expiración, etc.)

import uuid
# uuid:
#   - Se usa para generar identificadores únicos (jti) en tokens SSO


# -----------------------------------------------------------------------------
# CONSTANTES DE SEGURIDAD SSO
# -----------------------------------------------------------------------------
# iss (issuer):
#   - Identifica qué servicio emitió el token
# aud (audience):
#   - Identifica para qué servicio es válido el token
#
# Estas claims previenen:
# - Uso del token en servicios no autorizados
# - Replay attacks entre aplicaciones
SSO_ISSUER = "task-manager-auth"
SSO_AUDIENCE = "web-b"

# Algoritmo de firma JWT
# HS256 = HMAC + SHA-256 (simétrico)
ALGO = "HS256"


# -----------------------------------------------------------------------------
# PASSWORD HASHING
# -----------------------------------------------------------------------------
def hash_password(pw: str) -> str:
    """
    Hashea una contraseña en texto plano usando bcrypt.

    Detalles de seguridad:
    - bcrypt trabaja sobre bytes → se codifica a UTF-8.
    - Se genera un salt único por contraseña.
    - rounds=12 define el costo computacional (seguridad vs performance).
    - El resultado se guarda como string (UTF-8) en la base de datos.

    Nunca se almacenan contraseñas en texto plano.
    """

    # bcrypt requiere bytes
    pw_bytes = pw.encode("utf-8")

    # gensalt genera un salt aleatorio con un costo definido
    salt = bcrypt.gensalt(rounds=12)

    # hashpw combina contraseña + salt
    hashed = bcrypt.hashpw(pw_bytes, salt)

    # Se guarda como string para compatibilidad con DB
    return hashed.decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    """
    Verifica una contraseña contra un hash almacenado.

    Proceso:
    - Convierte ambos valores a bytes.
    - bcrypt.checkpw aplica el mismo algoritmo y salt.
    - Retorna True si coinciden, False si no.
    """

    pw_bytes = pw.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")

    return bcrypt.checkpw(pw_bytes, hashed_bytes)


# -----------------------------------------------------------------------------
# ACCESS TOKEN (JWT CLÁSICO)
# -----------------------------------------------------------------------------
def create_access_token(sub: str) -> str:
    """
    Crea un JWT de acceso (access token).

    Claims incluidos:
    - sub:
        Identidad del usuario (ej. UUID del usuario).
    - exp:
        Fecha/hora de expiración del token.

    Expiración:
    - Definida en minutos por JWT_EXPIRES_MIN (settings).
    """

    # Calcula la expiración
    exp = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MIN)

    # Payload mínimo y seguro
    payload = {
        "sub": sub,
        "exp": exp
    }

    # Firma el token con secreto compartido
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=ALGO
    )


def decode_token(token: str) -> str:
    """
    Decodifica y valida un JWT de acceso.

    Validaciones automáticas:
    - Firma (JWT_SECRET)
    - Algoritmo permitido
    - Expiración (exp)

    Retorna:
    - El 'sub' (subject) si el token es válido.

    En caso de error:
    - Se lanza ValueError para ocultar detalles internos.
    """

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[ALGO]
        )
        return payload["sub"]

    except JWTError as e:
        # Se encapsula el error real para no filtrar información sensible
        raise ValueError("Token inválido") from e


# -----------------------------------------------------------------------------
# SSO TOKEN (SINGLE SIGN-ON)
# -----------------------------------------------------------------------------
def create_sso_token(sub: str, minutes: int = 2) -> str:
    """
    Crea un token SSO de vida corta.

    Características:
    - Uso exclusivo para redirección entre aplicaciones (Web A → Web B).
    - Vida útil muy corta (por defecto 2 minutos).
    - Incluye claims adicionales de seguridad.

    Claims SSO:
    - sub:
        Identidad del usuario.
    - exp:
        Expiración corta.
    - iat:
        Fecha de emisión.
    - iss:
        Emisor del token (previene tokens externos).
    - aud:
        Audiencia destino (previene uso en otros servicios).
    - jti:
        ID único del token (previene replay attacks).
    """

    exp = datetime.utcnow() + timedelta(minutes=minutes)

    payload = {
        "sub": sub,
        "exp": exp,
        "iat": datetime.utcnow(),
        "iss": SSO_ISSUER,
        "aud": SSO_AUDIENCE,
        "jti": str(uuid.uuid4())
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=ALGO
    )


def decode_sso_token(token: str) -> str:
    """
    Decodifica y valida un token SSO.

    Validaciones estrictas:
    - Firma válida
    - Algoritmo permitido
    - Expiración
    - Emisor (iss)
    - Audiencia (aud)

    Retorna:
    - El 'sub' si el token es válido.
    """

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[ALGO],
            audience=SSO_AUDIENCE,
            issuer=SSO_ISSUER
        )
        return payload["sub"]

    except JWTError as e:
        raise ValueError("SSO token inválido") from e
