# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class MrpBatchWeighingWizard(models.TransientModel):
    _name = 'mrp.batch.weighing.wizard'
    _description = 'Batch Weighing Wizard'

    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        required=True,
        readonly=True
    )
    weighing_line_ids = fields.One2many(
        'mrp.batch.weighing.wizard.line',
        'wizard_id',
        string='Components to Weigh'
    )
    show_all_components = fields.Boolean(
        string='Show All Components',
        default=False,
        help='Show all BoM components, including those already weighed'
    )
    only_phantom_components = fields.Boolean(
        string='Only Phantom BoM Ingredients',
        default=True,
        help='Show only ingredients from phantom BoMs (excludes packaging materials)'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default production_id from context and populate lines"""
        res = super().default_get(fields_list)
        if self._context.get('active_model') == 'mrp.production' and self._context.get('active_id'):
            res['production_id'] = self._context['active_id']
            # Populate weighing lines (default: only phantom components, show unweighed only)
            res['weighing_line_ids'] = self._prepare_weighing_lines(
                self._context['active_id'], 
                show_all_components=False,
                only_phantom_components=True
            )
        return res

    @api.onchange('show_all_components', 'only_phantom_components')
    def _onchange_filters(self):
        """Repopulate lines when filters change (but preserve entered weights)"""
        if self.production_id:
            # Save current weights before repopulating
            current_weights = {}
            for line in self.weighing_line_ids:
                if line.product_id and line.actual_weight > 0:
                    current_weights[line.product_id.id] = {
                        'actual_weight': line.actual_weight,
                        'batch_number': line.batch_number,
                        'lot_id': line.lot_id.id if line.lot_id else False,
                        'notes': line.notes,
                    }
            
            # Repopulate lines
            self.weighing_line_ids = self._prepare_weighing_lines(
                self.production_id.id, 
                self.show_all_components,
                self.only_phantom_components
            )
            
            # Restore saved weights
            for line in self.weighing_line_ids:
                if line.product_id and line.product_id.id in current_weights:
                    saved = current_weights[line.product_id.id]
                    line.actual_weight = saved['actual_weight']
                    line.batch_number = saved['batch_number']
                    line.lot_id = saved['lot_id']
                    line.notes = saved['notes']

    def _prepare_weighing_lines(self, production_id, show_all_components, only_phantom_components=True):
        """Prepare line values from MO's To Consume components (stock moves)"""
        if not production_id:
            return [Command.clear()]

        lines = [Command.clear()]
        production = self.env['mrp.production'].browse(production_id)

        # Get all raw material moves (To Consume)
        raw_moves = production.move_raw_ids.filtered(lambda m: m.state not in ['cancel', 'done'])
        
        # Filter to only phantom BoM components if requested
        if only_phantom_components:
            raw_moves = raw_moves.filtered(lambda m: self._is_from_phantom_bom(m, production))

        # Get existing weighings grouped by product
        existing_weighings = self.env['mrp.batch.weighing'].read_group(
            [('production_id', '=', production_id)],
            ['product_id', 'actual_weight:sum'],
            ['product_id']
        )
        weighed_amounts = {item['product_id'][0]: item['actual_weight'] for item in existing_weighings}

        for move in raw_moves:
            # Skip service products
            if move.product_id.type == 'service':
                continue

            # Calculate remaining quantity
            to_consume = move.product_uom_qty
            already_weighed = weighed_amounts.get(move.product_id.id, 0.0)
            remaining = to_consume - already_weighed

            # Skip if fully weighed (unless show_all_components is True)
            if not show_all_components and remaining <= 0:
                continue

            lines.append(Command.create({
                'product_id': move.product_id.id,
                'stock_move_id': move.id,
                'to_consume_qty': to_consume,
                'already_weighed': already_weighed,
            }))

        return lines

    def _is_from_phantom_bom(self, move, production):
        """Check if a stock move originated from a phantom BoM component"""
        if not move.bom_line_id:
            return False
        
        # Check if this component's BoM line belongs to a phantom BoM
        bom_line = move.bom_line_id
        
        # If the bom_line's parent BoM is different from the main production BoM,
        # and it's a phantom type, then this component came from phantom explosion
        if bom_line.bom_id != production.bom_id:
            # This is from a sub-BoM, check if any parent is phantom
            parent_bom = bom_line.bom_id
            
            # Find if there's a line in the main BoM that references this phantom BoM
            phantom_parent = production.bom_id.bom_line_ids.filtered(
                lambda l: l.child_bom_id == parent_bom and l.child_bom_id.type == 'phantom'
            )
            return bool(phantom_parent)
        
        # Also check if this line itself has a phantom child (shouldn't appear, but safety check)
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return False  # This is the phantom product itself, not the ingredients
        
        return False

    def action_validate(self):
        """Save weighings and close. Reopen wizard to continue weighing remaining quantities."""
        self.ensure_one()

        import logging
        _logger = logging.getLogger(__name__)
        
        # Flush all pending writes to ensure we have the latest data from the form
        self.env.flush_all()
        self.invalidate_recordset()
        
        weighing_records = []
        
        # Explicitly access the lines to ensure they're loaded
        lines = self.weighing_line_ids
        _logger.info(f"Total lines in wizard: {len(lines)}")
        
        # Debug: print each line's details
        for idx, line in enumerate(lines):
            _logger.info(f"Line {idx}: product={line.product_id.name if line.product_id else 'None'}, actual_weight={line.actual_weight}")
        
        # Filter valid lines (must have product and weight > 0)
        valid_lines = lines.filtered(lambda l: l.product_id and l.actual_weight > 0)
        _logger.info(f"Valid lines to save: {len(valid_lines)}")
        
        for line in valid_lines:
            _logger.info(f"Saving line: product={line.product_id.name}, weight={line.actual_weight}")
            vals = {
                'production_id': self.production_id.id,
                'product_id': line.product_id.id,
                'lot_id': line.lot_id.id if line.lot_id else False,
                'batch_number': line.batch_number,
                'theoretical_qty': line.to_consume_qty,
                'actual_weight': line.actual_weight,
                'weighing_date': fields.Datetime.now(),
                'user_id': self.env.user.id,
                'notes': line.notes,
                'stock_move_id': line.stock_move_id.id if line.stock_move_id else False,
            }
            weighing_record = self.env['mrp.batch.weighing'].create(vals)
            weighing_records.append(weighing_record)
            _logger.info(f"Created record ID: {weighing_record.id}")

        if weighing_records:
            message = _('Recorded %d batch weighing(s)') % len(weighing_records)
            self.production_id.message_post(body=message)
            _logger.info(f"Posted message to MO, created {len(weighing_records)} records")

        return {'type': 'ir.actions.act_window_close'}


class MrpBatchWeighingWizardLine(models.TransientModel):
    _name = 'mrp.batch.weighing.wizard.line'
    _description = 'Batch Weighing Wizard Line'

    wizard_id = fields.Many2one(
        'mrp.batch.weighing.wizard',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=False  # Allow saving wizard with incomplete lines
    )
    stock_move_id = fields.Many2one(
        'stock.move',
        string='Stock Move',
        help='Related stock move for this component'
    )
    to_consume_qty = fields.Float(
        string='To Consume',
        digits='Product Unit of Measure',
        help='Total quantity to consume from the MO'
    )
    already_weighed = fields.Float(
        string='Already Weighed',
        digits='Product Unit of Measure',
        help='Sum of all previous weighings for this product'
    )
    remaining_qty = fields.Float(
        string='Remaining',
        compute='_compute_remaining',
        digits='Product Unit of Measure',
        help='Quantity still to be weighed'
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='UoM',
        related='product_id.uom_id',
        readonly=True
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial',
        help='Lot or serial number of the ingredient'
    )
    batch_number = fields.Char(
        string='Batch #',
        help='Batch identification number'
    )
    actual_weight = fields.Float(
        string='Weight',
        digits='Product Unit of Measure',
        help='Weight for this batch'
    )
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('to_consume_qty', 'already_weighed', 'actual_weight')
    def _compute_remaining(self):
        for line in self:
            line.remaining_qty = line.to_consume_qty - line.already_weighed - line.actual_weight

    @api.onchange('actual_weight')
    def _onchange_actual_weight(self):
        """Auto-save when weight is entered and user tabs out"""
        if self.actual_weight > 0 and self.product_id and self.wizard_id.production_id:
            # Create the permanent record immediately
            vals = {
                'production_id': self.wizard_id.production_id.id,
                'product_id': self.product_id.id,
                'lot_id': self.lot_id.id if self.lot_id else False,
                'batch_number': self.batch_number,
                'theoretical_qty': self.to_consume_qty,
                'actual_weight': self.actual_weight,
                'weighing_date': fields.Datetime.now(),
                'user_id': self.env.user.id,
                'notes': self.notes,
                'stock_move_id': self.stock_move_id.id if self.stock_move_id else False,
            }
            self.env['mrp.batch.weighing'].create(vals)
            
            # Update already_weighed to include this new entry
            self.already_weighed += self.actual_weight
            
            # Clear the actual_weight field so they can enter another batch
            self.actual_weight = 0.0
