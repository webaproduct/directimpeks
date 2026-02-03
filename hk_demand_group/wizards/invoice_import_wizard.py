from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
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
    purchase_line_ids = fields.One2many('wizard.invoice.import.purchase', 'wizard_id', string='Purchase Lines')
    
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
            
            self._load_purchase_lines()
            
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

    def _load_purchase_lines(self):
        """Load expected purchase order lines with remaining quantities"""
        self.ensure_one()
        
        self.purchase_line_ids.unlink()
        
        products = self.invoice_line_ids.mapped('product_id')
        purchases = self.invoice_line_ids.mapped('source_purchase_id')
        if not products:
            return
        
        domain = [
            ('product_id', 'in', products.ids),
            ('order_id', 'in', purchases.ids),
            ('order_id.state', 'in', ['purchase']),
        ]
        
        po_lines = self.env['purchase.order.line'].search(domain, order='order_id, demand_group_id, id')
        
        purchase_lines_to_create = []
        for po_line in po_lines:
            qty_to_receive = po_line.product_qty - po_line.qty_received
            
            if qty_to_receive <= 0:
                continue
            
            purchase_lines_to_create.append({
                'wizard_id': self.id,
                'partner_id': po_line.order_id.partner_id.id,
                'purchase_id': po_line.order_id.id,
                'purchase_line_id': po_line.id,
                'product_id': po_line.product_id.id,
                'demand_group_id': po_line.demand_group_id.id if po_line.demand_group_id else False,
                'recipient_partner_id': po_line.demand_group_id.partner_id.id if po_line.demand_group_id else False,
                'quantity_plan': qty_to_receive,
            })
        
        for line_vals in purchase_lines_to_create:
            self.env['wizard.invoice.import.purchase'].create(line_vals)

    def action_distribute(self):
        """Distribute invoice lines to purchase order lines using FIFO method"""
        self.ensure_one()
        
        if not self.invoice_line_ids:
            raise UserError(_('No invoice lines to distribute'))
        
        self.distribution_ids.unlink()
        
        for invoice_line in self.invoice_line_ids.sorted(key=lambda l: l.sequence):
            if not invoice_line.product_id:
                continue
            
            remaining_qty = invoice_line.quantity
            
            domain = [
                ('wizard_id', '=', self.id),
                ('product_id', '=', invoice_line.product_id.id),
            ]

            if invoice_line.source_purchase_id:
                domain.append(('purchase_id', '=', invoice_line.source_purchase_id.id))

            if invoice_line.recipient_partner_id:
                domain.append(('recipient_partner_id', '=', invoice_line.recipient_partner_id.id))

            purchase_lines = self.purchase_line_ids.filtered_domain(domain).sorted(key=lambda p: (p.demand_group_id.id or 0, p.id))
            
            for purchase_line in purchase_lines:
                available_qty = purchase_line.quantity_plan - purchase_line.quantity_distributed
                
                if available_qty <= 0 or remaining_qty <= 0:
                    self.env['wizard.invoice.import.distribution'].create({
                        'wizard_id': self.id,
                        'invoice_line_id': invoice_line.id,
                        'product_id': invoice_line.product_id.id,
                        'quantity': 0,
                        'quantity_purchase': purchase_line.quantity_plan,
                        # 'quantity_result': 0,
                        'recipient_partner_id': purchase_line.recipient_partner_id.id if purchase_line.recipient_partner_id else False,
                        'source_purchase_id': purchase_line.purchase_id.id if purchase_line.purchase_id else False,
                        'source_purchase_line_id': purchase_line.purchase_line_id.id if purchase_line.purchase_line_id else False,
                        'demand_group_id': purchase_line.demand_group_id.id if purchase_line.demand_group_id else False,
                    })
                    continue
                
                allocated_qty = min(remaining_qty, available_qty)
                
                self.env['wizard.invoice.import.distribution'].create({
                    'wizard_id': self.id,
                    'invoice_line_id': invoice_line.id,
                    'product_id': invoice_line.product_id.id,
                    'quantity': allocated_qty,
                    'quantity_purchase': purchase_line.quantity_plan,
                    # 'quantity_result': available_qty - allocated_qty,
                    'recipient_partner_id': purchase_line.recipient_partner_id.id if purchase_line.recipient_partner_id else False,
                    'source_purchase_id': purchase_line.purchase_id.id if purchase_line.purchase_id else False,
                    'source_purchase_line_id': purchase_line.purchase_line_id.id if purchase_line.purchase_line_id else False,
                    'demand_group_id': purchase_line.demand_group_id.id if purchase_line.demand_group_id else False,
                })
                
                purchase_line.quantity_distributed += allocated_qty
                remaining_qty -= allocated_qty
            
            if remaining_qty > 0:
                self.env['wizard.invoice.import.distribution'].create({
                    'wizard_id': self.id,
                    'invoice_line_id': invoice_line.id,
                    'product_id': invoice_line.product_id.id,
                    'quantity': remaining_qty,
                    'quantity_purchase': 0,
                    # 'quantity_result': remaining_qty,
                    'recipient_partner_id': invoice_line.recipient_partner_id.id if invoice_line.recipient_partner_id else False,
                    'source_purchase_id': invoice_line.source_purchase_id.id,
                    'source_purchase_line_id': False,
                    'demand_group_id': False,
                })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Invoice'),
            'res_model': 'wizard.invoice.import.settings',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_save(self):
        """Create purchase orders based on distribution"""
        self.ensure_one()
        
        if not self.distribution_ids:
            raise UserError(_('No distribution lines to save'))
        
        purchase_orders_created = []
        
        distribution_by_supplier = {}
        for dist_line in self.distribution_ids.filtered(lambda d: d.quantity > 0 and d.source_purchase_id):
            supplier_id = dist_line.source_purchase_id.partner_id.id
            if supplier_id not in distribution_by_supplier:
                distribution_by_supplier[supplier_id] = []
            distribution_by_supplier[supplier_id].append(dist_line)
        
        for supplier_id, dist_lines in distribution_by_supplier.items():
            source_po = dist_lines[0].source_purchase_id
            
            po_vals = {
                'partner_id': supplier_id,
                'date_order': fields.Datetime.now(),
                'origin': source_po.name if source_po else '',
            }
            
            new_po = self.env['purchase.order'].create(po_vals)
            
            for dist_line in dist_lines:
                if dist_line.quantity <= 0:
                    continue
                
                po_line_vals = {
                    'order_id': new_po.id,
                    'product_id': dist_line.product_id.id,
                    'product_qty': dist_line.quantity,
                    'price_unit': dist_line.invoice_line_id.base_price,
                    'discount': dist_line.invoice_line_id.discount,
                    # 'price_with_discount': dist_line.invoice_line_id.price_with_discount,
                    'date_planned': fields.Datetime.now(),
                    'demand_group_id': dist_line.demand_group_id.id if dist_line.demand_group_id else False,
                    'source_purchase_order_id': dist_line.source_purchase_id.id if dist_line.source_purchase_id else False,
                    'source_purchase_order_line_id': dist_line.source_purchase_line_id.id if dist_line.source_purchase_line_id else False,
                }
                
                self.env['purchase.order.line'].create(po_line_vals)
            
            purchase_orders_created.append(new_po.id)
        
        if not purchase_orders_created:
            raise UserError(_('No purchase orders were created'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Created Purchase Orders'),
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', purchase_orders_created)],
            'target': 'current',
        }

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

    # @api.constrains('quantity', 'distribution_ids')
    # def _check_distribution_quantity(self):
    #     for record in self:
    #         if record.distribution_ids:
    #             total_distributed = sum(record.distribution_ids.mapped('quantity'))
    #             if abs(total_distributed - record.quantity) > 0.01:
    #                 raise ValidationError(
    #                     _('Total distributed quantity (%.2f) must equal invoice line quantity (%.2f) for line %s') %
    #                     (total_distributed, record.quantity, record.barcode)
    #                 )


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

    # @api.constrains('quantity', 'quantity_purchase')
    # def _check_quantity_limit(self):
    #     for record in self:
    #         if record.quantity_purchase > 0 and record.quantity > record.quantity_purchase:
    #             raise ValidationError(
    #                 _('Distributed quantity (%.2f) cannot exceed purchase quantity (%.2f) for product %s') %
    #                 (record.quantity, record.quantity_purchase, record.product_id.display_name)
    #             )
    #
    #         if record.invoice_line_id:
    #             record.invoice_line_id._check_distribution_quantity()


class WizardInvoiceImportPurchase(models.TransientModel):
    _name = 'wizard.invoice.import.purchase'
    _description = 'Wizard Invoice Import Purchase Lines'
    _order = 'partner_id, demand_group_id, id'

    wizard_id = fields.Many2one('wizard.invoice.import.settings', string='Wizard', ondelete='cascade', required=True)
    partner_id = fields.Many2one('res.partner', string='Supplier', required=True)
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Line')
    product_id = fields.Many2one('product.product', string='Product')
    demand_group_id = fields.Many2one('demand.group', string='Demand Group')
    recipient_partner_id = fields.Many2one('res.partner', string='Recipient Partner')
    quantity_plan = fields.Float(string='Planned Quantity', digits='Product Unit of Measure')
    quantity_distributed = fields.Float(string='Distributed Quantity', digits='Product Unit of Measure', default=0.0)
