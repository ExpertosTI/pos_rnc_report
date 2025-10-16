from odoo import models, api, _

class ReportSalesSummary(models.AbstractModel):
    _name = 'report.pos_rnc_report.report_sales_summary'
    _description = 'Reporte Z - Detalle del Día (PDF)'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pos.session'].browse(docids)
        report_payload = {}
        for session in docs:
            # Reutilizamos la util existente para construir los datos del reporte
            built = session.build_sessions_report()
            report_payload[session.id] = built.get(session.id, {})
        # Para uso más simple en el template cuando hay 1 sesión
        single_data = report_payload[docs[0].id] if len(docs) == 1 else None
        return {
            'doc_ids': docids,
            'doc_model': 'pos.session',
            'docs': docs,
            'data_map': report_payload,
            'data': single_data,
        }
