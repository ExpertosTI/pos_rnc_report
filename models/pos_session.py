from pytz import timezone, UTC
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, MissingError
import base64
import logging

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = "pos.session"
 

    def get_current_date(self):
        if self.env.user and self.env.user.tz:
            tz = self.env.user.tz
            tz = timezone(tz)
        else:
            tz = UTC
        if tz:
            c_time = datetime.now(tz)
            return c_time.strftime('%d/%m/%Y')
        else:
            return date.today().strftime('%d/%m/%Y')

    def get_current_time(self):
        if self.env.user and self.env.user.tz:
            tz = self.env.user.tz
            tz = timezone(tz)
        else:
            tz = UTC
        if tz:
            c_time = datetime.now(tz)
            return c_time.strftime('%I:%M %p')
        else:
            return datetime.now().strftime('%I:%M:%S %p')

    def get_cash_in_out(self):
        account_bank_statement_lines = self.env['account.bank.statement.line'].search([
            ('pos_session_id', '=', self.id)])
        cash_in_out = {}
        for absl in account_bank_statement_lines:
            if absl.amount > 0:
                cash_in_out.setdefault('cash_in', []).append({
                    'amount': absl.amount,
                    'date': absl.create_date,
                    'reason': absl.payment_ref or absl.ref or absl.name
                })
            else:
                cash_in_out.setdefault('cash_out', []).append({
                    'amount': absl.amount,
                    'date': absl.create_date,
                    'reason': absl.payment_ref or absl.ref or absl.name
                })
        return cash_in_out

    def get_payments_amount(self):
        payments_amount = []
        for payment_method in self.config_id.payment_method_ids:
            payments = self.env['pos.payment'].search([
                ('session_id', '=', self.id),
                ('payment_method_id', '=', payment_method.id)
            ])
            journal_dict = {
                'name': payment_method.name,
                'amount': 0
            }
            for payment in payments:
                amount = payment.amount
                journal_dict['amount'] += amount
            payments_amount.append(journal_dict)
        return payments_amount

    def get_total_sales(self):
        total_price = 0.0
        for order in self.order_ids:
            if order.amount_paid >= 0:
                total_price += sum([(line.qty * line.price_unit) for line in order.lines])
        return total_price

    def get_total_reversal(self):
        total_price = 0.0
        for order in self.order_ids:
            if order.amount_paid <= 0:
                total_price += order.amount_paid
        return total_price

    def get_reversal_orders_detail(self):
        reversal_orders_detail = {}
        for order in self.order_ids:
            if order.amount_paid <= 0:
                reversal_orders_detail[order.name] = []
                for line in order.lines:
                    reversal_orders_detail[order.name].append({
                        'product_id': line.product_id.display_name,
                        'qty': line.qty,
                        'price_subtotal_incl': line.price_subtotal_incl,
                    })
        return reversal_orders_detail

    def get_vat_tax(self):
        taxes_info = []
        tax_list = [tax.id for order in self.order_ids for line in
                    order.lines.filtered(lambda line: line.tax_ids_after_fiscal_position) for tax in
                    line.tax_ids_after_fiscal_position]
        tax_list = list(set(tax_list))
        for tax in self.env['account.tax'].browse(tax_list):
            total_tax = 0.00
            net_total = 0.00
            for line in self.env['pos.order.line'].search(
                    [('order_id', 'in', [order.id for order in self.order_ids])]).filtered(
                lambda line: tax in line.tax_ids_after_fiscal_position):
                total_tax += line.price_subtotal * tax.amount / 100
                net_total += line.price_subtotal
            taxes_info.append({
                'tax_name': tax.name,
                'tax_total': total_tax,
                'tax_per': tax.amount,
                'net_total': net_total,
                'gross_tax': total_tax + net_total
            })
        return taxes_info

    def get_total_tax(self):
        total_tax = 0.0
        for order in self.order_ids:
            total_tax += order.amount_tax
        return total_tax

    def get_total_discount(self):
        total_discount = 0.0
        if self.order_ids:
            for order in self.order_ids:
                total_discount += sum([((line.qty * line.price_unit) * line.discount) / 100 for line in order.lines])
                total_discount += sum([line.price_extra for line in order.lines])
        return total_discount

    def get_products_stats(self):
        """Agrega estadísticas por producto: cantidad, ventas y ganancia."""
        stats = {}
        for order in self.order_ids:
            for line in order.lines:
                product = line.product_id
                rec = stats.setdefault(product.id, {
                    'product_id': product.id,
                    'product_name': product.display_name,
                    'qty': 0.0,
                    'sales': 0.0,
                    'profit': 0.0,
                })
                rec['qty'] += line.qty
                rec['sales'] += line.price_subtotal_incl
                rec['profit'] += line.qty * (line.price_unit - product.standard_price)
        return stats

    # def get_sale_summary_by_user(self):
    #     user_summary = {}
    #     for order in self.order_ids:
    #         for line in order.lines:
    #             if line.user_id:
    #                 if not user_summary.get(line.user_id.name, None):
    #                     user_summary[line.user_id.name] = line.price_subtotal_incl
    #                 else:
    #                     user_summary[line.user_id.name] += line.price_subtotal_incl
    #             else:
    #                 if not user_summary.get(order.user_id.name, None):
    #                     user_summary[order.user_id.name] = line.price_subtotal_incl
    #                 else:
    #                     user_summary[order.user_id.name] += line.price_subtotal_incl
    #     return user_summary

    def get_total_refund(self):
        refund_total = 0.0
        if self.order_ids:
            for order in self.order_ids:
                if order.amount_total < 0:
                    refund_total += order.amount_total
        return refund_total

    def get_total_first(self):
        return sum(order.amount_total for order in self.order_ids)

    def get_gross_total(self):
        gross_total = 0.0
        if self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    gross_total += line.qty * (line.price_unit - line.product_id.standard_price)
        return gross_total

    def validate_report_password(self, password):
        """Valida la contraseña del reporte desde el frontend"""
        if not self.config_id.report_password:
            raise UserError(_('No se ha configurado una contraseña para el reporte.'))
        
        if password != self.config_id.report_password:
            raise UserError(_('Contraseña incorrecta.'))
        
        return True

    def build_sessions_report(self):
        vals = {}
        session_state = {
            'new_session': _('Nueva Sesión'),
            'opening_control': _('Control de Apertura'),
            'opened': _('En Progreso'),
            'closing_control': _('Control de Cierre'),
            'closed': _('Cerrado y Contabilizado'),
        }
        for session in self:
            session_report = {}
            session_report['name'] = session.name
            session_report['current_date'] = session.get_current_date()
            session_report['current_time'] = session.get_current_time()
            session_report['state'] = session_state[session.state]
            session_report['start_at'] = session.start_at
            session_report['stop_at'] = session.stop_at
            session_report['seller'] = session.user_id.name
            session_report['cash_register_balance_start'] = session.cash_register_balance_start
            session_report['orders_count'] = len(session.order_ids)
            session_report['sales_total'] = session.get_total_sales()
            session_report['reversal_total'] = session.get_total_reversal()
            session_report['reversal_orders_detail'] = session.get_reversal_orders_detail()
            session_report['taxes'] = session.get_vat_tax()
            session_report['taxes_total'] = session.get_total_tax()
            session_report['discounts_total'] = session.get_total_discount()
            # session_report['users_summary'] = session.get_sale_summary_by_user()
            session_report['refund_total'] = session.get_total_refund()
            session_report['gross_total'] = session.get_total_first()
            session_report['gross_profit_total'] = session.get_gross_total()
            session_report['net_gross_total'] = session.get_gross_total() - session.get_total_tax()
            session_report['closing_total'] = session.cash_register_balance_end_real
            session_report['payments_amount'] = session.get_payments_amount()
            session_report['cash_in'] = session.get_cash_in_out().get('cash_in', {})
            session_report['cash_out'] = session.get_cash_in_out().get('cash_out', {})
            # Top productos por cantidad y producto con mayor ganancia
            prod_stats = session.get_products_stats()
            top_products = sorted(prod_stats.values(), key=lambda x: x['qty'], reverse=True)[:10]
            best_profit_product = (max(prod_stats.values(), key=lambda x: x['profit']) if prod_stats else None)
            session_report['top_products'] = top_products
            session_report['best_profit_product'] = best_profit_product
            vals[session.id] = session_report
        return vals
    
    def send_z_report_email(self, send_now=True, attach_pdf=True, attach_html=True):
        """Envía el Reporte-Z por correo electrónico.
        Retorna un dict con el resultado para evitar cortar el flujo del POS.
        """
        self.ensure_one()
        _logger.info("="*80)
        _logger.info("INICIO: Envío de Reporte-Z por correo (send_now=%s, attach_pdf=%s, attach_html=%s)" % (send_now, attach_pdf, attach_html))
        _logger.debug(f"Sesión: {self.name} (ID: {self.id})")

        config = self.config_id
        _logger.debug(f"Config ID: {config.id}")
        _logger.debug(f"report_send_email: {config.report_send_email}")
        _logger.debug(f"report_email_recipients: {config.report_email_recipients}")

        if not config.report_send_email:
            _logger.warning("Envío de correo desactivado en la configuración")
            return {'ok': False, 'reason': 'disabled'}

        if not config.report_email_recipients:
            msg = _('No se han configurado destinatarios de correo electrónico.')
            _logger.error(msg)
            return {'ok': False, 'reason': 'no_recipients', 'message': msg}

        # Verificar servidor de correo saliente
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            msg = _('No hay servidor de correo saliente configurado.')
            _logger.error(msg)
            return {'ok': False, 'reason': 'no_mail_server', 'message': msg}

        # PASO 1: PDF o Fallback HTML
        pdf_base64 = None
        if attach_pdf:
            _logger.debug("→ PASO 1: Generando PDF del reporte")
            try:
                try:
                    report_action = self.env.ref('pos_rnc_report.action_report_sales_summary')
                except ValueError:
                    report_action = self.env['ir.actions.report']._get_report_from_name('pos_rnc_report.report_sales_summary')
                _logger.debug(f"  Acción de reporte: {report_action and report_action.name or 'No encontrada'}")
                if report_action:
                    pdf_content, _ = report_action._render_qweb_pdf([self.id])
                    pdf_size = len(pdf_content)
                    _logger.debug(f"  ✓ PDF generado: {pdf_size} bytes")
                    pdf_base64 = base64.b64encode(pdf_content).decode()
                    _logger.debug(f"  ✓ PDF codificado en base64")
                else:
                    _logger.warning("  Definición de reporte no instalada. Se omite PDF.")
            except Exception as e:
                _logger.error(f"  ERROR al generar PDF: {str(e)}", exc_info=True)
                _logger.warning("  Falló la generación de PDF. Se continuará sin PDF.")

        # PASO 2: Adjuntos (PDF si existe, si no HTML)
        _logger.debug("→ PASO 2: Creando adjunto(s)")
        attachment_ids = []
        try:
            if pdf_base64:
                attachment_pdf = self.env['ir.attachment'].sudo().create({
                    'name': f'Reporte_Cierre_Sesion_{self.name}.pdf',
                    'type': 'binary',
                    'datas': pdf_base64,
                    'res_model': 'pos.session',
                    'res_id': self.id,
                    'mimetype': 'application/pdf'
                })
                attachment_ids.append(attachment_pdf.id)
                _logger.debug(f"  ✓ Adjunto PDF creado: ID {attachment_pdf.id}")
            elif attach_html:
                # Construir el mismo HTML detallado que se usa en el cuerpo del correo
                d_fb = self.build_sessions_report().get(self.id, {})
                def fmt_fb(v):
                    return ('%.2f' % v) if isinstance(v, (int, float)) else (v or '')
                payments_rows_fb = ''.join([
                    f"<tr><td>{(pm or {}).get('name','')}</td><td style='text-align:right;'>{fmt_fb((pm or {}).get('amount'))}</td></tr>"
                    for pm in (d_fb.get('payments_amount') or [])
                ])
                top_products_rows_fb = ''.join([
                    f"<tr><td>{(tp or {}).get('product_name','')}</td><td style='text-align:right;'>{fmt_fb((tp or {}).get('qty'))}</td><td style='text-align:right;'>{fmt_fb((tp or {}).get('sales'))}</td></tr>"
                    for tp in (d_fb.get('top_products') or [])
                ])
                bestp_fb = d_fb.get('best_profit_product') or {}
                taxes_rows_fb = ''.join([
                    f"<tr><td>{(tx or {}).get('tax_name','')}</td><td style='text-align:right;'>{fmt_fb((tx or {}).get('tax_total'))}</td><td style='text-align:right;'>{fmt_fb((tx or {}).get('net_total'))}</td></tr>"
                    for tx in (d_fb.get('taxes') or [])
                ])
                cashin_rows_fb = ''.join([
                    f"<tr><td>{fmt_fb((ci or {}).get('date'))}</td><td style='text-align:right;'>{fmt_fb((ci or {}).get('amount'))}</td><td>{(ci or {}).get('reason','')}</td></tr>"
                    for ci in (d_fb.get('cash_in') or [])
                ])
                cashout_rows_fb = ''.join([
                    f"<tr><td>{fmt_fb((co or {}).get('date'))}</td><td style='text-align:right;'>{fmt_fb((co or {}).get('amount'))}</td><td>{(co or {}).get('reason','')}</td></tr>"
                    for co in (d_fb.get('cash_out') or [])
                ])
                reversals_html_fb = ''
                if d_fb.get('reversal_orders_detail'):
                    for order_ref, lines in (d_fb.get('reversal_orders_detail') or {}).items():
                        line_rows = ''.join([
                            f"<tr><td>{fmt_fb((ln or {}).get('qty'))}</td><td>{(ln or {}).get('product_id','')}</td><td style='text-align:right;'>{fmt_fb((ln or {}).get('price_subtotal_incl'))}</td></tr>"
                            for ln in (lines or [])
                        ])
                        reversals_html_fb += f"<h4>Reversión: {order_ref}</h4><table style='width:100%;border-collapse:collapse' border='1'><thead><tr><th>Cant.</th><th>Producto</th><th style='text-align:right;'>Subtotal</th></tr></thead><tbody>{line_rows}</tbody></table>"
                html_fb = f"""
                    <div>
                      <h2>REPORTE DE CIERRE DE SESIÓN</h2>
                      <p><b>Empresa:</b> {self.company_id.name or ''}</p>
                      <p><b>POS:</b> {self.config_id.name or ''} &nbsp; <b>Sesión:</b> {self.name}</p>
                      <p><b>Fecha:</b> {d_fb.get('current_date') or ''} &nbsp; <b>Hora:</b> {d_fb.get('current_time') or ''}</p>
                      <p><b>Estado:</b> {d_fb.get('state') or ''} &nbsp; <b>Usuario:</b> {self.user_id.name or ''}</p>
                      <p><b>Inicio:</b> {d_fb.get('start_at') or ''} &nbsp; <b>Fin:</b> {d_fb.get('stop_at') or ''}</p>
                      <hr/>
                      <h3>Resumen</h3>
                      <ul>
                        <li><b>Órdenes:</b> {d_fb.get('orders_count') or ''}</li>
                        <li><b>Ventas Totales:</b> {fmt_fb(d_fb.get('gross_total'))}</li>
                        <li><b>Impuestos:</b> {fmt_fb(d_fb.get('taxes_total'))}</li>
                        <li><b>Descuentos:</b> {fmt_fb(d_fb.get('discounts_total'))}</li>
                        <li><b>Reembolso:</b> {fmt_fb(d_fb.get('refund_total'))}</li>
                        <li><b>Ganancias:</b> {fmt_fb(d_fb.get('gross_profit_total'))}</li>
                        <li><b>Total de Cierre:</b> {fmt_fb(d_fb.get('closing_total'))}</li>
                      </ul>
                      <h3>Métodos de Pago</h3>
                      <table style='width:100%;border-collapse:collapse' border='1'>
                        <thead><tr><th>Nombre</th><th style='text-align:right;'>Monto</th></tr></thead>
                        <tbody>{payments_rows_fb or '<tr><td colspan=2>Sin datos</td></tr>'}</tbody>
                      </table>
                      <h3>Top 10 Productos Más Vendidos</h3>
                      <table style='width:100%;border-collapse:collapse' border='1'>
                        <thead><tr><th>Producto</th><th style='text-align:right;'>Cantidad</th><th style='text-align:right;'>Ventas</th></tr></thead>
                        <tbody>{top_products_rows_fb or '<tr><td colspan=3>Sin datos</td></tr>'}</tbody>
                      </table>
                      <h3>Producto con Mayores Ganancias</h3>
                      <p>
                        <b>Producto:</b> {bestp_fb.get('product_name','')} &nbsp; 
                        <b>Cantidad:</b> {fmt_fb(bestp_fb.get('qty'))} &nbsp; 
                        <b>Ganancias:</b> {fmt_fb(bestp_fb.get('profit'))}
                      </p>
                      <h3>Impuestos</h3>
                      <table style='width:100%;border-collapse:collapse' border='1'>
                        <thead><tr><th>Impuesto</th><th style='text-align:right;'>Impuesto</th><th style='text-align:right;'>Base</th></tr></thead>
                        <tbody>{taxes_rows_fb or '<tr><td colspan=3>Sin datos</td></tr>'}</tbody>
                      </table>
                      <h3>Entrada de Efectivo</h3>
                      <table style='width:100%;border-collapse:collapse' border='1'>
                        <thead><tr><th>Fecha</th><th style='text-align:right;'>Monto</th><th>Motivo</th></tr></thead>
                        <tbody>{cashin_rows_fb or '<tr><td colspan=3>Sin datos</td></tr>'}</tbody>
                      </table>
                      <h3>Salida de Efectivo</h3>
                      <table style='width:100%;border-collapse:collapse' border='1'>
                        <thead><tr><th>Fecha</th><th style='text-align:right;'>Monto</th><th>Motivo</th></tr></thead>
                        <tbody>{cashout_rows_fb or '<tr><td colspan=3>Sin datos</td></tr>'}</tbody>
                      </table>
                      {reversals_html_fb}
                    </div>
                """
                html_base64 = base64.b64encode(html_fb.encode('utf-8')).decode()
                attachment_html = self.env['ir.attachment'].sudo().create({
                    'name': f'Reporte_Cierre_Sesion_{self.name}.html',
                    'type': 'binary',
                    'datas': html_base64,
                    'res_model': 'pos.session',
                    'res_id': self.id,
                    'mimetype': 'text/html'
                })
                attachment_ids.append(attachment_html.id)
                _logger.debug(f"  ✓ Adjunto HTML creado (fallback): ID {attachment_html.id}")
        except Exception as e:
            _logger.error(f"  ERROR al crear adjunto: {str(e)}", exc_info=True)
            return {'ok': False, 'reason': 'attachment_error', 'message': str(e)}

        # PASO 3: Correo (asunto y cuerpo detallado)
        _logger.debug("→ PASO 3: Preparando correo")
        email_to = config.report_email_recipients.replace(' ', '')
        email_from = self.env.company.email or self.user_id.email or self.env['ir.mail_server']._get_default_from_address()
        _logger.debug(f"  Destinatarios: {email_to}")
        _logger.debug(f"  Remitente (email_from): {email_from}")

        # Construir HTML con todos los datos de la sesión
        d = self.build_sessions_report().get(self.id, {})
        def fmt(v):
            return ('%.2f' % v) if isinstance(v, (int, float)) else (v or '')
        payments_rows = ''.join([
            f"<tr><td>{(pm or {}).get('name','')}</td><td style='text-align:right;'>{fmt((pm or {}).get('amount'))}</td></tr>"
            for pm in (d.get('payments_amount') or [])
        ])
        top_products_rows = ''.join([
            f"<tr><td>{(tp or {}).get('product_name','')}</td><td style='text-align:right;'>{fmt((tp or {}).get('qty'))}</td><td style='text-align:right;'>{fmt((tp or {}).get('sales'))}</td></tr>"
            for tp in (d.get('top_products') or [])
        ])
        bestp = d.get('best_profit_product') or {}
        taxes_rows = ''.join([
            f"<tr><td>{(tx or {}).get('tax_name','')}</td><td style='text-align:right;'>{fmt((tx or {}).get('tax_total'))}</td><td style='text-align:right;'>{fmt((tx or {}).get('net_total'))}</td></tr>"
            for tx in (d.get('taxes') or [])
        ])
        cashin_rows = ''.join([
            f"<tr><td>{fmt((ci or {}).get('date'))}</td><td style='text-align:right;'>{fmt((ci or {}).get('amount'))}</td><td>{(ci or {}).get('reason','')}</td></tr>"
            for ci in (d.get('cash_in') or [])
        ])
        cashout_rows = ''.join([
            f"<tr><td>{fmt((co or {}).get('date'))}</td><td style='text-align:right;'>{fmt((co or {}).get('amount'))}</td><td>{(co or {}).get('reason','')}</td></tr>"
            for co in (d.get('cash_out') or [])
        ])
        reversals_html = ''
        if d.get('reversal_orders_detail'):
            for order_ref, lines in (d.get('reversal_orders_detail') or {}).items():
                line_rows = ''.join([
                    f"<tr><td>{fmt((ln or {}).get('qty'))}</td><td>{(ln or {}).get('product_id','')}</td><td style='text-align:right;'>{fmt((ln or {}).get('price_subtotal_incl'))}</td></tr>"
                    for ln in (lines or [])
                ])
                reversals_html += f"<h4>Reversión: {order_ref}</h4><table style='width:100%;border-collapse:collapse' border='1'><thead><tr><th>Cant.</th><th>Producto</th><th style='text-align:right;'>Subtotal</th></tr></thead><tbody>{line_rows}</tbody></table>"

        html_body = f"""
            <div>
              <h2>REPORTE DE CIERRE DE SESIÓN</h2>
              <p><b>Empresa:</b> {self.company_id.name or ''}</p>
              <p><b>POS:</b> {self.config_id.name or ''} &nbsp; <b>Sesión:</b> {self.name}</p>
              <p><b>Fecha:</b> {d.get('current_date') or ''} &nbsp; <b>Hora:</b> {d.get('current_time') or ''}</p>
              <p><b>Estado:</b> {d.get('state') or ''} &nbsp; <b>Usuario:</b> {self.user_id.name or ''}</p>
              <p><b>Inicio:</b> {d.get('start_at') or ''} &nbsp; <b>Fin:</b> {d.get('stop_at') or ''}</p>
              <hr/>
              <h3>Resumen</h3>
              <ul>
                <li><b>Órdenes:</b> {d.get('orders_count') or ''}</li>
                <li><b>Ventas Totales:</b> {fmt(d.get('gross_total'))}</li>
                <li><b>Impuestos:</b> {fmt(d.get('taxes_total'))}</li>
                <li><b>Descuentos:</b> {fmt(d.get('discounts_total'))}</li>
                <li><b>Reembolso:</b> {fmt(d.get('refund_total'))}</li>
                <li><b>Ganancias:</b> {fmt(d.get('gross_profit_total'))}</li>
                <li><b>Total de Cierre:</b> {fmt(d.get('closing_total'))}</li>
              </ul>
              <h3>Métodos de Pago</h3>
              <table style='width:100%;border-collapse:collapse' border='1'>
                <thead><tr><th>Nombre</th><th style='text-align:right;'>Monto</th></tr></thead>
                <tbody>{payments_rows or '<tr><td colspan=2>Sin datos</td></tr>'}</tbody>
              </table>
              <h3>Top 10 Productos Más Vendidos</h3>
              <table style='width:100%;border-collapse:collapse' border='1'>
                <thead><tr><th>Producto</th><th style='text-align:right;'>Cantidad</th><th style='text-align:right;'>Ventas</th></tr></thead>
                <tbody>{top_products_rows or '<tr><td colspan=3>Sin datos</td></tr>'}</tbody>
              </table>
              <h3>Producto con Mayores Ganancias</h3>
              <p>
                <b>Producto:</b> {bestp.get('product_name','')} &nbsp; 
                <b>Cantidad:</b> {fmt(bestp.get('qty'))} &nbsp; 
                <b>Ganancias:</b> {fmt(bestp.get('profit'))}
              </p>
              <h3>Impuestos</h3>
              <table style='width:100%;border-collapse:collapse' border='1'>
                <thead><tr><th>Impuesto</th><th style='text-align:right;'>Impuesto</th><th style='text-align:right;'>Base</th></tr></thead>
                <tbody>{taxes_rows or '<tr><td colspan=3>Sin datos</td></tr>'}</tbody>
              </table>
              <h3>Entrada de Efectivo</h3>
              <table style='width:100%;border-collapse:collapse' border='1'>
                <thead><tr><th>Fecha</th><th style='text-align:right;'>Monto</th><th>Motivo</th></tr></thead>
                <tbody>{cashin_rows or '<tr><td colspan=3>Sin datos</td></tr>'}</tbody>
              </table>
              <h3>Salida de Efectivo</h3>
              <table style='width:100%;border-collapse:collapse' border='1'>
                <thead><tr><th>Fecha</th><th style='text-align:right;'>Monto</th><th>Motivo</th></tr></thead>
                <tbody>{cashout_rows or '<tr><td colspan=3>Sin datos</td></tr>'}</tbody>
              </table>
              {reversals_html}
            </div>
        """

        try:
            mail_values = {
                'subject': f'Reporte de Cierre de Sesión - {self.name}',
                'body_html': html_body,
                'email_to': email_to,
                'email_from': email_from,
                'reply_to': email_from,
                'auto_delete': True,
                'attachment_ids': [(6, 0, attachment_ids)]
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            _logger.debug(f"  ✓ Correo creado: ID {mail.id}")
        except Exception as e:
            _logger.error(f"  ERROR al crear correo: {str(e)}", exc_info=True)
            return {'ok': False, 'reason': 'mail_create_error', 'message': str(e)}

        # PASO 4: Envío o Encolado
        if not send_now:
            _logger.debug("→ PASO 4: Encolando correo para envío asíncrono por el cron")
            _logger.debug("  ✓ Correo creado en cola (mail.mail). No se envía sincrónicamente")
            _logger.info("FIN: Proceso completado (correo encolado)")
            _logger.info("="*80)
            return {'ok': True, 'mail_id': mail.id, 'state': 'outgoing', 'queued': True}
        _logger.info("→ PASO 4: Enviando correo")
        try:
            mail.sudo().send()
            _logger.info("  ✓ Correo enviado exitosamente")
            state = 'sent'
            try:
                existing = mail.exists()
                if existing:
                    state = existing.state
            except Exception:
                pass
            _logger.debug(f"  Estado del correo: {state}")
            _logger.info("FIN: Proceso completado exitosamente")
            _logger.info("="*80)
            return {'ok': True, 'mail_id': mail.id, 'state': state}
        except Exception as e:
            msg = str(e)
            if isinstance(e, MissingError) or 'record does not exist' in msg or 'registro no existe' in msg:
                _logger.warning("  mail.mail fue eliminado durante el envío; se asume envío exitoso")
                _logger.info("="*80)
                return {'ok': True, 'mail_id': mail.id, 'state': 'sent'}
            _logger.error(f"  ERROR al enviar correo: {msg}", exc_info=True)
            _logger.info("="*80)
            return {'ok': False, 'reason': 'send_error', 'message': msg}
 

    def action_pos_session_close(self, balancing_account=None, amount_to_balance=0.0, bank_payment_method_diffs=None):
        res = super().action_pos_session_close(balancing_account, amount_to_balance, bank_payment_method_diffs)
        for session in self:
            try:
                result = session.send_z_report_email(send_now=True, attach_pdf=False, attach_html=True)
                _logger.debug(f"Resultado del envío de correo al cerrar sesión {session.name}: {result}")
            except Exception as e:
                _logger.error(f"Error al enviar correo de cierre para la sesión {session.name}: {e}", exc_info=True)
        return res
