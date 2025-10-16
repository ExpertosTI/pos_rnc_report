=======================
Detalle del Día TPV
=======================

Módulo para generar reportes detallados del día en el Punto de Venta con protección por contraseña.

Características
===============

* **Reporte-Z**: Genera un resumen completo de las ventas del día
* **Protección por contraseña**: Acceso restringido a los reportes mediante contraseña configurable
* **Interfaz intuitiva**: Popup de autenticación integrado en el POS
* **Configuración flexible**: Contraseña configurable por punto de venta

Configuración
=============

1. **Activar el módulo**:
   - Ir a Aplicaciones > Buscar "Detalle del Día TPV"
   - Instalar el módulo

2. **Configurar el Punto de Venta**:
   - Ir a Punto de Venta > Configuración > Puntos de Venta
   - Seleccionar el punto de venta deseado
   - Activar "Resumen de Ventas (Reporte-Z)"
   - **Opcional**: Establecer una contraseña en el campo "Contraseña del Reporte"

Uso
===

**Sin contraseña configurada**:
- El botón "Z Report" genera el reporte directamente

**Con contraseña configurada**:
- Al hacer clic en "Z Report", aparece un popup solicitando la contraseña
- Ingrese la contraseña correcta para generar el reporte
- Si la contraseña es incorrecta, se muestra un mensaje de error

Seguridad
=========

* La contraseña se almacena en texto plano en la configuración del POS
* Solo usuarios con permisos de POS pueden acceder a la configuración
* La validación se realiza en el backend para mayor seguridad

Soporte Técnico
===============

Desarrollado por: Adderly Marte
Empresa: renace.tech
Licencia: OPL-1

Para soporte técnico, contactar a través de https://renace.tech
