/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { _t } from "@web/core/l10n/translation";
import { renderToElement } from "@web/core/utils/render";

patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },

    // Función para mostrar modal de contraseña oculta
    showPasswordModal() {
        return new Promise((resolve) => {
            // Crear modal HTML
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.5); z-index: 9999; display: flex; 
                align-items: center; justify-content: center;
            `;
            
            modal.innerHTML = `
                <div style="background: white; padding: 20px; border-radius: 8px; min-width: 300px; text-align: center;">
                    <h4 style="margin-bottom: 15px; color: #333;">🔒 Contraseña del Reporte</h4>
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
            
            // Enfocar el input
            passwordInput.focus();
            
            // Manejar eventos
            const cleanup = () => {
                document.body.removeChild(modal);
            };
            
            cancelBtn.onclick = () => {
                cleanup();
                resolve(null);
            };
            
            confirmBtn.onclick = () => {
                const password = passwordInput.value;
                cleanup();
                resolve(password);
            };
            
            // Enter para confirmar
            passwordInput.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    const password = passwordInput.value;
                    cleanup();
                    resolve(password);
                }
            };
            
            // Escape para cancelar
            modal.onkeydown = (e) => {
                if (e.key === 'Escape') {
                    cleanup();
                    resolve(null);
                }
            };
        });
    },

    async printZReport() {
        // Verificar si hay contraseña configurada
        if (this.pos.config.report_password) {
            // Solicitar contraseña con modal personalizado
            const password = await this.showPasswordModal();
            
            if (!password) {
                return; // Usuario canceló
            }

            try {
                // Validar contraseña en el backend
                await this.pos.data.call("pos.session", "validate_report_password", [this.pos.session.id, password]);
            } catch (error) {
                alert("Error: " + (error.message || "Contraseña incorrecta"));
                return;
            }
        }

        // Si no hay contraseña o la validación fue exitosa, generar el reporte
        let results = await this.pos.data.call("pos.session", "build_sessions_report", [[this.pos.session.id]]);
        const report = renderToElement("pos_rnc_report.ReportSalesSummary", Object.assign({}, {
            pos: this.pos,
            data: results[this.pos.session.id]
        }));
        return await this.pos.printer.printHtml(report, {webPrintFallback: true});
    }

});

