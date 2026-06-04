/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { EditListPopup } from "@point_of_sale/app/store/select_lot_popup/select_lot_popup";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";

patch(EditListPopup.prototype, {
    setup() {
        super.setup();
        this.pos = usePos()
        this.popup = useService("popup")
        this.state = useState({ array: this._initialize(this.props.array) });

        if (this.props.title === _t("Lot/Serial Number(s) Required")) {
            this.props.lots = this.env.services.pos.lots;
        }
    },
});




