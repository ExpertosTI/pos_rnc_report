/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { useService } from "@web/core/utils/hooks";
import { renderToElement } from "@web/core/utils/render";

patch(PosStore.prototype, {

    async printZReport() {
        let results = await this.data.call("pos.session", "build_sessions_report", [[this.session.id]]);
        const report = renderToElement("pos_rnc_report.ReportSalesSummary", Object.assign({}, {
            pos: this,
            data: results[this.session.id]
        }));
        return await this.printer.printHtml(report, {webPrintFallback: true});
    }

})