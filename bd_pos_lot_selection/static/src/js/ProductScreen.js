/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Product } from "@point_of_sale/app/store/models";

patch(Product.prototype, {
    async getAddProductOptions() {
        if (["serial", "lot"].includes(this.tracking)) {
            this.env.services.pos.lots = await this.env.services.pos.getProductLots(this);
        }
        const res = await super.getAddProductOptions(...arguments);
        this.env.services.pos.lots = undefined;
        return res;
    }
});
