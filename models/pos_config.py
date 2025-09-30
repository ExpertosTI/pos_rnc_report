from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    report_sale_summary = fields.Boolean('Resumen de Ventas (Reporte-Z)')
    report_password = fields.Char('Contraseña del Reporte', help="Contraseña requerida para acceder al Reporte-Z")

    def _get_pos_ui_config(self):
        """Enviar configuración al frontend del POS"""
        config = super()._get_pos_ui_config()
        config.update({
            'report_password': self.report_password,
            'report_sale_summary': self.report_sale_summary,
        })
        return config
