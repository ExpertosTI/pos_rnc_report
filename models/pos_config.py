from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    report_sale_summary = fields.Boolean('Resumen de Ventas (Reporte-Z)')
