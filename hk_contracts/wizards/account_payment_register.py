from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    contract_id = fields.Many2one(
        string="Contract",
        comodel_name="contract.contract",
    )

    @api.model
    def _get_line_batch_key(self, line):
        result = super()._get_line_batch_key(line)
        result.update(
            {
                "contract_id": line.contract_id.id,
            }
        )
        return result

    @api.model
    def _get_wizard_values_from_batch(self, batch_result):
        result = super()._get_wizard_values_from_batch(batch_result)
        payment_values = batch_result["payment_values"]
        result.update(
            {
                "contract_id": payment_values.get("contract_id"),
            }
        )
        return result

    def _create_payment_vals_from_batch(self, batch_result):
        result = super()._create_payment_vals_from_batch(batch_result)
        batch_values = self._get_wizard_values_from_batch(batch_result)
        result.update(
            {
                "contract_id": batch_values.get("contract_id"),
            }
        )
        return result

    def _create_payment_vals_from_wizard(self, batch_result):
        result = super()._create_payment_vals_from_wizard(batch_result)
        result.update(
            {
                "contract_id": self.contract_id.id,
            }
        )
        return result
