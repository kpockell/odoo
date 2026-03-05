# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MrpBatchWeighing(models.Model):
    _name = 'mrp.batch.weighing'
    _description = 'Manufacturing Batch Weighing'
    _order = 'weighing_date desc, id desc'

    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        required=True,
        ondelete='cascade',
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Component Product',
        required=True,
        index=True
    )
    bom_line_id = fields.Many2one(
        'mrp.bom.line',
        string='BoM Line',
        help='Original BoM line this component comes from (may be from a phantom BoM)'
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial Number',
        help='Lot or serial number of the weighed ingredient'
    )
    batch_number = fields.Char(
        string='Batch Number',
        help='Internal batch identification number for this weighing session'
    )
    theoretical_qty = fields.Float(
        string='Theoretical Quantity',
        digits='Product Unit of Measure',
        help='Expected quantity based on BoM calculation'
    )
    actual_weight = fields.Float(
        string='Actual Weight',
        digits='Product Unit of Measure',
        required=True,
        help='Actual weighed quantity'
    )
    variance = fields.Float(
        string='Variance',
        compute='_compute_variance',
        store=True,
        digits='Product Unit of Measure',
        help='Difference between actual and theoretical quantity'
    )
    variance_percent = fields.Float(
        string='Variance %',
        compute='_compute_variance',
        store=True,
        help='Variance as percentage of theoretical quantity'
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        readonly=True
    )
    weighing_date = fields.Datetime(
        string='Weighing Date',
        default=fields.Datetime.now,
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Weighed By',
        default=lambda self: self.env.user,
        required=True
    )
    stock_move_id = fields.Many2one(
        'stock.move',
        string='Related Stock Move',
        help='Stock move for this component consumption'
    )
    notes = fields.Text(
        string='Notes',
        help='Additional notes or observations about this weighing'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='production_id.company_id',
        store=True,
        readonly=True
    )

    @api.depends('theoretical_qty', 'actual_weight')
    def _compute_variance(self):
        for record in self:
            record.variance = record.actual_weight - record.theoretical_qty
            if record.theoretical_qty != 0:
                record.variance_percent = (record.variance / record.theoretical_qty) * 100
            else:
                record.variance_percent = 0.0

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.production_id.name} - {record.product_id.display_name}"
            if record.batch_number:
                name += f" (Batch: {record.batch_number})"
            result.append((record.id, name))
        return result
