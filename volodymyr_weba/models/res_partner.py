from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    date_of_birth = fields.Date(string="Date of birth")
    edrpou = fields.Char(string="ЄДРПОУ")