from odoo import fields, models, api


class DirectionId(models.Model):
    _name = "direction.id"
    _rec_name = "name" 
    
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Direction", 
        required=True, 
    )
    active = fields.Boolean(
        string="Active", 
        default=True
    )
