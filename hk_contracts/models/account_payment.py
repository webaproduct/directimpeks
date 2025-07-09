from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_contract_required = fields.Boolean(related="partner_id.is_contract_required")

    def _prepare_move_line_default_vals(
        self, write_off_line_vals=None, force_balance=None
    ):
        result = super()._prepare_move_line_default_vals(
            write_off_line_vals, force_balance
        )

        for line in result:
            account_id = line.get("account_id")
            if not account_id:
                continue
            account_id = self.env["account.account"].browse(account_id)
            if account_id.l10n_ua_track_by_contract:
                line.update({"contract_id": self.contract_id.id})
            else:
                line.update({"contract_id": False})

        return result

    @api.model
    def _get_trigger_fields_to_synchronize(self):
        result = super()._get_trigger_fields_to_synchronize()
        result += ("contract_id",)
        return result
