# cs2032-usuarios — Microservicio de Usuarios / Autenticación

Microservicio base del CRM de Empleabilidad Nacional. Gestiona el registro de
reclutadores (usuarios) por tenant y la emisión/validación de tokens de
acceso que usan los demás microservicios.

## 0. Requisitos previos (una sola vez)

```bash
# Node.js (si no lo tienes) y Serverless Framework
# (fijamos la v3 para evitar el login obligatorio que pide la v4)
npm install -g serverless@3

# Confirmar versión
serverless --version
```

## 1. Configurar credenciales de AWS (cuenta compartida / Learner Lab)

AWS Academy Learner Lab da credenciales **temporales** (caducan cada pocas
horas, hay que repetir esto cuando caduquen):

1. Entra a tu Learner Lab → botón **AWS Details** → **Show** en AWS CLI.
2. Copia el bloque `[default] aws_access_key_id / aws_secret_access_key / aws_session_token`.
3. Pégalo en `~/.aws/credentials` (créalo si no existe):

```ini
[default]
aws_access_key_id = TU_ACCESS_KEY
aws_secret_access_key = TU_SECRET_KEY
aws_session_token = TU_SESSION_TOKEN
```

4. Confirma que apunta bien:

```bash
aws sts get-caller-identity
```

Si te devuelve un `Account` y un `Arn`, estás conectado correctamente.

## 2. Instalar dependencias del proyecto

Este microservicio solo usa `boto3`, que ya viene incluido en el runtime de
Lambda — no necesitas instalar nada adicional ni empaquetar dependencias.

## 3. Desplegar

```bash
cd cs2032-final-usuarios
serverless deploy --stage dev
```

Al terminar, la terminal te muestra las URLs de los 3 endpoints, algo así:

```
endpoints:
  POST - https://xxxxxxx.execute-api.us-east-1.amazonaws.com/dev/usuarios
  POST - https://xxxxxxx.execute-api.us-east-1.amazonaws.com/dev/usuarios/login
  GET  - https://xxxxxxx.execute-api.us-east-1.amazonaws.com/dev/usuarios/validar
```

Guarda esa URL base (`https://xxxxxxx.execute-api.us-east-1.amazonaws.com/dev`)
— la necesitarás para probar y para pasársela a tus compañeros.

## 4. Probar con `curl`

### Crear un usuario en `tenant_1`

```bash
curl -X POST https://TU_URL/dev/usuarios \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "tenant_1", "nombre": "Ana Reclutadora", "email": "ana@empresa1.com", "password": "clave123"}'
```

Respuesta esperada (201): `{"usuario_id": "...", "tenant_id": "tenant_1"}`

### Login

```bash
curl -X POST https://TU_URL/dev/usuarios/login \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "tenant_1", "email": "ana@empresa1.com", "password": "clave123"}'
```

Respuesta esperada (200): `{"token": "...", "fecha_expiracion": "..."}`

Guarda ese `token`, lo vas a usar en el header `Authorization: Bearer <token>`
para probar los demás endpoints protegidos (y es el mismo que usarán Santiago,
Patrick y Sanders para probar los suyos).

### Validar token

```bash
curl https://TU_URL/dev/usuarios/validar \
  -H "Authorization: Bearer TU_TOKEN"
```

Respuesta esperada (200): `{"tenant_id": "tenant_1", "valido": true}`

### Repetir con `tenant_2` y `tenant_3`

Repite los 3 pasos anteriores cambiando `tenant_id` a `tenant_2` y `tenant_3`
(y un email distinto), para tener un usuario de prueba por cada tenant antes
de la demo.

## 5. Ver logs si algo falla

```bash
serverless logs -f crearUsuario --stage dev
serverless logs -f loginUsuario --stage dev
```

## 6. Qué compartir con el equipo

- La URL base del API (`https://xxxxxxx.execute-api.us-east-1.amazonaws.com/dev`).
- El nombre exacto de la tabla de tokens: `t_tokens_acceso-dev` (lo necesitan
  Santiago, Patrick y Sanders para que sus Lambdas puedan leerla).
- Un `token` de prueba por cada tenant, para que puedan probar sus propios
  endpoints sin tener que hacer login ellos mismos cada vez.
