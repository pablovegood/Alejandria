# HITO  2: Integración continua

## Elección y configuración de un Gestor de Tareas

Para el gestor de tareas he utilizado **invoke**, que es una biblioteca de Python que te permite ejecutar una serie de tareas definidas en un archivo **tasks.py** similar a como sucedería con un Makefile, pero en lugar de hacer uso de *make* como comando en el terminal para ejecutar las diferentes instrucciones, se hace uso de *invoke + nombre_de_la_tarea*. Pero, ¿por qué **Invoke**?

Básicamente, el lenguaje de programación que estoy usando para **Alejandría** es Python con el IDE PyCharm, por lo que me parecía bastante lógico e intuitivo hacer uso de una biblioteca pensada para el caso de Python, en lugar de hacer uso por ejemplo de un Makefile. Además, en primero de carrera ya usé y programé Makefiles, por lo que me apetecía atreverme con algo que no hubiera usado antes, para así enriquecerme aún más durante este proyecto.

Por otro lado, a diferencia de otros gestores como **GNU Make** que dependen del entorno Unix y por tanto no presenta portabilidad multiplataforma de forma nativa en Windows o macOS. Si bien había otros gestores de tareas como Tox, Nox o Doit tienen una mayor complejidad, lo cual podría no ser del todo ideal en un proyecto de complejidad media-baja como viene siendo esta biblioteca virtual.

Finalmente, y sin querer adelantarme mucho, ni hacer demasiados *spoilers*, este gestor de tareas es totalmente compatible con el sitema de Integración Continua (CI) elegido para el caso: GitHub Actions.

## Elección y uso de la biblioteca de aserciones

## Elección y uso del marco de pruebas

## Elección y funcionamiento del sistema de Integración Continua (CI)

## Funcionalidad implementada y que será testeada de Alejandría
