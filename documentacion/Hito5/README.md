# 🧩 HITO 5: Despliegue de la aplicación en un IaaS o PaaS

[![GitHub Actions](https://github.com/pablovegood/Alejandria/actions/workflows/ci.yml/badge.svg)](https://github.com/pablovegood/Alejandria/actions)

## Fly.io como PaaS elegido

En un primer momento pensé en desplegar mi aplicación en **Render**, ya que la había utilizado para desplegar SyllaBUG, una herramienta para personal bibliotecario de control de versiones de bibliografías de las diferentes asignaturas impartidas en la UGR y que se puede consultar en el siguiente enlace: https://syllabug.onrender.com/.

Pero Render plantea algunos inconvenientes, siendo el más notable que duerme para su plan gratuito los servidores tras un periodo de inactividad. No quería esto para mi aplicación por lo que esta opción fue descartada casi inmediatamente.

También pensé en opciones como **Google Cloud Run**, **AWS App Runner** y **Azure Container Apps**, pero las descarté porque no quería depender de macrotecnológicas americanas para desplegar mi aplicación.

Finalmente, y aunque la opción elegida es también una empresa americana, esta es mucho más pequeña que las opciones previamente mencionadas.

Fly es una opción que encaja muy bien con Docker y contenedores en general. Además, Fly expone de por sí ciertos logs y facilita la integración de métricas, lo cual era necesario para este Hito. Por otro lado, Fly hace uso de multi-regio para baja latencia, es decir sigue una filosofía *run apps close to users*.

## Herramientas usadas para desplegar Alejandría en Fly.io

Para llevar a cabo el despliegue, se ha hecho uso del fichero *fly.toml* que define y especifican la región principal (Frankfurt), el puerto interno del servicio (8000), el uso de HTTPS, auto-start/stop de instancias y los checks de salud.

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

Fly.io proporciona observabilidad integrada a nivel de plataforma para cada aplicación desplegada, accesible desde el panel de métricas. Esta observabilidad resulta especialmente adecuada para el hito porque permite monitorizar el estado del servicio sin desplegar infraestructura adicional (por ejemplo, un Prometheus propio) y ofrece información en tiempo real sobre el funcionamiento del despliegue desde el primer momento. Al estar incluida en el PaaS, reduce la complejidad del sistema y evita puntos extra de fallo, manteniendo el despliegue más sencillo y reproducible.

<img width="844" height="542" alt="image" src="https://github.com/user-attachments/assets/3c9f579a-b132-47f8-9054-9b9deeff7bad" />

En concreto, el panel de Fly.io permite visualizar métricas operativas clave como los códigos de estado HTTP (para detectar rápidamente incrementos de errores 4xx/5xx), los tiempos de respuesta agregados mediante percentiles (p50, p95 y p99), el tráfico de red (data transfer de entrada y salida), y métricas de la máquina/instancia como el load average, el uso de memoria y el swap. Estas métricas permiten detectar anomalías típicas de producción (picos de latencia, saturación de CPU, crecimiento de memoria, caídas de disponibilidad o patrones anormales de tráfico) y justifican que el despliegue se está monitorizando de forma continua y objetiva.

El uso de la observabilidad integrada también aporta valor en la parte de prestaciones, ya que durante pruebas de carga o smoke tests se puede observar si el p95/p99 de latencia se degrada, si aparecen errores HTTP bajo concurrencia o si la instancia muestra señales de estrés (aumento del load o consumo de memoria). De esta manera, la evaluación de rendimiento no se limita a la app responde, sino que se puede respaldar con evidencias cuantitativas registradas por la plataforma.

<img width="856" height="885" alt="image" src="https://github.com/user-attachments/assets/402f91a2-a944-4d52-b562-34cec3f1deb2" />

Estas gráficas, además, se pueden abrir en Grafana.

<img width="955" height="1019" alt="image" src="https://github.com/user-attachments/assets/6fdd3870-e53e-45f3-8ba9-fb72b9536142" />

Adicionalmente, como complemento a las métricas del PaaS, la aplicación expone un endpoint /metrics en formato Prometheus y un endpoint /healthz para checks de salud. 

<img width="877" height="514" alt="image" src="https://github.com/user-attachments/assets/a34dc0d0-be8f-433b-8979-da7d6470c632" />

<img width="498" height="168" alt="image" src="https://github.com/user-attachments/assets/7e644200-c101-49fe-a09a-83b5f830c0fb" />

Esto permite disponer también de observabilidad a nivel de aplicación (por ejemplo, latencias por endpoint, número de peticiones o métricas internas del runtime), aportando mayor detalle cuando se necesita diagnóstico. En conjunto, el enfoque elegido combina una primera capa de observabilidad “lista para usar” (Fly.io) con una segunda capa opcional de métricas propias de la API, logrando una solución completa y adecuada para monitorización en tiempo real.

## Pruebas de las prestaciones de Alejandría

Para evaluar el rendimiento del despliegue se ha realizado una prueba de carga ligera (smoke test) contra el servicio publicado, con el objetivo de medir latencia y estabilidad bajo concurrencia moderada. Para ello se ha utilizado k6, una herramienta de benchmarking que permite definir escenarios reproducibles y obtener métricas como tiempo de respuesta, tasa de peticiones por segundo y porcentaje de errores. La prueba se ejecuta contra el endpoint /healthz (y/o endpoints representativos), ya que es un punto de verificación estable que permite medir el overhead del servicio y su capacidad de respuesta sin introducir variabilidad adicional.

Durante la ejecución del test se han recogido dos tipos de evidencias: (1) el resultado de k6, donde se observan los tiempos de respuesta agregados y la ausencia (o presencia) de fallos, y (2) la correlación con el panel de métricas de Fly.io, comprobando que no aparecen picos de errores HTTP y que los percentiles de latencia (p95/p99) se mantienen en valores estables. Adicionalmente, se observa el consumo de memoria y carga de la instancia para verificar que, bajo carga, el servicio no entra en saturación ni presenta crecimiento anómalo. Este enfoque permite justificar las prestaciones con datos objetivos, en lugar de basarse únicamente en una comprobación manual.

<img width="1210" height="900" alt="image" src="https://github.com/user-attachments/assets/f126ccfa-3059-4fb5-acba-c97ce23d281f" />

<img width="1206" height="469" alt="image" src="https://github.com/user-attachments/assets/8716dea3-63b4-4ca7-bb15-e849fa7b3c60" />


## ¿Dónde utilizar Alejandría?

Para poder acceder a la aplicación, basta con acceder al siguiente enlace desde su navegador de confianza: https://alejandria.fly.dev 

La aplicación permite iniciar sesión, crear un usuario, tomar libros en préstamo y leer aquellos libros que han sido tomados en préstamos, devolver los libros y escribir reseñas de cualquier libro.

<img width="1915" height="1074" alt="image" src="https://github.com/user-attachments/assets/6fc69b78-2c2e-4e0c-836c-18b6b3bfb813" />

Si se abre un libro tomado en préstamo se abre este mostrado a través de un visor que permite ponerse en modo oscuro, modificar el tamaño de la letra y la fuente de la letra.

<img width="1919" height="973" alt="image" src="https://github.com/user-attachments/assets/c05716b5-40ad-4ecb-a312-6831e5ab2667" />

Me hubiera gustado dedicarle más tiempo a pulir detalles del frontend, pero al no ser el objetivo principal de la asignatura, lo dejo planteado como trabajo futuro.
