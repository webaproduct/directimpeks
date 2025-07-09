from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    def get_account_type_assets(self):
        return [
            "asset_current",
            "asset_receivable",
            "liability_non_current",
            "liability_current",
            "liability_payable",
        ]

    l10n_ua_track_by_contract = fields.Boolean(string="Track by contract")
