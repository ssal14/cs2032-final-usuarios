import boto3
import hashlib
import uuid
from datetime import datetime, timezone
from faker import Faker

fake = Faker()
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
tabla_usuarios = dynamodb.Table("t_usuarios-dev")

CANTIDAD_POR_TENANT = 100
TENANTS = ["tenant_1", "tenant_2", "tenant_3"]

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

for tenant_id in TENANTS:
    for _ in range(CANTIDAD_POR_TENANT):
        tabla_usuarios.put_item(
            Item={
                "tenant_id": tenant_id,
                "usuario_id": str(uuid.uuid4()),
                "nombre": fake.name(),
                "email": fake.unique.email(),
                "password_hash": hash_password("clave123"),
                "rol": "reclutador",
                "fecha_registro": datetime.now(timezone.utc).isoformat(),
            }
        )
    print(f"{CANTIDAD_POR_TENANT} usuarios cargados en {tenant_id}")

print("Listo.")
