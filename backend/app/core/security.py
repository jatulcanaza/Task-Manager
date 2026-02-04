from datetime import datetime, timedelta  # Manejo de fechas para expiración del token
from jose import jwt, JWTError  # jwt para encode/decode; JWTError para capturar errores de validación
import bcrypt  # Librería de hashing seguro para contraseñas
from app.core.config import settings  # Acceso a variables de configuración (JWT_SECRET, JWT_EXPIRES_MIN, etc.)

# Algoritmo de firma del JWT (HMAC + SHA-256)
ALGO = "HS256"


def hash_password(pw: str) -> str:
    """
    Hashea una contraseña en texto plano usando bcrypt.
    - bcrypt trabaja con bytes, por eso se codifica a utf-8.
    - Se genera un salt con costo (rounds=12) para aumentar la seguridad.
    - Retorna el hash como string (utf-8) para poder guardarlo en la base de datos.
    """
    # bcrypt recibe bytes
    pw_bytes = pw.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")  # guardamos string en DB


def verify_password(pw: str, hashed: str) -> bool:
    """
    Verifica una contraseña en texto plano contra un hash bcrypt almacenado.
    - Convierte ambos valores a bytes.
    - bcrypt.checkpw devuelve True si coincide, False si no.
    """
    pw_bytes = pw.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pw_bytes, hashed_bytes)


def create_access_token(sub: str) -> str:
    """
    Crea un JWT de acceso (access token).
    - 'sub' (subject) representa la identidad del usuario (por ejemplo, user_id).
    - 'exp' define la fecha/hora de expiración del token.
    - La expiración se calcula usando JWT_EXPIRES_MIN desde la configuración.
    - Retorna el token firmado como string.
    """
    exp = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MIN)
    payload = {"sub": sub, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGO)


def decode_token(token: str) -> str:
    """
    Decodifica y valida un JWT.
    - Verifica firma y expiración usando el JWT_SECRET y el algoritmo configurado.
    - Si es válido, retorna el 'sub' (subject) contenido en el payload.
    - Si falla (token inválido/expirado/mal formado), lanza ValueError.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGO])
        return payload["sub"]
    except JWTError as e:
        # Se encapsula el error original de jose en un ValueError más simple para el resto de la app
        raise ValueError("Token inválido") from e
