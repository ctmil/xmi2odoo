Manual del Usuario
==================

Introducción
------------

XMI2OERP es un generador de módulos para OpenERP utilizando la descripción
detallada en un archivo XMI.


Los archivos XMI_ tiene como objetivo el intercambio de diagramas descriptivos
de modelos de software. En este caso lo usamos para tomar la descripción
UML de objetos para construir la estructura básica de los módulos que ahí se
describen.

Lo que no logra hacer es insertar código correspondiente a la lógica del problema,
ni describir cosas que estén fuera del diagrama de clases. En otras palabras,
apenas se limita a construir la estructura básica del módulo, la descripción de la
clase y las vistas.

La estructura básica de un módulo construida con el XMI2OERP es la siguientes:

1. [directorio del módulo, un módulo por Paquete UML]

   1. __init__.py
   2. __openerp__.py
   3. README
   4. [Nombre del Módulo]_menuitem.xml
   5. [archivo de clase, una clase por Clase UML]
   6. [archivo de vista, una vista por Clase UML]
   7. report

       1. __init__.py
       2. [archivo de clase, una clase por Clase UML]
       3. [archivo de vista, una vista por Clase UML]

   8. wizard
       1. __init__.py
       2. [archivo de clase, una clase por Clase UML]
       3. [archivo de vista, una vista por Clase UML]

Aunque hasta el momento solo hemos probado archivos XMI generados por ArgoUML_,
se espera poder procesar cualquier archivo generado por otras aplicaciones.
Para generar un módulo básico, solo de prueba, se puede utilizar los arhivos
disponibles en el directorio test/demo del paquete python.

Recomiendo el siguiente tutorial_ para empezar a entender que es UML. 
Aunque no viene mal leer una referencia rápida en tutorial_ibm_ y
una descripción más robusta en tutorial_omg_.

En las próximas secciones se detallarán las entidades incorporadas en el 
XMI base para el diseño de entidades compatibles con OpenERP: 
./xmi2odoo/data/OpenObjectStadardElements.xmi

.. _XMI: http://es.wikipedia.org/wiki/XML_Metadata_Interchange 
.. _ArgoUML: http://argouml.tigris.org/
.. _tutorial: http://www.cragsystems.co.uk/uml_tutorial/
.. _tutorial_ibm: http://www.ibm.com/developerworks/rational/library/769.html
.. _tutorial_omg: http://www.omg.org/gettingstarted/what_is_uml.htm

Tipos
-----

        * binary: Conjunto de datos binarios como imágenes o archivos.
        * Boolean: Dos valores posibles, 0/1, Verdadero/Falso, Negro/Blanco.
        * Char: Cadena de caracteres.
        * Date: Fecha.
        * Datetime: Fecha y hora.
        * Float: Número real.
        * Integer: Número entero.
        * Text: Texto largo.
        * Time: hora.

Estereotipos
------------

de Paquetes
~~~~~~~~~~~

        * external

de Clases
~~~~~~~~~

        * form
        * tree

de Atributos
~~~~~~~~~~~~

        * readonly
        * select
        * store
        * tranlatable
        * method
        * required

de Operaciones
~~~~~~~~~~~~~~

de Relaciones
~~~~~~~~~~~~~

de Casos de Uso
~~~~~~~~~~~~~~~

        * menu

de Actor
~~~~~~~~

        * group

Etiquetas o tags
----------------

de Paquetes
~~~~~~~~~~~

        * label
        * author
        * documentation
        * menu_parent
        * menu_sequence
        * version

de Clases
~~~~~~~~~

        * label
        * documentation
        * menu_parent
        * menu_sequence

de Atributos
~~~~~~~~~~~~

        * label
        * documentation
        * fnct
        * fnct_inv
        * fnct_search
        * default
        * size
        * context
        * help

de Operaciones
~~~~~~~~~~~~~~

        * label
        * documentation

de Relaciones
~~~~~~~~~~~~~

        * label
        * documentation
        * related_to

Clases
------

El concepto de Clase en UML es muy parecido a las clases de OpenObject_, el motor de relaciones de objetos (ORM_) de OpenERP_.
En principio contiene los mismos principios de miembros atributos o variables, miembros operaciones o funciones, y herencia.

Las diferencias escenciales es que el objeto de OpenERP tiene más atributos y propiedades como clase por lo que hay que utilizar etiquetas o tags para indicarle como configurar.

.. _OpenObject: http://doc.openerp.com/v6.0/developer/2_5_Objects_Fields_Methods/methods.html
.. _ORM: http://es.wikipedia.org/wiki/Mapeo_objeto-relacional
.. _OpenERP: http://doc.openerp.com
