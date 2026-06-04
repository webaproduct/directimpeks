/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";

patch(OrderWidget.prototype, {
    async _editPackLotLines(event) {
        const orderline = event.detail.orderline;
        this.env.services.pos.lots = await this.env.services.pos.getProductLots(
            orderline.product
        );
        const res = await super._editPackLotLines(...arguments);
        this.env.services.pos.lots = undefined;
        return res;
    }
});
