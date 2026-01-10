# 🧩 HITO 5: Despliegue de la aplicación en un IaaS o PaaS

[![GitHub Actions](https://github.com/pablovegood/Alejandria/actions/workflows/ci.yml/badge.svg)](https://github.com/pablovegood/Alejandria/actions)

## Fly.io como PaaS elegido

En un primer momento pensé en desplegar mi aplicación en **Render**, ya que la había utilizado para desplegar SyllaBUG, una herramienta para personal bibliotecario de control de versiones de bibliografías de las diferentes asignaturas impartidas en la UGR y que se puede consultar en el siguiente enlace: https://syllabug.onrender.com/.

Pero Render plantea algunos inconvenientes, siendo el más notable que duerme para su plan gratuito los servidores tras un periodo de inactividad. No quería esto para mi aplicación por lo que esta opción fue descartada casi inmediatamente.

También pensé en opciones como **Google Cloud Run**, **AWS App Runner** y **Azure Container Apps**, pero las descarté porque no quería depender de macrotecnológicas americanas para desplegar mi aplicación.

Finalmente, y aunque la opción elegida es también una empresa americana, esta es mucho más pequeña que las opciones previamente mencionadas.

Fly es una opción que encaja muy bien con Docker y contenedores en general. Además, Fly expone de por sí ciertos logs y facilita la integración de métricas, lo cual era necesario para este Hito. Por otro lado, Fly hace uso de multi-regio para baja latencia, es decir sigue una filosofía *run apps close to users*.

## Herramientas usadas para desplegar Alejandría en Fly.io

Para llevar a cabo el despliegue, se ha hecho uso del fichero *fly.toml* que define y especifican la región principal (Francia), el puerto interno del servicio (8000), el uso de HTTPS, auto-start/stop de instancias y los checks de salud.

La base técnica del despliegue es la containerización de la aplicación. A nivel local, el proyecto ya está estructurado en múltiples servicios Docker mediante compose.yaml (servicios data, api y web) y un volumen compartido (alejandria_texts) para persistencia/compartición de ficheros. 
En producción (Fly.io), el despliegue actual se centra en el servicio API y se construye desde el Dockerfile indicado en fly.toml (Dockerfile.api). 

Además, se utiliza la CLI de Fly (flyctl) para operar la plataforma (crear app, crear volúmenes, desplegar, etc.).

<img width="1355" height="910" alt="image" src="https://github.com/user-attachments/assets/baf1bee3-0288-44af-957a-a0f6a7846c1c" />

## Configuración para el despliegue desde GitHub

El despliegue automático se realiza con GitHub Actions mediante el workflow deploy-fly.yml. Este workflow se ejecuta en cada push a la rama Hito5.

El job hace lo siguiente:
  - Checkout del repositorio.
  - Instalación de la CLI (flyctl) usando la acción oficial.
  - Ejecución del despliegue con flyctl deploy --remote-only.

La opción --remote-only implica que el build del contenedor se hace en infraestructura remota (builders de Fly), evitando depender de Docker local en el runner y simplificando el pipeline. El workflow usa un secreto FLY_API_TOKEN (configurado en GitHub Secrets) para autenticar el despliegue sin exponer credenciales en el repositorio. 

Como medida de robustez, el workflow incorpora concurrency para evitar despliegues simultáneos: si se hacen varios pushes seguidos, se cancela el despliegue anterior y se deja solo el último (reduce estados intermedios y fallos por colisiones).

## Configuración de las herramientas de observabilidad implementadas para monotorización

## Pruebas de las prestaciones de la aplicación desplegada en el PaaS

## ¿Dónde utilizar Alejandría?

Para poder acceder a la aplicación, basta con acceder al siguiente enlace desde su navegador de confianza: https://alejandria.fly.dev 
