# 📚 Alejandría: Una biblioteca en la nube

**Alejandría** es una propuesta que busca emular el uso de una biblioteca pública convencional, 
pero adaptada al entorno digital y con algunas modificaciones.

El nombre es un homenaje a la biblioteca de Alejandría, que por desgracia se incendió y todo el 
conocimiento allí almacenado se perdió.

---

## 🌐 Descripción general

En **Alejandría**, los usuarios podrán acceder, compartir y disfrutar de obras literarias de 
**dominio público** o **autopublicadas** por autores noveles.  

### 📖 Reglas principales

En primer lugar, sólo se permitirá la subida de documentos, textos y cualquier artículo 
que sea de dominio público, es decir, **se puede subir** *Frankenstein* de *Mary Shelley*, pero 
**no** *Los Juegos del Hambre* de *Suzanne Collins*, por nombrar un par de ejemplos.

En segundo lugar, se permitirá a cualquier autor novel o  cualquier autor que así lo desee que 
suba sus obras para que otras personas puedan disfrutarlas  de forma totalmente **gratuita**, lo cual 
puede **ayudar a autores** que estén empezando en el mundo editorial a usar la biblioteca como 
**escaparate al mundo** y darse a conocer.

---

## 📑 Índice General

| Nº | Hito | Descripción | Enlace |
|----|------|--------------|---------|
| 1️⃣ | **Hito 1** | Configuración de Git, selección de licencia y planteamiento del servicio a desplegar. | [Ver Hito 1](https://github.com/pablovegood/Alejandria/tree/main/documentacion/Hito1) |
| 2️⃣ | **Hito 2** | Implementación de Integración Continua (CI) con pytest, Invoke y GitHub Actions. | [Ver Hito 2](https://github.com/pablovegood/Alejandria/tree/main/documentacion/Hito2) |
| 3️⃣ | **Hito 3** | Diseño de microservicios. | [Ver Hito 3](https://github.com/pablovegood/Alejandria/blob/Hito3/documentacion/Hito3/README.md) |
| 4️⃣ | **Hito 4** | Composición de servicios. | [Ver Hito 4](https://github.com/pablovegood/Alejandria/blob/main/documentacion/Hito4/README.md) |
| 5️⃣ | **Hito 5** | Despliegue de la aplicación en un IaaS o PaaS. | [Ver Hito 5](https://github.com/pablovegood/Alejandria/blob/Hito5/documentacion/Hito5/README.md) |

---

## 👥 Roles y funcionalidades

Alejandría cuenta con **tres tipos de roles de usuario**, cada uno con permisos y responsabilidades diferentes:

### 🧍 Usuario base (lector)
- Puede **pedir libros en préstamo**.  
- Puede **reservar libros** que no estén disponibles temporalmente.  
- Puede **solicitar la subida de un escrito** propio.  
- Puede **escribir comentarios y reseñas** visibles para toda la comunidad.  

### 📚 Bibliotecario
- Gestiona las **reservas**.  
- Puede **subir nuevos archivos** a la biblioteca.  
- Tiene acceso limitado a herramientas administrativas.

### 🧠 Administrador
- Se encarga del **mantenimiento del software**.  
- Garantiza la **escalabilidad** y el incremento de recursos del sistema.  
- Puede **actualizar los roles de los usuarios** según corresponda.  
- Atiende **incidencias técnicas** o de gestión.
  
Independientemente del rol que tengan los usuarios, todos podrán editar la mayoría 
de datos de su perfil y comunicarse entre usuarios a través de mensajes internos. 

---

## ☁️ Despliegue en la nube

Desplegar este servicio en la nube será bastante beneficioso ya que los usuarios podrán
hacer un **uso remoto** de la biblioteca y **grandes cantidades de usuarios** podrán 
hacer uso de esta sin degradar el rendimiento a la vez que se van realizando **copias
de seguridad automáticas**.

---

## 🧩 Historias de usuario

- Como María, escritora novel quiero poder dar a conocer mi novela debut a través de Alejandría.
- Como Fran, lector ávido, me gustaría poder tomar en préstamo novelas de dominio público.
- Como Juanjo, bibliotecario, me gustaría poder subir libros nuevos a la biblioteca.
- Como Charo, bibliotecaria, me gustaría poder gestionar reservas.
- Como Sonia, administradora, me gustaría poder resolver incidencias.
- Como Marina, administradora, me gustaría poder actualizar los roles de los usuarios.


---

## 🚀 Objetivo

Crear un entorno colaborativo, libre y accesible para fomentar la **lectura**, el **conocimiento abierto** y el **talento literario emergente**, aprovechando las ventajas del **cloud computing**.

---
