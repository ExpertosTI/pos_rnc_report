from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class ReportPasswordWizard(models.TransientModel):
    _name = 'report.password.wizard'
    _description = 'Wizard para Contraseña del Reporte'

    password = fields.Char('Contraseña', required=True)
    session_id = fields.Many2one('pos.session', 'Sesión POS', required=True)

    def validate_password_and_print(self):
        """Valida la contraseña y genera el reporte si es correcta"""
        self.ensure_one()
        _logger.info("="*80)
        _logger.info("INICIO: Validación de contraseña para Reporte-Z")
        _logger.info(f"Sesión: {self.session_id.name} (ID: {self.session_id.id})")
        
        # Obtener la contraseña configurada
        config_password = self.session_id.config_id.report_password
        _logger.info(f"Contraseña configurada: {'Sí' if config_password else 'No'}")
        
        if not config_password:
            _logger.warning("ERROR: No hay contraseña configurada")
            raise UserError(_('No se ha configurado una contraseña para el reporte en la configuración del POS.'))
        
        if self.password != config_password:
            _logger.warning("ERROR: Contraseña incorrecta")
            raise UserError(_('Contraseña incorrecta. Acceso denegado.'))
        
        _logger.info("✓ Contraseña validada correctamente")
        
        # Si la contraseña es correcta, generar el reporte
        _logger.info("Generando reporte...")
        # Si la contraseña es correcta, generar el reporte y devolver acción PDF
        results = self.session_id.build_sessions_report()

        # Enviar correo si está configurado
        if self.session_id.config_id.report_send_email:
            _logger.info("Envío de correo ACTIVADO - Iniciando proceso...")
            self._send_report_email()
        else:
            _logger.info("Envío de correo DESACTIVADO - Saltando envío")

        _logger.info("FIN: Proceso completado")
        _logger.info("="*80)

        # Retornar acción de reporte PDF estándar con fallback
        try:
            action = self.env.ref('pos_rnc_report.action_report_sales_summary')
        except ValueError:
            action = self.env['ir.actions.report']._get_report_from_name('pos_rnc_report.report_sales_summary')
        if not action:
            _logger.warning("Definición de reporte no instalada; se cierra el wizard sin imprimir.")
            return {'type': 'ir.actions.act_window_close'}
        return action.report_action(self.session_id)
    
    def _send_report_email(self):
        """Genera el PDF del reporte y lo envía por correo electrónico"""
        self.ensure_one()
        _logger.info("  → PASO 1: Verificando configuración de correo")
        
        config = self.session_id.config_id
        _logger.info(f"     Config ID: {config.id}")
        _logger.info(f"     report_send_email: {config.report_send_email}")
        _logger.info(f"     report_email_recipients: {config.report_email_recipients}")
        
        if not config.report_email_recipients:
            _logger.error("     ERROR: No hay destinatarios configurados")
            raise UserError(_('No se han configurado destinatarios de correo electrónico.'))
        
        _logger.info("  → PASO 2: Generando PDF del reporte")
        try:
            # Generar el PDF del reporte usando la acción registrada
            try:
                action = self.env.ref('pos_rnc_report.action_report_sales_summary')
            except ValueError:
                action = self.env['ir.actions.report']._get_report_from_name('pos_rnc_report.report_sales_summary')
            pdf_content, _ = action._render_qweb_pdf([self.session_id.id])
            pdf_size = len(pdf_content)
            _logger.info(f"     ✓ PDF generado: {pdf_size} bytes")
            pdf_base64 = base64.b64encode(pdf_content).decode()
            _logger.info(f"     ✓ PDF codificado en base64")
        except Exception as e:
            _logger.error(f"     ERROR al generar PDF: {str(e)}")
            raise
        
        _logger.info("  → PASO 3: Creando adjunto")
        try:
            attachment = self.env['ir.attachment'].sudo().create({
                'name': f'Reporte_Z_{self.session_id.name}.pdf',
                'type': 'binary',
                'datas': pdf_base64,
                'res_model': 'pos.session',
                'res_id': self.session_id.id,
                'mimetype': 'application/pdf'
            })
            _logger.info(f"     ✓ Adjunto creado: ID {attachment.id}, Nombre: {attachment.name}")
        except Exception as e:
            _logger.error(f"     ERROR al crear adjunto: {str(e)}")
            raise
        
        _logger.info("  → PASO 4: Preparando destinatarios")
        email_to = config.report_email_recipients.replace(' ', '')
        _logger.info(f"     Destinatarios: {email_to}")
        
        _logger.info("  → PASO 5: Creando correo electrónico")
        try:
            email_from = self.env.company.email or self.session_id.user_id.email or self.env['ir.mail_server']._get_default_from_address()
            mail_values = {
                'subject': f'Reporte de Cierre de Sesión - {self.session_id.name}',
                'body_html': f'''<p>Estimado/a,</p>
                    <p>Adjunto encontrará el <strong>Reporte de Cierre de Sesión</strong> de la sesión <strong>{self.session_id.name}</strong>.</p>
                    <p><strong>Fecha:</strong> {self.session_id.get_current_date()}</p>
                    <p><strong>Hora:</strong> {self.session_id.get_current_time()}</p>
                    <p><strong>Usuario:</strong> {self.session_id.user_id.name}</p>
                    <br/>
                    <p>Saludos cordiales.</p>''',
                'email_to': email_to,
                'email_from': email_from,
                'reply_to': email_from,
                'auto_delete': False,
                'attachment_ids': [(6, 0, [attachment.id])]
            }
            _logger.info(f"     Valores del correo: {mail_values.keys()}")
            
            mail = self.env['mail.mail'].sudo().create(mail_values)
            _logger.info(f"     ✓ Correo creado: ID {mail.id}")
        except Exception as e:
            _logger.error(f"     ERROR al crear correo: {str(e)}")
            raise
        
        _logger.info("  → PASO 6: Enviando correo")
        try:
            mail.send()
            _logger.info(f"     ✓ Correo enviado exitosamente")
            try:
                existing = mail.exists()
                if existing:
                    _logger.info(f"     Estado del correo: {existing.state}")
            except Exception:
                pass
        except Exception as e:
            msg = str(e)
            if 'record does not exist' in msg or 'registro no existe' in msg:
                _logger.warning("     mail.mail eliminado durante envío; se asume envío exitoso")
                return
            _logger.error(f"     ERROR al enviar correo: {msg}")
            raise
