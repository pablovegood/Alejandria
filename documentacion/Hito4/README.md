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
