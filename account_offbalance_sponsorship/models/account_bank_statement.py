from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountBankStatementLine(models.Model):

    _inherit = "account.bank.statement.line"

    def button_undo_reconciliation(self):
        """remove all income allocation from the payment move
        """
        return super(AccountBankStatementLine, self.with_context(bypass_offbalance_operations=True)).button_undo_reconciliation()
