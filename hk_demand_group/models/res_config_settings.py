from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    intercompany_account_id = fields.Many2one(
        'account.account',
        string='Рахунок обліку взаєморозрахунків між своїми компаніями',
        related='company_id.intercompany_account_id',
        readonly=False,
        check_company=True,
        domain="[('deprecated', '=', False)]"
    )
    
    intercompany_price_list_id = fields.Many2one(
        'product.pricelist',
        string='Прайс-лист взаєморозрахунків між своїми компаніями',
        related='company_id.intercompany_price_list_id',
        readonly=False,
        check_company=True
    )
