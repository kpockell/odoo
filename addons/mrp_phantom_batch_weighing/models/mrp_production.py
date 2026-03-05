# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    batch_weighing_ids = fields.One2many(
        'mrp.batch.weighing',
        'production_id',
        string='Batch Weighings',
        help='Records of all batch weighings for this manufacturing order'
    )
    batch_weighing_count = fields.Integer(
        string='Weighing Count',
        compute='_compute_batch_weighing_count'
    )

    @api.depends('batch_weighing_ids')
    def _compute_batch_weighing_count(self):
        for production in self:
            production.batch_weighing_count = len(production.batch_weighing_ids)

    def action_open_batch_weighing(self):
        """Open the batch weighing wizard"""
        self.ensure_one()
        return {
            'name': _('Batch Weighing'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.batch.weighing.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
            },
        }

    def action_view_batch_weighings(self):
        """View all batch weighings for this MO"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('mrp_phantom_batch_weighing.action_mrp_batch_weighing')
        action['domain'] = [('production_id', '=', self.id)]
        action['context'] = {
            'default_production_id': self.id,
        }
        return action
