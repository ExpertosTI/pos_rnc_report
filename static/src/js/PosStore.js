/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { renderToElement } from "@web/core/utils/render";

patch(PosStore.prototype, {

    async printZReport() {
        // Validación de contraseña
        if (this.config.report_password) {
            const password = await this._showPasswordModal();
            if (!password) {
                return;
            }
            try {
                await this.data.call("pos.session", "validate_report_password", [[this.session.id], password]);
            } catch (error) {
                alert("Error: " + (error.message || "Contraseña incorrecta"));
                return;
            }
        }

        // Generación de datos del reporte
        let results = await this.data.call("pos.session", "build_sessions_report", [[this.session.id]]);

        // Envío de correo
        if (this.config.report_send_email) {
            if (!this.config.report_email_recipients) {
                alert("Advertencia: El envío de correo está activado pero no hay destinatarios configurados.");
            } else {
                try {
                    const emailResult = await this.data.call("pos.session", "send_z_report_email", [[this.session.id]]);
                    if (emailResult && emailResult.ok) {
                    } else {
                        const reason = emailResult && emailResult.reason ? emailResult.reason : 'unknown';
                        const message = (emailResult && emailResult.message ? String(emailResult.message) : '');
                        const msgLower = message.toLowerCase();
                        const isMissingRecord = reason === 'send_error' && (
                            msgLower.includes('record does not exist') ||
                            msgLower.includes('registro no existe') ||
                            msgLower.includes('se eliminó')
                        );
                        if (isMissingRecord) {
                        } else {
                            alert("Advertencia: El reporte se generó pero hubo un problema al enviar el correo (" + reason + ")\n" + message);
                        }
                    }
                } catch (error) {
                    alert("Advertencia: El reporte se generó pero hubo un error al enviar el correo: " + (error.message || 'Error desconocido'));
                }
            }
        }

        // Impresión
        const report = renderToElement("pos_rnc_report.ReportSalesSummary", Object.assign({}, {
            pos: this,
            data: results[this.session.id]
        }));
        return await this.printer.printHtml(report, {webPrintFallback: true});
    },

    async _showPasswordModal() {
        return await new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.5); z-index: 9999; display: flex;
                align-items: center; justify-content: center;
            `;
            modal.innerHTML = `
                <div style="background: white; padding: 20px; border-radius: 8px; min-width: 300px; text-align: center;">
                    <h4 style="margin-bottom: 15px; color: #333;"> Contraseña del Reporte</h4>
                    <p style="margin-bottom: 15px; color: #666;">Ingrese la contraseña para acceder al Reporte-Z:</p>
                    <input type="password" id="passwordInput" placeholder="Contraseña..." 
                           style="width: 100%; padding: 8px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px;">
                    <div>
                        <button id="cancelBtn" style="padding: 8px 16px; margin-right: 10px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">Cancelar</button>
                        <button id="confirmBtn" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Confirmar</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            const passwordInput = modal.querySelector('#passwordInput');
            const cancelBtn = modal.querySelector('#cancelBtn');
            const confirmBtn = modal.querySelector('#confirmBtn');
            passwordInput.focus();
            const cleanup = () => { document.body.removeChild(modal); };
            cancelBtn.onclick = () => { cleanup(); resolve(null); };
            confirmBtn.onclick = () => { const password = passwordInput.value; cleanup(); resolve(password); };
            passwordInput.onkeydown = (e) => { if (e.key === 'Enter') { const password = passwordInput.value; cleanup(); resolve(password); } };
            modal.onkeydown = (e) => { if (e.key === 'Escape') { cleanup(); resolve(null); } };
        });
    }

})