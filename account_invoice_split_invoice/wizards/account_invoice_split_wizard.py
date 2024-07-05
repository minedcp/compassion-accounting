##############################################################################
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class SplitInvoiceWizard(models.TransientModel):
    """Wizard for selecting invoice lines to be moved
    onto a new invoice."""

    _name = "account.invoice.split.wizard"
    _description = "Split Invoice Wizard"

    move_id = fields.Many2one(
        "account.move", default=lambda self: self._get_invoice(), readonly=False
    )

    invoice_line_ids = fields.Many2many(
        "account.move.line",
        "account_invoice_line_2_splitwizard",
        "account_invoice_split_wizard_id",
        "account_invoice_line_id",
        string="Invoice lines",
        readonly=False,
    )

    line_ids = fields.Many2many(
        "account.move.line",
        string="Journal Items",
        compute="_compute_line_ids",
        readonly=False,
    )

    @api.model
    def _get_invoice(self):
        return self.env.context.get("active_id")

    @api.depends('invoice_line_ids')
    def _compute_line_ids(self):
        for wizard in self:
            if wizard.invoice_line_ids:
                move_ids = wizard.invoice_line_ids.mapped('move_id').ids
                # Fetch all lines for the invoices, including the receivable line
                all_lines = self.env['account.move.line'].search([('move_id', 'in', move_ids)])
                # Filter to only include lines related to the selected invoice lines and the receivable line
                relevant_lines = all_lines.filtered(lambda l: l.id in wizard.invoice_line_ids.ids or l.account_id.internal_type == 'receivable')
                wizard.line_ids = relevant_lines

    def split_invoice(self):
        self.ensure_one()
        invoice = False

        if self.invoice_line_ids:
            old_invoice = self.invoice_line_ids[0].move_id
            if old_invoice.state in ("draft", "posted"):
                invoice = self._copy_invoice(old_invoice)
                was_open = old_invoice.state == "posted"
                if was_open:
                    old_invoice.button_draft()
                    old_invoice.env.clear()
                self.invoice_line_ids.move_id.write({"line_ids": self.line_ids})
                self.invoice_line_ids.write({"move_id": invoice.id})
                if was_open:
                    old_invoice.action_post()
                    invoice.action_post()
        return invoice

    def _copy_invoice(self, old_invoice):
        # Create new invoice
        new_invoice = old_invoice.copy(
            default={"invoice_date": old_invoice.invoice_date}
        )
        new_invoice.line_ids.unlink()
        new_invoice.invoice_line_ids.unlink()
        return new_invoice
