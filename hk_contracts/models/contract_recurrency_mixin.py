from odoo import fields, models


class ContractRecurrencyMixin(models.AbstractModel):
    _inherit = "contract.recurrency.mixin"

    is_not_recurrence = fields.Boolean(
        default=True,
    )
