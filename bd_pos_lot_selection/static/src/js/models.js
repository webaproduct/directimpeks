/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { EditListPopup } from "@point_of_sale/app/store/select_lot_popup/select_lot_popup";

patch(PosStore.prototype, {
    //@override
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.lot_serial_no_restrict = loadedData['lot_serial_no_restrict'];
    },


    async getProductLots(product) {
        try {
            return await this.env.services.orm.call(
                "stock.lot",
                "get_available_lots_for_pos",
                [{
                    product_id: product.id,
                    company_id: this.env.services.pos.company.id,

                }]

            );
        } catch (error) {
            return [];
        }
    },

    async getEditedPackLotLines(isAllowOnlyOneLot, packLotLinesToEdit, productName) {

        const { confirmed, payload } = await this.env.services.popup.add(EditListPopup, {
            title: _t("Lot/Serial Number(s) Required"),
            name: productName,
            isSingleItem: isAllowOnlyOneLot,
            array: packLotLinesToEdit,
        });

        if (!confirmed) {
            return;
        }
            else {

            const packLotLinesToEditList = packLotLinesToEdit.map(item => item.text);
            const payloadTextList = payload.newArray.map(item => item.text);
            if (this.env.services.pos.config.lot_serial_no_restrict) {
            if (this.env.services.pos.lots){

            const invalidLots = payload.newArray.filter(item => !this.env.services.pos.lots.includes(item.text));

             if (!payload.newArray || payload.newArray.length === 0) {
                    await this.popup.add(ErrorPopup, {
                        title: _t('Lot No. Error'),
                        body: _t('Please enter at least one Lot/Serial Number(s) is Required.')
                    });
                    return;
                }
             else if (invalidLots.length > 0) {
                    await this.popup.add(ErrorPopup, {
                        title: _t('Lot No. Error'),
                        body: _t('Some of the entered Lot/Serial Number(s) are invalid.')
                    });

                    return;
                }

            }
            else{

            this.env.services.pos.lots = await this.env.services.pos.getProductLots(this.env.services.pos.selectedOrder.selected_orderline.product);
               const invalidLots = payload.newArray.filter(item => !this.env.services.pos.lots.includes(item.text));
                if (!payload.newArray || payload.newArray.length === 0) {
                    await this.popup.add(ErrorPopup, {
                        title: _t('Lot No. Error'),
                        body: _t('Please enter at least one Lot/Serial Number(s) is Required.')
                    });
                    return;
                }
                else if (invalidLots.length > 0) {
                    await this.popup.add(ErrorPopup, {
                        title: _t('Lot No. Error'),
                        body: _t('Some of the entered Lot/Serial Number(s) are invalid.')
                    });

                    return;
                }

            }
            if ((payloadTextList) && (packLotLinesToEditList.length > 0)) {


            if (payloadTextList.length != packLotLinesToEdit.length){
             await this.popup.add(ErrorPopup, {
                                    title: _t('Lot No. Error'),
                                    body: _t('Please enter at least one Lot/Serial Number(s) is Required.')
                                });
                                return;}
                        }
            }
        }
        const modifiedPackLotLines = Object.fromEntries(
            payload.newArray.filter((item) => item.id).map((item) => [item.id, item.text])
        );

        const newPackLotLines = payload.newArray
            .filter((item) => !item.id)
            .map((item) => ({ lot_name: item.text }));


        return { modifiedPackLotLines, newPackLotLines };
    }

});
