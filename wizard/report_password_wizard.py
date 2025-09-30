from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReportPasswordWizard(models.TransientModel):
    _name = 'report.password.wizard'
    _description = 'Wizard para Contraseña del Reporte'

    password = fields.Char('Contraseña', required=True)
    session_id = fields.Many2one('pos.session', 'Sesión POS', required=True)

    def validate_password_and_print(self):
        """Valida la contraseña y genera el reporte si es correcta"""
        self.ensure_one()
        
        # Obtener la contraseña configurada
        config_password = self.session_id.config_id.report_password
        
        if not config_password:
            raise UserError(_('No se ha configurado una contraseña para el reporte en la configuración del POS.'))
        
        if self.password != config_password:
            raise UserError(_('Contraseña incorrecta. Acceso denegado.'))
        
        # Si la contraseña es correcta, generar el reporte
        results = self.session_id.build_sessions_report()
        
        return {
            'type': 'ir.actions.report',
            'report_name': 'pos_rnc_report.report_sales_summary',
            'report_type': 'qweb-html',
            'data': results[self.session_id.id],
            'context': {'session_id': self.session_id.id}
        }
