from odoo import fields, models, api


class DepartmentId(models.Model):
    _name = "department.id"
    _rec_name = "name" 
    
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Department", 
        required=True, 
    )
    active = fields.Boolean(
        string="Active", 
        default=True
    )
