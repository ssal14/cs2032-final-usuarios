import json
import os
import uuid
import hashlib
from datetime import datetime, timedelta, timezone

import boto3

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _respuesta(status_code, cuerpo_dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(cuerpo_dict, default=str),
    }


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def validar_token(event):
    """
    Copia esta función (tal cual) en los demás microservicios.
    Devuelve (tenant_id, None) si el token es válido,
    o (None, respuesta_error) si no lo es.
    """
    headers = event.get("headers") or {}
    auth_header = headers.get("Authorization") or headers.get("authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None, _respuesta(401, {"error": "Token no enviado"})

    token = auth_header.replace("Bearer ", "").strip()
    tabla_tokens = dynamodb.Table(os.environ["TOKENS_TABLE"])
    item = tabla_tokens.get_item(Key={"token": token}).get("Item")

    if not item:
        return None, _respuesta(401, {"error": "Token inválido"})

    if datetime.now(timezone.utc).isoformat() > item["fecha_expiracion"]:
        return None, _respuesta(401, {"error": "Token expirado"})

    return item["tenant_id"], None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def crear_usuario(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        tenant_id = body["tenant_id"]
        nombre = body["nombre"]
        email = body["email"]
        password = body["password"]
        rol = body.get("rol", "reclutador")
    except (KeyError, json.JSONDecodeError):
        return _respuesta(400, {"error": "Faltan campos: tenant_id, nombre, email, password"})

    tabla_usuarios = dynamodb.Table(os.environ["USUARIOS_TABLE"])
    usuario_id = str(uuid.uuid4())

    tabla_usuarios.put_item(
        Item={
            "tenant_id": tenant_id,
            "usuario_id": usuario_id,
            "nombre": nombre,
            "email": email,
            "password_hash": _hash_password(password),
            "rol": rol,
            "fecha_registro": datetime.now(timezone.utc).isoformat(),
        }
    )

    return _respuesta(201, {"usuario_id": usuario_id, "tenant_id": tenant_id})


def login_usuario(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        tenant_id = body["tenant_id"]
        email = body["email"]
        password = body["password"]
    except (KeyError, json.JSONDecodeError):
        return _respuesta(400, {"error": "Faltan campos: tenant_id, email, password"})

    tabla_usuarios = dynamodb.Table(os.environ["USUARIOS_TABLE"])

    # Query por tenant_id (partition key) y filtramos por email en memoria,
    # suficiente para el volumen de usuarios/reclutadores de este proyecto.
    resp = tabla_usuarios.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("tenant_id").eq(tenant_id)
    )
    usuario = next((u for u in resp["Items"] if u["email"] == email), None)

    if not usuario or usuario["password_hash"] != _hash_password(password):
        return _respuesta(401, {"error": "Credenciales inválidas"})

    token = str(uuid.uuid4())
    fecha_expiracion = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    tabla_tokens = dynamodb.Table(os.environ["TOKENS_TABLE"])
    tabla_tokens.put_item(
        Item={
            "token": token,
            "tenant_id": tenant_id,
            "usuario_id": usuario["usuario_id"],
            "fecha_creacion": datetime.now(timezone.utc).isoformat(),
            "fecha_expiracion": fecha_expiracion,
        }
    )

    return _respuesta(200, {"token": token, "fecha_expiracion": fecha_expiracion})


def validar_token_endpoint(event, context):
    tenant_id, error = validar_token(event)
    if error:
        return error
    return _respuesta(200, {"tenant_id": tenant_id, "valido": True})
