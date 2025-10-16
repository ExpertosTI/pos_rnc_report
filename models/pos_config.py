from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    report_sale_summary = fields.Boolean('Resumen de Ventas (Reporte-Z)')
    report_password = fields.Char('Contraseña del Reporte', help="Contraseña requerida para acceder al Reporte-Z")
    report_send_email = fields.Boolean('Enviar Reporte por Correo', help="Enviar automáticamente el Reporte-Z por correo electrónico")
    report_email_recipients = fields.Char('Destinatarios', help="Correos electrónicos separados por comas")

    def _get_pos_ui_config(self):
        """Enviar configuración al frontend del POS"""
        config = super()._get_pos_ui_config()
        config.update({
            'report_password': self.report_password,
            'report_sale_summary': self.report_sale_summary,
            'report_send_email': self.report_send_email,
            'report_email_recipients': self.report_email_recipients,
        })
        return config
