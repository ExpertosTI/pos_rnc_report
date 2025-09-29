/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";

patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },

    async printZReport() {
        await this.pos.printZReport()
    }

});

