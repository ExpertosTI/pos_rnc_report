# Configuración de Envío de Correo - Reporte Z

## 📋 Pasos para Activar el Envío de Correo

### 1. Acceder a la Configuración del POS
1. Ve a **Punto de Venta** → **Configuración** → **Puntos de Venta**
2. Selecciona tu punto de venta
3. Busca la sección **"Detalle del Día"**

### 2. Configurar el Envío de Correo
En la sección "Detalle del Día" encontrarás:

- ✅ **Contraseña del Reporte**: (Opcional) Contraseña para proteger el acceso al reporte
- ✅ **Enviar por Correo**: Activa esta casilla para habilitar el envío automático
- ✅ **Destinatarios**: Ingresa los correos separados por comas
  - Ejemplo: `correo1@ejemplo.com, correo2@ejemplo.com`

### 3. Guardar la Configuración
Haz clic en **Guardar** para aplicar los cambios.

### 4. Actualizar la Sesión del POS
**IMPORTANTE**: Después de cambiar la configuración:
1. Cierra la sesión actual del POS
2. Abre una nueva sesión
3. Esto cargará la nueva configuración

## 🔍 Cómo Verificar que Funciona

### En el Navegador (Consola del Desarrollador)
1. Presiona **F12** en el navegador
2. Ve a la pestaña **Console**
3. Presiona el botón **"Z Report"**
4. Deberías ver logs como estos:

```
================================================================================
🔵 INICIO: Generación de Reporte-Z desde POS
📋 Sesión: POS/2025/0001 (ID: 123)
⚙️ Configuración POS: {
    report_sale_summary: true,
    report_password: '***configurada***',
    report_send_email: true,
    report_email_recipients: 'correo@ejemplo.com'
}
🔒 Contraseña requerida - Mostrando modal...
🔍 Validando contraseña en el backend...
✅ Contraseña validada correctamente
📊 Generando reporte...
✅ Reporte generado exitosamente
📧 Verificando configuración de correo electrónico...
   - report_send_email: true
   - report_email_recipients: correo@ejemplo.com
✅ Envío de correo ACTIVADO
📬 Destinatarios: correo@ejemplo.com
🚀 Llamando al backend para enviar correo...
✅ Correo enviado exitosamente
🖨️ Imprimiendo reporte...
✅ Reporte renderizado
🔵 FIN: Proceso completado exitosamente
================================================================================
```

### En el Servidor (Log de Odoo)
Los logs del servidor aparecerán en el archivo de log de Odoo:
- **Linux**: `/var/log/odoo/odoo-server.log`
- **Consola**: Si ejecutas Odoo desde terminal

Busca líneas como:
```
================================================================================
INICIO: Envío de Reporte-Z por correo
Sesión: POS/2025/0001 (ID: 123)
Config ID: 5
report_send_email: True
report_email_recipients: correo@ejemplo.com
→ PASO 1: Generando PDF del reporte
  ✓ PDF generado: 45678 bytes
→ PASO 2: Creando adjunto
  ✓ Adjunto creado: ID 456
→ PASO 3: Preparando correo
  Destinatarios: correo@ejemplo.com
→ PASO 4: Enviando correo
  ✓ Correo enviado exitosamente
  Estado del correo: sent
FIN: Proceso completado exitosamente
================================================================================
```

## ⚠️ Problemas Comunes

### No aparecen logs en la consola
- **Solución**: Recarga la página del POS (F5) después de actualizar el módulo
- Verifica que la consola esté en la pestaña "Console" y no en "Issues"

### El correo no se envía
1. **Verifica la configuración de correo de Odoo**:
   - Ve a **Ajustes** → **Técnico** → **Correo electrónico** → **Servidores de correo saliente**
   - Asegúrate de tener un servidor SMTP configurado

2. **Verifica que los campos estén configurados**:
   - `report_send_email` debe estar marcado (✓)
   - `report_email_recipients` debe tener al menos un correo válido

3. **Revisa los logs del servidor** para ver el error específico

### El campo no aparece en la configuración
- **Solución**: Actualiza el módulo desde Aplicaciones
- Si el error persiste, reinicia el servidor de Odoo

## 📧 Configuración del Servidor SMTP

Para que Odoo pueda enviar correos, necesitas configurar un servidor SMTP:

1. Ve a **Ajustes** → **Técnico** → **Correo electrónico** → **Servidores de correo saliente**
2. Crea un nuevo servidor con estos datos (ejemplo Gmail):
   - **Descripción**: Gmail
   - **Servidor SMTP**: smtp.gmail.com
   - **Puerto SMTP**: 587
   - **Seguridad de la conexión**: TLS (STARTTLS)
   - **Usuario**: tu-correo@gmail.com
   - **Contraseña**: tu-contraseña-de-aplicación
3. Haz clic en **Probar conexión** para verificar

**Nota**: Para Gmail, necesitas crear una "Contraseña de aplicación" en tu cuenta de Google.

## 🎯 Resumen Rápido

1. ✅ Configurar servidor SMTP en Odoo
2. ✅ Activar "Enviar por Correo" en la configuración del POS
3. ✅ Agregar destinatarios (correos separados por comas)
4. ✅ Guardar y cerrar/abrir sesión del POS
5. ✅ Presionar "Z Report" y verificar logs en consola (F12)
6. ✅ Verificar que el correo llegó a los destinatarios
