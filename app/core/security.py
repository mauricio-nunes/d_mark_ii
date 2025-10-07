import bcrypt
from getpass import getpass

def hash_password(raw: str) -> bytes:
	return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt())

def check_password(raw: str, hashed: bytes) -> bool:
	try:
		return bcrypt.checkpw(raw.encode("utf-8"), hashed)
	except Exception:
		return False

def prompt_password(prompt: str = "Senha: ") -> str:
	return getpass(prompt)
