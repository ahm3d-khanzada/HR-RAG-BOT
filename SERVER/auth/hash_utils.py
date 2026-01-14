# import bcrypt

# def hash_password(password: str) -> str:
#     """Hash a plain text password"""
#     return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# def verify_password(password: str, hashed: str) -> bool:
#     """Verify a plain text password against a hashed password"""
#     return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# filename: auth/hash_utils.py
import bcrypt
import hashlib

def hash_password(password: str) -> str:
    """Hash a plain text password"""
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256(password_bytes).digest()
    return bcrypt.hashpw(sha256_hash, bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a plain text password against a hashed password"""
    if not password or not hashed:
        return False
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256(password_bytes).digest()
    if hashed.startswith('$bcrypt-sha256$'):
        parts = hashed.split('$')
        if len(parts) != 5:
            return False
        type_rounds = parts[2].split(',')
        if len(type_rounds) != 2:
            return False
        type_, rounds = type_rounds
        inner_hash = f'${type_}${rounds}${parts[3]}${parts[4]}'.encode('utf-8')
        return bcrypt.checkpw(sha256_hash, inner_hash)
    else:
        return bcrypt.checkpw(sha256_hash, hashed.encode('utf-8'))