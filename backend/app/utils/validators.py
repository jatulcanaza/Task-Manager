import re  # Módulo de expresiones regulares para validar patrones (mayúsculas, dígitos, etc.)

def validate_uce_email(email: str) -> str:
    """
    Valida y normaliza un email institucional de la UCE.
    - Elimina espacios al inicio/fin (strip)
    - Convierte a minúsculas (lower) para consistencia
    - Verifica que termine en '@uce.edu.ec'
    Retorna el email normalizado si es válido, o lanza ValueError si no lo es.
    """
    email = email.strip().lower()  # Normaliza el email (sin espacios y en minúsculas)
    if not email.endswith("@uce.edu.ec"):
        # Regla de negocio: solo se permiten correos institucionales UCE
        raise ValueError("El correo debe ser institucional @uce.edu.ec")
    return email  # Email válido y normalizado

def validate_password(pw: str) -> str:
    """
    Valida una contraseña según reglas mínimas:
    - Longitud mínima: 8 caracteres
    - Debe incluir al menos 1 letra mayúscula
    - Debe incluir al menos 1 número
    Retorna la contraseña original si cumple, o lanza ValueError si falla.
    """
    if len(pw) < 8:
        # Evita contraseñas demasiado cortas
        raise ValueError("La contraseña debe tener al menos 8 caracteres")

    # opcional: una mayúscula y un número
    # re.search(...) devuelve un match si encuentra el patrón en cualquier parte del string
    if not re.search(r"[A-Z]", pw) or not re.search(r"\d", pw):
        # Si falta una mayúscula o falta un dígito => inválida
        raise ValueError("La contraseña debe incluir al menos 1 mayúscula y 1 número")

    return pw  # Contraseña válida (se devuelve tal cual; el hash se hace en otra capa)
