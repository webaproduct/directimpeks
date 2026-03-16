from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    date_planned = fields.Date(string='Дата планової поставки')
