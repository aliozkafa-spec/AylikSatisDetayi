# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MonthlySupplierSalesReport(models.TransientModel):
    _name = 'monthly.supplier.sales.report'
    _description = 'Tedarikçi Aylık Satış Raporu'

    # Filters
    date_from = fields.Date(string='Başlangıç', required=True, default=lambda self: fields.Date.context_today(self).replace(day=1))
    date_to = fields.Date(string='Bitiş', required=True, default=lambda self: fields.Date.context_today(self))
    supplier_ids = fields.Many2many('res.partner', string='Tedarikçiler', domain=[('supplier_rank', '>', 0)])
    currency_id = fields.Many2one('res.currency', string='Para Birimi', required=True, default=lambda self: self.env.company.currency_id)

    # Navigation
    detail_level = fields.Selection([('main', 'Aylık Özet'), ('supplier_month', 'Tedarikçi Ay Detayı'), ('invoice', 'Fatura Detayı'), ('invoice_line', 'Fatura Satırları')], default='main')
    selected_supplier_id = fields.Many2one('res.partner', string='Seçili Tedarikçi')
    selected_month = fields.Char(string='Seçili Ay')  # YYYY-MM
    selected_invoice_id = fields.Many2one('account.move', string='Seçili Fatura')

    # Results
    main_lines = fields.One2many('monthly.supplier.sales.main.line', 'report_id', string='Özet Satırları')
    supplier_month_lines = fields.One2many('monthly.supplier.sales.supplier.month.line', 'report_id', string='Tedarikçi Ay Satırları')
    invoice_lines = fields.One2many('monthly.supplier.sales.invoice.line', 'report_id', string='Fatura Satırları')
    invoice_line_lines = fields.One2many('monthly.supplier.sales.invoice.line.line', 'report_id', string='Fatura Kalemleri')

    # Helpers
    def _get_suppliers(self):
        if self.supplier_ids:
            return self.supplier_ids
        return self.env['res.partner'].search([('supplier_rank', '>', 0), ('active', '=', True)])

    def _compute_cost_price(self, move_line):
        product = move_line.product_id
        if not product:
            return 0.0
        # Prefer standard_price as last cost; for avg cost environments, this may differ
        return product.standard_price or 0.0

    def _get_product_vendor_partner(self, product):
        if not product:
            return False
        seller = product.seller_ids[:1]
        if not seller:
            return False
        # Odoo versions differ: vendor field can be `partner_id` or `name`
        return getattr(seller, 'partner_id', False) or getattr(seller, 'name', False)

    def _convert_amount(self, amount, src_currency, company, date):
        return src_currency._convert(amount, self.currency_id, company, date)

    def _prepare_invoice_domain(self):
        return [
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ]

    # Data builders
    def _build_main_data(self):
        self.ensure_one()
        suppliers = self._get_suppliers()
        supplier_ids_filter = set(suppliers.ids)
        invoices = self.env['account.move'].search(self._prepare_invoice_domain())

        # Map supplier by month aggregates
        data = {}
        for inv in invoices:
            month_key = fields.Date.to_date(inv.invoice_date).strftime('%Y-%m')
            company_currency = inv.company_id.currency_id

            for line in inv.invoice_line_ids:
                if not line.product_id:
                    continue
                vendor_partner = self._get_product_vendor_partner(line.product_id)
                if not vendor_partner:
                    continue
                if supplier_ids_filter and vendor_partner.id not in supplier_ids_filter:
                    continue

                line_sales = line.price_subtotal or 0.0
                unit_cost = self._compute_cost_price(line)
                line_cost = unit_cost * (line.quantity or 0.0)

                sales_conv = self._convert_amount(line_sales, inv.currency_id, inv.company_id, inv.invoice_date)
                cost_conv = self._convert_amount(line_cost, company_currency, inv.company_id, inv.invoice_date)

                supplier_bucket = data.setdefault(vendor_partner.id, {})
                month_bucket = supplier_bucket.setdefault(month_key, {
                    'supplier_name': vendor_partner.name,
                    'total_sales': 0.0,
                    'total_cost': 0.0,
                })
                month_bucket['total_sales'] += abs(sales_conv)
                month_bucket['total_cost'] += abs(cost_conv)

        return data

    def generate_report(self):
        self.ensure_one()
        self.main_lines.unlink()
        self.supplier_month_lines.unlink()
        self.invoice_lines.unlink()
        self.invoice_line_lines.unlink()

        data = self._build_main_data()

        line_vals = []
        for supplier_id, months in data.items():
            for month_key, vals in months.items():
                sales = vals['total_sales']
                cost = vals['total_cost']
                margin = sales - cost
                margin_pct = (margin / sales * 100.0) if sales else 0.0
                line_vals.append({
                    'report_id': self.id,
                    'supplier_id': supplier_id,
                    'supplier_name': vals['supplier_name'],
                    'month': month_key,
                    'total_sales': sales,
                    'total_cost': cost,
                    'margin': margin,
                    'margin_percent': margin_pct,
                })
        if line_vals:
            self.env['monthly.supplier.sales.main.line'].create(line_vals)

        self.detail_level = 'main'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tedarikçi Aylık Satış Raporu'),
            'res_model': 'monthly.supplier.sales.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # Drilldowns
    def open_supplier_month(self):
        self.ensure_one()
        supplier = self.env.context.get('default_supplier_id')
        month_key = self.env.context.get('default_month')
        if not supplier or not month_key:
            raise UserError(_('Seçim bilgileri eksik'))

        self.supplier_month_lines.unlink()

        # Find invoices for supplier and month
        year, month = month_key.split('-')
        date_start = fields.Date.from_string(f'{year}-{month}-01')
        if int(month) == 12:
            next_month_first = fields.Date.from_string(f'{int(year)+1}-01-01')
        else:
            next_month_first = fields.Date.from_string(f'{year}-{int(month)+1:02d}-01')
        from datetime import timedelta
        date_end = next_month_first - timedelta(days=1)

        invoices = self.env['account.move'].search(self._prepare_invoice_domain() + [
            ('invoice_date', '>=', date_start), ('invoice_date', '<=', date_end),
        ])

        line_vals = []
        for inv in invoices:
            # Determine if invoice contains products linked to supplier
            has_supplier = False
            invoice_sales = 0.0  # in invoice currency
            invoice_cost = 0.0   # in company currency
            for line in inv.invoice_line_ids:
                prod_supplier = self._get_product_vendor_partner(line.product_id) if line.product_id else False
                if prod_supplier and prod_supplier.id == supplier:
                    has_supplier = True
                    unit_cost = self._compute_cost_price(line)
                    invoice_sales += line.price_subtotal
                    invoice_cost += unit_cost * line.quantity
            if not has_supplier:
                continue

            # Convert to target currency consistently
            sales_conv = self._convert_amount(invoice_sales, inv.currency_id, inv.company_id, inv.invoice_date)
            cost_conv = self._convert_amount(invoice_cost, inv.company_id.currency_id, inv.company_id, inv.invoice_date)
            sales_conv = abs(sales_conv)
            cost_conv = abs(cost_conv)
            margin_conv = sales_conv - cost_conv
            margin_pct = (margin_conv / sales_conv * 100.0) if sales_conv else 0.0
            line_vals.append({
                'report_id': self.id,
                'invoice_id': inv.id,
                'invoice_name': inv.name,
                'invoice_date': inv.invoice_date,
                'supplier_id': supplier,
                'total_sales': sales_conv,
                'total_cost': cost_conv,
                'margin': margin_conv,
                'margin_percent': margin_pct,
            })

        if line_vals:
            self.env['monthly.supplier.sales.supplier.month.line'].create(line_vals)

        self.detail_level = 'supplier_month'
        self.selected_supplier_id = supplier
        self.selected_month = month_key
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tedarikçi Ay Detayı'),
            'res_model': 'monthly.supplier.sales.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def open_invoices(self):
        self.ensure_one()
        invoice_id = self.env.context.get('default_invoice_id')
        if not invoice_id:
            raise UserError(_('Fatura bilgisi eksik'))

        # Populate invoice line lines
        self.invoice_line_lines.unlink()
        inv = self.env['account.move'].browse(invoice_id)
        rows = []
        for line in inv.invoice_line_ids:
            unit_cost = self._compute_cost_price(line)
            line_cost = unit_cost * line.quantity
            margin = line.price_subtotal - line_cost
            margin_pct = (margin / line.price_subtotal * 100.0) if line.price_subtotal else 0.0
            rows.append({
                'report_id': self.id,
                'invoice_id': inv.id,
                'product_name': line.product_id.display_name or line.name,
                'quantity': line.quantity,
                'unit_cost': unit_cost,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
                'margin': margin,
                'margin_percent': margin_pct,
            })
        if rows:
            self.env['monthly.supplier.sales.invoice.line.line'].create(rows)

        self.detail_level = 'invoice_line'
        self.selected_invoice_id = invoice_id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fatura Satırları'),
            'res_model': 'monthly.supplier.sales.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class MonthlySupplierSalesMainLine(models.TransientModel):
    _name = 'monthly.supplier.sales.main.line'
    _description = 'Tedarikçi Aylık Özet Satırı'

    report_id = fields.Many2one('monthly.supplier.sales.report', ondelete='cascade')
    supplier_id = fields.Many2one('res.partner', string='Tedarikçi')
    supplier_name = fields.Char(string='Tedarikçi Adı')
    month = fields.Char(string='Ay')
    total_sales = fields.Float(string='Toplam Satış')
    total_cost = fields.Float(string='Toplam Maliyet')
    margin = fields.Float(string='Kâr')
    margin_percent = fields.Float(string='Kâr %')

    def open_supplier_month(self):
        return self.report_id.open_supplier_month()


