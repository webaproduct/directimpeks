from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    
    department_id = fields.Many2one('department.id', string="Department")
    direction_id = fields.Many2one('direction.id', string="Direction")
