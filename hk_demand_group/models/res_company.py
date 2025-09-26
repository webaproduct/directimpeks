from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    intercompany_account_id = fields.Many2one(
        'account.account',
        string='Intercompany Settlement Account',
        check_company=True,
        domain="[('deprecated', '=', False)]"
    )
    
    intercompany_price_list_id = fields.Many2one(
        'product.pricelist',
        string='Intercompany Settlement Pricelist',
        check_company=True
    )