class MonthlySupplierSalesSupplierMonthLine(models.TransientModel):
    _name = 'monthly.supplier.sales.supplier.month.line'
    _description = 'Tedarikçi Ay Detay Satırı'

    report_id = fields.Many2one('monthly.supplier.sales.report', ondelete='cascade')
    supplier_id = fields.Many2one('res.partner', string='Tedarikçi')
    invoice_id = fields.Many2one('account.move', string='Fatura')
    invoice_name = fields.Char(string='Fatura No')
    invoice_date = fields.Date(string='Tarih')
    total_sales = fields.Float(string='Satış')
    total_cost = fields.Float(string='Maliyet')
    margin = fields.Float(string='Kâr')
    margin_percent = fields.Float(string='Kâr %')

    def open_invoices(self):
        return self.report_id.open_invoices()


class MonthlySupplierSalesInvoiceLine(models.TransientModel):
    _name = 'monthly.supplier.sales.invoice.line'
    _description = 'Tedarikçi Fatura Özet Satırı'

    report_id = fields.Many2one('monthly.supplier.sales.report', ondelete='cascade')
    invoice_id = fields.Many2one('account.move', string='Fatura')
    invoice_name = fields.Char(string='Fatura No')
    invoice_date = fields.Date(string='Tarih')
    supplier_id = fields.Many2one('res.partner', string='Tedarikçi')
    total_sales = fields.Float(string='Satış')
    total_cost = fields.Float(string='Maliyet')
    margin = fields.Float(string='Kâr')
    margin_percent = fields.Float(string='Kâr %')

    def open_invoices(self):
        return self.report_id.open_invoices()


class MonthlySupplierSalesInvoiceLineLine(models.TransientModel):
    _name = 'monthly.supplier.sales.invoice.line.line'
    _description = 'Tedarikçi Fatura Kalemi'

    report_id = fields.Many2one('monthly.supplier.sales.report', ondelete='cascade')
    invoice_id = fields.Many2one('account.move', string='Fatura')
    product_name = fields.Char(string='Ürün')
    quantity = fields.Float(string='Miktar')
    unit_cost = fields.Float(string='Birim Maliyet')
    price_unit = fields.Float(string='Satış Fiyatı')
    price_subtotal = fields.Float(string='Satır Tutarı')
    margin = fields.Float(string='Kâr')
    margin_percent = fields.Float(string='Kâr %')
