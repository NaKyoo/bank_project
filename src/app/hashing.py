from passlib.context import CryptContext
import bcrypt

#pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


class Hasher():
    @staticmethod
    def verify_password(plain_password, hashed_password):
        return bcrypt.checkpw(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password:str):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Contexte de hachage (bcrypt pour hashé et gère automatiquement les ancien format de hachage)

    # les deux méthode peuvent être appler directement comme "Hasher.verify_password"  token uid
print(Hasher.get_password_hash("Hello"))