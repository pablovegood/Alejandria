# 🧩 HITO 3: Diseño de microservicios

## FastAPI como framework elegido para crear microservcios

En un principio pensé en utilizar Django para crear los microservicios de mi aplciación Alejandría, pero la curva de aprendizaje resultó ser algo más elevada de lo que estimé en un primer momento.Es por eso que buscando en internet, encontré este foro de Reddit donde este usuario hablaba maravillas sobre FastAPI https://www.reddit.com/r/FastAPI/comments/1bs889k/why_i_chose_fastapi_how_was_my_experience_and/
Los motivos por los que FastAPI es un framework tan querido es porque permite llevar a cabo APIs de forma rápida y efectiva al estar montada por encima de bibliotecas de Python bien diseñadas como Starlette and Pydantic. Por otro lado, he aprovechado la documentación automática generada por Swagger UI (/docs) y ReDoc (/redoc), que permite probar y validar los endpoints de cada microservicio sin necesidad de herramientas externas.

![img.png](img.png)
![img_1.png](img_1.png)

## Diseño en general de la API

He dividido la arquitectura de mi aplicación en 4 microservicios (por el momento), uno que gestiona la autenticación de usuarios dentro del directorio auth, otro que gestiona la visualización y el acceso a los metadatos de los libros dentro del directorio catalog, otro microservicio que gestiona los préstamos de los usuarios (tomar en préstamo y devolver por el momento), dentro de loan y otro microservicio que gestiona la publicación de reseñas para los libros dentro del directorio review.
La API principal (api/main.py) se encarga de montar los routers de cada microservicio dentro de una única aplicación FastAPI, manteniendo el desacoplo entre servicios pero facilitando su integración.
Dentro de cada microservicio, hay tres tipos de archivos: los schemas que definen los modelos de datos y validaciones con Pydantic, los routers, que define las rutas REST y la comunicación HTTP para hacer llamadas a los métodos y los services que implementan la lógica interna de negocio, independiente de la API.

## Uso de logs para registrar la actividad de la API

He implementado un sistema de logs dentro del archivo alejandria.log en el directorio logs que muestra información acerca de las operaciones efectuadas por la API, además de los diferentes WARNINGS y ERRORS que pudiesen aparecen. Esto es muy útil para detectar errores ya que aumenta la trazabilidad de la aplicación.

## Correcta ejecución de los tests

He diseñado nuevos tests, ya que al haber realizado cambios a nivel de arquitectura del proyecto y cambios de funcionalidad, los tests del Hito 2 ya no me servían, por lo que he desarrollado un test_api para testear el funcionamiento de la API y y otros tests para testear la funcionalidad de los servicios de los microservicios.

## Ejecución y testeo de la aplicación

Para poder probar la versión actual de la aplicación, he implementado un humilde frontend para no depender del terminal para realizar las peticiones (aunque también se podría hacer así). Para poder verlo en nuestra máquina local basta con ejecutar server.py y acceder a la dirección IP indicada en el terminal. Esto nos llevará a la página de inicio de sesión, nos creamos un usuario si no tenemos ninguno e introducimos nuestras credenciales, entonces podremos pedir libros prestados, leerlos, devolverlos y escribir una reseña si nos apetece. Dentro del visor del libro se podrá ajustar el tamaño de la letra, 