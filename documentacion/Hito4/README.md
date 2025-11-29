# 🧩 HITO 4: Composición de Servicios

[![GitHub Actions](https://github.com/pablovegood/Alejandria/actions/workflows/ci.yml/badge.svg)](https://github.com/pablovegood/Alejandria/actions)

## Estructura del clúster de contenedores

He decidido usar 3 contenedores (mínimo de la práctica), uno de ellos para almacenar exclusivamente datos, en el caso que nos atañe los archivos de tipo .txt almacenados en /data/texts, para que se use ese contenedor para la extracción de los textos que quieran leer los usuarios y que tengan en préstamo. El segundo contenedor almacenará todo el frontend y el último contenedor almacenará la parte de backend (CSS, HTML, JavaScript).

Visto de forma más clara y mostrando ya los nombres:

- **`api`**: servicio FastAPI que implementa la lógica de negocio de Alejandría  
  (autenticación, catálogo, préstamos y reseñas).
- **`web`**: servicio nginx que sirve la interfaz web estática (HTML, CSS, JS)  
  y actúa como punto de entrada para el usuario.
- **`data`**: contenedor de datos minimalista que almacena los archivos de texto (`.txt`)  
  con el contenido de los libros provenientes de Gutenberg.

## Configuración de los contenedores

### Dockerfile.api

La imagen base es python:3.12-slim ya que es una imagen oficial y mantenida, además he usado la variante slim para reducir tamaño de la imagen.

Toma una copia de requirements.txt e instala dependencias con pip. Toma todo el código alojado en el directorio /src y configura el directorio de trabajo en /app y realiza el comando de arranque **uvicorn src.api.main:app --host 0.0.0.0 --port 8000**.

La API gestiona las bases de datos SQLite (book.db, loan.db...) y accede al contenido de los libros a través del volumen montado en /app/data/texts.

### Dockerfile.web

La imagen base de este contenedor es nginx:alpine, es ideal para servir estáticos. Realiza una copia de la carpeta /web en /usr/share/nginx/html. Ajusta y modifica la configuración por defecto de nginx, haciendo uso del archivo **nginx.conf**. 

Como puerto interno tiene el 80 y hace un mapeo con el host 8000:80 y se expone en http://localhost:8080.

### Dockerfile.data

La imagen base es **busybox**, ya que es una imagen mínima, ideal para contenedores de datos. Hace una copia de todos los archivos con extensión .txt y declara el volumen **VOLUME ["/data/texts"]**. Tiene un comando final que permite mantener el contenedor activo e inspeccionar los datos. El contenedor no exponepuertos ni ejecuta lógica de negocio.

## GitHub Packages y actualización automática

He configurado un flujo de trabajo de GitHub Actions en .github/workflows/docker-images.yml para construir y publicar las imágenes de los tres servicios en GitHub Container Registry (ghcr.io). Este flujo se ejecuta con cada push a la rama main.

Lo que viene a hacer docker-images.yml es obtener el repositorio en minúsculas ya que si no se utilizaba el formato adecuado daba error. Esto se hace en la siguiente sección de código:

``` 
- name: Set image names (lowercase)
  run: |
    IMAGE_REPO_LOWER=${GITHUB_REPOSITORY,,}
    echo "IMAGE_API=${IMAGE_REPO_LOWER}-api" >> $GITHUB_ENV
    echo "IMAGE_WEB=${IMAGE_REPO_LOWER}-web" >> $GITHUB_ENV
    echo "IMAGE_DATA=${IMAGE_REPO_LOWER}-data" >> $GITHUB_ENV
```

Esto genera los siguientes nombres de imagen:

1. **`pablovegood/alejandria-api`**
2. **`pablovegood/alejandria-web`**
3. **`pablovegood/alejandria-data`**

Luego el flujo de trabajo inicia sesión en ghcr.io usando la acción oficial docker/login-action y el GITHUB-TOKEN del repositorio sin necesidad de credenciales adicionales.

```
- name: Log in to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ${{ env.REGISTRY }}         # ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

Se construyen y publican tres imagenes (una por servicio). Cada imagen es subida a GHCR con *latest* y con el SHA del commit para tener versiones inmutaables:

```
- name: Build and push API image
  uses: docker/build-push-action@v6
  with:
    context: .
    file: Dockerfile.api
    push: true
    tags: |
      ${{ env.REGISTRY }}/${{ env.IMAGE_API }}:latest
      ${{ env.REGISTRY }}/${{ env.IMAGE_API }}:${{ github.sha }}
```

Se haría lo mismo para IMAGE_WEB e IMAGE_DATA.

Gracias a este flujo, en cada push a main el sistema reconstruye y publica automáticamente las imágenes en GHCR. Esto garantiza que siempre haya versiones actualizadas de los contenedores en GitHub Packages, listas para ser consumidas desde cualquier entorno con Docker:

```
docker pull ghcr.io/pablovegood/alejandria-api:latest
docker pull ghcr.io/pablovegood/alejandria-web:latest
docker pull ghcr.io/pablovegood/alejandria-data:latest
```

## Fichero de composición (compose.yaml)

Este fichero, describe el clúster de contenedores necesario para ejecutar Alejandría de forma orquestada. Define tres servicios principales previamente descritos.

```
services:
  data:
    build:
      context: .
      dockerfile: Dockerfile.data
    container_name: alejandria-data
    volumes:
      - alejandria_texts:/texts

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: alejandria-api
    depends_on:
      - data
    environment:
      TEXTS_PATH: /texts
    volumes:
      - alejandria_texts:/texts
    ports:
      - "8000:8000"   # expone la API en http://localhost:8000

  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    container_name: alejandria-web
    depends_on:
      - api
    ports:
      - "8080:80"     # expone el frontend en http://localhost:8080

volumes:
  alejandria_texts:
```

Se encarga de separar responsabilidades (la web solo muestra los servicios estáticos, data encapsula el montaje y la preparación de los textos...). 

El volumen **alejandria_texts** permite que data y api compartan datos sin acoplarse a rutas del host.

**depends_on** garantiza que api no arranque antes de que data esté creado, y que web arranque después de api. Esto simplifica el arranque del clúster y evita errores de conexión iniciales.

También asigna puertos sin conflictos, La API se expone en el host como 8000:8000, lo que permite a los tests y a los clientes acceder a http://localhost:8000/openapi.json y al catálogo. 

Por otro lado, el servicio web se expone en el host como 8080:80. De esta forma, no se produce conflicto de puertos en el host (me dio error antes: Bind for 0.0.0.0:8000 failed: port is already allocated) y sigue siendo accesible vía http://localhost:8080. 

Dentro de la red de Docker, web sigue pudiendo llamar a api por el nombre del servicio (http://api:8000), sin depender de los puertos externos.

Esta configuración hace que el clúster sea coherente, reproducible y portable, y además está alineada con el test de integración que valida el correcto funcionamiento del despliegue.

## Test de validación del clúster de contenedores

Para asegurar que el clúster de contenedores funciona realmente como se espera (y no solo que la aplicación arranca “a mano”), se ha implementado un test de integración en tests/test_compose_cluster.py que valida el despliegue con Docker Compose.

El test comprueba que el comando docker compose up -d --build es capaz de construir las imágenes y levantar todo el clúster definido en compose.yaml (servicios data, api, web, red y volúmenes). También comprueba que el servicio api está realmente accesible desde el host en http://localhost:8000/openapi.json, lo que implica a grandes rasgos que la imagen se ha construido correctamente. Además, indica que Uvicorn/FastAPI arrancan sin errores dentro del contenedor, que el mapeo de puertos 8000:8000 está bien configurado, que la ruta /catalog/search está operativa y devuelve una respuesta JSON con la clave results.
Finalemente, se comprueba que el clúster queda limpio al final del test (docker compose down -v), evitando interferencias con otros tests o ejecuciones posteriores.

Este test se integra en la pipeline de integración continua definida en ci.yml. Aunque, antes de ejecutar los tests libera espacio en disco antes de ejecutarlos ya que me estaba dando errores por perdida de espacio en disco, así me aseguraba que solo se usaran los recursos necesarios y GitHub Actions pudiese ejecutar con éxito los test.
