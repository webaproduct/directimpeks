from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import io
import pandas as pd


class InvoiceImportWizard(models.TransientModel):
    _name = 'wizard.invoice.import.settings'
    _description = 'Invoice Import Wizard'

    file_data = fields.Binary(string='XLS File', required=True)
    file_name = fields.Char(string='File Name')
    internal_owner_id = fields.Many2one('res.partner', string='Product Owner', required=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type', required=True)
    
    invoice_line_ids = fields.One2many('wizard.invoice.import.line', 'wizard_id', string='Invoice Lines')
    selected_line_id = fields.Many2one('wizard.invoice.import.line', string='Selected Line')
    distribution_ids = fields.One2many('wizard.invoice.import.distribution', 'wizard_id', string='Distribution Lines')
    
    @api.onchange('selected_line_id')
    def _onchange_selected_line(self):
        """Filter distribution lines by selected invoice line product"""
        if self.selected_line_id and self.selected_line_id.product_id:
            return {
                'domain': {
                    'distribution_ids': [('product_id', '=', self.selected_line_id.product_id.id)]
                }
            }
        else:
            return {
                'domain': {
                    'distribution_ids': []
                }
            }

    def action_import_file(self):
        """Import data from XLS file using pandas"""
        self.ensure_one()
        
        if not self.file_data:
            raise UserError(_('Please select a file to import'))
        
        try:
            file_content = base64.b64decode(self.file_data)
            df = pd.read_excel(io.BytesIO(file_content))
            
            self.invoice_line_ids.unlink()
            
            lines_to_create = []
            for index, row in df.iterrows():
                barcode = str(row.get('Штрихкод', '')) if pd.notna(row.get('Штрихкод')) else ''
                recipient_code = str(row.get('Код отримувача', '')) if pd.notna(row.get('Код отримувача')) else ''
                primary_order_number = str(row.get('Номер первинного замовлення постачальнику', '')) if pd.notna(row.get('Номер первинного замовлення постачальнику')) else ''
                
                product_id = False
                if barcode:
                    product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
                    if product:
                        product_id = product.id
                
                recipient_partner_id = False
                if recipient_code:
                    partner = self.env['res.partner'].search([('ref', '=', recipient_code)], limit=1)
                    if partner:
                        recipient_partner_id = partner.id
                
                source_purchase_id = False
                if primary_order_number:
                    purchase_order = self.env['purchase.order'].search([('partner_ref', '=', primary_order_number)], limit=1)
                    if purchase_order:
                        source_purchase_id = purchase_order.id
                
                line_vals = {
                    'wizard_id': self.id,
                    'sequence': int(row.get('№ п/п', index + 1)) if pd.notna(row.get('№ п/п')) else index + 1,
                    'barcode': barcode,
                    'product_id': product_id,
                    'quantity': float(row.get('Кількість', 0)) if pd.notna(row.get('Кількість')) else 0,
                    'base_price': float(row.get('Базова тарифна Ціна', 0)) if pd.notna(row.get('Базова тарифна Ціна')) else 0,
                    'discount': float(row.get('знижка', 0)) if pd.notna(row.get('знижка')) else 0,
                    'price_with_discount': float(row.get('ціна зі знижкою', 0)) if pd.notna(row.get('ціна зі знижкою')) else 0,
                    'recipient_code': recipient_code,
                    'recipient_partner_id': recipient_partner_id,
                    'invoice_number': str(row.get('Номер інвойса', '')) if pd.notna(row.get('Номер інвойса')) else '',
                    'primary_order_number': primary_order_number,
                    'source_purchase_id': source_purchase_id,
                }
                lines_to_create.append(line_vals)
            
            for line_vals in lines_to_create:
                self.env['wizard.invoice.import.line'].create(line_vals)
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Import Invoice'),
                'res_model': 'wizard.invoice.import.settings',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
            }
            
        except Exception as e:
            raise UserError(_('Error importing file: %s') % str(e))

    def action_cancel(self):
        """Cancel wizard"""
        return {'type': 'ir.actions.act_window_close'}


class WizardInvoiceImport(models.TransientModel):
    _name = 'wizard.invoice.import.line'
    _description = 'Wizard Invoice Import Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('wizard.invoice.import.settings', string='Wizard', ondelete='cascade', required=True)
    sequence = fields.Integer(string='№ п/п', default=1)
    barcode = fields.Char(string='Barcode', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity', required=True, digits='Product Unit of Measure')
    base_price = fields.Float(string='Base Price', required=True, digits='Product Price')
    discount = fields.Float(string='Discount', digits='Product Price')
    price_with_discount = fields.Float(string='Price with Discount', required=True, digits='Product Price')
    recipient_code = fields.Char(string='Recipient Code')
    recipient_partner_id = fields.Many2one('res.partner', string='Recipient Partner')
    invoice_number = fields.Char(string='Invoice Number', required=True)
    primary_order_number = fields.Char(string='Primary Order Number', required=True)
    source_purchase_id = fields.Many2one('purchase.order', string='Source Purchase Order')
    distribution_ids = fields.One2many('wizard.invoice.import.distribution', 'invoice_line_id', string='Distribution Lines')


class WizardInvoiceImportDistribution(models.TransientModel):
    _name = 'wizard.invoice.import.distribution'
    _description = 'Wizard Invoice Import Distribution'
    _order = 'id'

    wizard_id = fields.Many2one('wizard.invoice.import.settings', string='Wizard', ondelete='cascade', required=True)
    invoice_line_id = fields.Many2one('wizard.invoice.import.line', string='Invoice Line')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure')
    quantity_purchase = fields.Float(string='Purchase Quantity', digits='Product Unit of Measure')
    quantity_result = fields.Float(string='Result Quantity', digits='Product Unit of Measure')
    recipient_partner_id = fields.Many2one('res.partner', string='Recipient Partner')
    source_purchase_id = fields.Many2one('purchase.order', string='Source Purchase Order')
    source_purchase_line_id = fields.Many2one('purchase.order.line', string='Source Purchase Line')
    demand_group_id = fields.Many2one('demand.group', string='Demand Group')
