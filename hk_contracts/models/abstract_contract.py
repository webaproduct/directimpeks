from odoo import api, models


class ContractAbstractContract(models.AbstractModel):
    _inherit = "contract.abstract.contract"

    @api.model
    def _default_generation_type(self):
        return "sale"
