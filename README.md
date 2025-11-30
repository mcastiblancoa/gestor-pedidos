# Gestor de Pedidos — API REST (Django + MongoDB)

API REST sin interfaz gráfica para gestionar pedidos de inventario con foco en rendimiento/latencia para `PATCH /orders/{id}/status/`.

## Estructura

```
.
├─ manage.py
├─ inventory_manager/
│  ├─ settings.py
│  ├─ urls.py
│  ├─ wsgi.py
│  └─ asgi.py
├─ orders/
│  ├─ apps.py
│  ├─ db.py
│  ├─ urls.py
│  ├─ views.py
│  ├─ serializers.py
│  └─ validators.py
├─ scripts/
│  └─ latency_test.py
├─ requirements.txt
├─ .env.example
└─ README.md
```

## Ejecución Local (Desarrollo)

### Requisitos

- Python 3.10+
- MongoDB local (o contenedor Docker)
- Opcional: `git`, `virtualenv`

### Pasos

```bash
git clone https://github.com/mcastiblancoa/gestor-pedidos.git inventario
cd inventario
python -m venv .venv
".venv\\Scripts\\activate"  # En PowerShell Windows; en Linux/macOS: source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Crear archivo `.env` (puedes copiar `.env.example`):

```env
SECRET_KEY=dev-secret
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
DB_HOST=localhost
DB_PORT=27017
DB_USER=
DB_PASS=
DB_NAME=inventory_db
```

Levantar MongoDB si usas Docker:

```bash
docker run -d --name mongo -p 27017:27017 mongo:7
```

Migraciones mínimas (auth/sessions):

```bash
python manage.py migrate
```

Iniciar servidor:

```bash
python manage.py runserver 0.0.0.0:8000
```

Probar Swagger: http://localhost:8000/docs/

Crear pedido ejemplo:

```bash
curl -X POST http://localhost:8000/orders/ \
  -H "Content-Type: application/json" \
  -d '{"producto_id":"SKU-123","cantidad":2,"vendedor_id":"S-01","estado":"pendiente"}'
```

Respuesta incluirá `id` para usar en PATCH:

```bash
curl -X PATCH http://localhost:8000/orders/<UUID>/status/ \
  -H "Content-Type: application/json" \
  -d '{"estado":"enviado"}'
```

_UUID es el ID del pedido_

Script de latencia local:

```bash
python scripts/latency_test.py --base-url http://localhost:8000 --order-id <UUID> --runs 50 --concurrency 1
```

_UUID es el ID del pedido_

# Despliegue simple en AWS (EC2)

Arquitectura mínima: 2 instancias en la misma VPC/subred privada.

- EC2-Django: corre la API con `runserver` (modo sencillo para pruebas / demo).
- EC2-Mongo: base de datos MongoDB.

## Security Groups

- SG-Django:

  - Inbound: 22/tcp (SSH) desde tu IP
  - Inbound: 8000/tcp (HTTP de desarrollo) desde tu IP o IPs permitidas (opcionalmente amplio si es demo).
  - Outbound: permitir todo (o al menos hacia la VPC)

- SG-Mongo:
  - Inbound: 27017/tcp SOLO desde SG-Django (referencia por security group) o la IP privada de EC2-Django.
  - Sin acceso público.
  - Outbound: permitir todo.

## Crear instancias

- AMI: Ubuntu 22.04 LTS (sugerido) / Amazon Linux 2.
- Tipo: `t3.micro` (pruebas).
- Par de llaves SSH (pem).

## Configurar EC2-Mongo (Ubuntu)

```bash
sudo apt update
sudo apt install -y wget gnupg
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
```

Restringir `bindIp` (opcional, refuerza SG):

```bash
sudo sed -i "s/^  bindIp:.*/  bindIp: 127.0.0.1,<EC2_MONGO_PRIVATE_IP>/" /etc/mongod.conf
sudo systemctl restart mongod
```

Crear usuario aplicación (opcional):

```bash
mongosh <<'EOF'
use inventory_db
db.createUser({user:'appuser', pwd:'AppStr0ng#Pass', roles:[{role:'readWrite', db:'inventory_db'}]})
EOF
```

Anota IP privada de Mongo (ej: `10.0.1.23`).

## Configurar EC2-Django (Ubuntu)

1. Dependencias base:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

2. Clonar repositorio:

```bash
git clone https://github.com/mcastiblancoa/gestor-pedidos.git app
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Crear `.env`:

```bash
cat > .env <<'ENV'
SECRET_KEY=prod-secret
DEBUG=true
ALLOWED_HOSTS=localhost,EC2_PUBLIC_IP
DB_HOST=10.0.1.23
DB_PORT=27017
DB_USER=appuser
DB_PASS=AppStr0ng#Pass
DB_NAME=inventory_db
ENV
```

4. Migraciones (solo para apps contrib de Django):

```bash
python manage.py migrate
```

5. Ejecutar servidor de desarrollo (expuesto en 0.0.0.0:8000):

```bash
python manage.py runserver 0.0.0.0:8000
```

Mantén la sesión SSH abierta; para uso prolongado puedes usar `tmux` o `screen`.

## Pruebas de latencia en EC2

En EC2-Django (misma VPC, baja latencia a Mongo):

```bash
source .venv/bin/activate
python scripts/latency_test.py --base-url http://127.0.0.1:8000 --order-id <UUID> --runs 200 --concurrency 1
```

_UUID es el ID del pedido_

Opcional: Desde tu máquina local contra la IP pública para medir impacto de red.
