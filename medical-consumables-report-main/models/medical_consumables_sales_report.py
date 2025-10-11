# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import xlsxwriter
import base64
import logging

_logger = logging.getLogger(__name__)


class MedicalConsumablesSalesReport(models.TransientModel):
    _name = 'medical.consumables.sales.report'
    _description = 'İki Tarih Aralığında Kategori veya Ürün Bazında Satış Raporu'

    # === Filtre alanları ===
    date_from = fields.Date(
        string='Start Date',
        required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1)
    )
    date_to = fields.Date(
        string='End Date',
        required=True,
        default=lambda self: fields.Date.context_today(self)
    )
    category_ids = fields.Many2many(
        'product.category',
        string='Product Categories',
        help="Boş bırakırsanız tüm kategoriler dahil edilir"
    )
    product_ids = fields.Many2many(
        'product.product',
        string='Specific Products',
        help="Opsiyonel: Belirli ürünleri ayrıca analiz etmek için seçin"
    )
    include_subcategories = fields.Boolean(
        string='Include Subcategories',
        default=True,
        help="Seçilen kategorilerin alt kategorilerini de dahil et"
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Target Currency',
        required=True,
        default=lambda self: (
            self.env.ref('base.USD', raise_if_not_found=False)
            or self.env.company.currency_id
        )
    )

    # === Rapor sonucu ===
    excel_file = fields.Binary(string='Excel File')
    excel_filename = fields.Char(string='Excel Filename')
    report_lines = fields.One2many(
        'medical.consumables.sales.report.line',
        'report_id',
        string='Report Lines'
    )

    # ---------------------------- Helpers ----------------------------
    def _get_selected_categories(self):
        """Seçilen kategorileri döndürür. Alt kategoriler açıksa child_of ile genişletir.
        Hiç seçim yoksa aktif tüm kategoriler döner.
        """
        ProductCategory = self.env['product.category']
        if self.category_ids:
            if self.include_subcategories:
                cats = ProductCategory.search([('id', 'child_of', self.category_ids.ids)])
                _logger.info("DEBUG: Alt kat. dahil kategori sayısı: %s", len(cats))
                return cats
            _logger.info("DEBUG: Sadece seçili kategoriler: %s", len(self.category_ids))
            return self.category_ids
        cats = ProductCategory.search([])
        _logger.info("DEBUG: Hiç seçim yok; tüm kategoriler: %s", len(cats))
        return cats

    def _get_report_data(self):
        """Rapor verilerini hesaplar ve aşağıdaki yapıda döner:
        {
          'YYYY-MM': {
             category_id: {
                'category_name': str,
                'category_total': float,
                'products': { product_id: {'product_name': str, 'amount': float} }
             }
          }
        }
        """
        self.ensure_one()

        categories = self._get_selected_categories()
        if not categories:
            raise UserError(_("No categories found matching your criteria."))

        # Ürün havuzu
        products = self.product_ids or self.env['product.product'].search([
            ('categ_id', 'in', categories.ids),
            ('active', '=', True),
        ])
        if not products:
            raise UserError(_("No products found in the selected categories."))

        # Account Move Line domain
        domain = [
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
            ('move_id.state', '=', 'posted'),
            ('product_id', 'in', products.ids),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            # Odoo 16: gelir hesapları
            ('account_id.account_type', 'in', ['income', 'other_income']),
        ]
        _logger.info("DEBUG: AML domain: %s", domain)

        move_lines = self.env['account.move.line'].search(domain)
        _logger.info("DEBUG: Bulunan fatura satırı sayısı: %s", len(move_lines))

        report_data = {}

        for line in move_lines:
            # Ay anahtarı
            month_key = fields.Date.to_date(line.date).strftime('%Y-%m')

            # Kategori (üründen)
            category = line.product_id.categ_id

            # Tutarı hedef para birimine çevir
            # amount_currency / currency_id varsa onu, yoksa company currency'deki balance'ı kullan
            if line.currency_id:
                src_amount = line.amount_currency
                src_currency = line.currency_id
            else:
                src_amount = line.balance
                src_currency = line.company_currency_id or line.company_id.currency_id

            amount = src_currency._convert(src_amount, self.currency_id, line.company_id, line.date)
            amount = abs(amount)  # satış/iadeyi pozitif göstermek için

            # Ay düğümü
            if month_key not in report_data:
                report_data[month_key] = {}

            # Kategori düğümü
            if category.id not in report_data[month_key]:
                report_data[month_key][category.id] = {
                    'category_name': category.name,
                    'category_total': 0.0,
                    'products': {}
                }

            # Kategori toplamı
            report_data[month_key][category.id]['category_total'] += amount

            # Belirli ürünler seçildiyse, onları ayrıca yaz
            if self.product_ids and line.product_id.id in self.product_ids.ids:
                pkey = line.product_id.id
                if pkey not in report_data[month_key][category.id]['products']:
                    product_code = line.product_id.default_code or 'NO-CODE'
                    product_display_name = '[{}] {}'.format(product_code, line.product_id.name)
                    report_data[month_key][category.id]['products'][pkey] = {
                        'product_name': product_display_name,
                        'amount': 0.0
                    }
                report_data[month_key][category.id]['products'][pkey]['amount'] += amount

        _logger.info("DEBUG: Rapor ay sayısı: %s", len(report_data))
        return report_data

    # ---------------------------- Actions ----------------------------
    def generate_report(self):
        """Raporu oluşturur, satırları yazar, Excel üretir ve wizard'ı açık tutar."""
        self.ensure_one()
        if self.report_lines:
            self.report_lines.unlink()  # Eski satırları temizle

        report_data = self._get_report_data()

        # Report lines oluştur
        line_vals = []
        for month, cats in sorted(report_data.items()):
            for category_id, category_data in cats.items():
                # Kategori toplam satırı
                line_vals.append({
                    'report_id': self.id,
                    'month': month,
                    'category_name': category_data['category_name'],
                    'product_name': False,
                    'amount': category_data['category_total'],
                    'is_category_total': True,
                })
                # Ürün satırları (seçilmişse)
                for product_id, product_data in category_data['products'].items():
                    line_vals.append({
                        'report_id': self.id,
                        'month': month,
                        'category_name': category_data['category_name'],
                        'product_name': product_data['product_name'],
                        'amount': product_data['amount'],
                        'is_category_total': False,
                    })

        if line_vals:
            self.env['medical.consumables.sales.report.line'].create(line_vals)

        # Excel oluştur
        self._generate_excel_report(report_data)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Medical Consumables Sales Report'),
            'res_model': 'medical.consumables.sales.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ---------------------------- Export ----------------------------
    def _generate_excel_report(self, report_data):
        """Excel raporunu oluşturup binary alana yazar."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Kategori Urun Satis Raporu')

        # Formatlar
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        category_format = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1})
        product_format = workbook.add_format({'border': 1, 'indent': 1})
        amount_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})

        # Başlıklar
        headers = ['Month', 'Category', 'Product', 'Total Sales ({})'.format(self.currency_id.name)]
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # Veri satırları
        row = 1
        for month in sorted(report_data.keys()):
            for category_id, category_data in report_data[month].items():
                # Kategori satırı
                worksheet.write(row, 0, month, category_format)
                worksheet.write(row, 1, category_data['category_name'], category_format)
                worksheet.write(row, 2, 'TOTAL', category_format)
                worksheet.write_number(row, 3, category_data['category_total'], category_format)
                row += 1

                # Ürün satırları
                for product_id, product_data in category_data['products'].items():
                    worksheet.write(row, 0, month, product_format)
                    worksheet.write(row, 1, category_data['category_name'], product_format)
                    worksheet.write(row, 2, product_data['product_name'], product_format)
                    worksheet.write_number(row, 3, product_data['amount'], amount_format)
                    row += 1

        # Sütun genişlikleri
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 18)

        workbook.close()
        output.seek(0)

        df = self.date_from.strftime('%Y-%m-%d') if self.date_from else ''
        dt = self.date_to.strftime('%Y-%m-%d') if self.date_to else ''
        filename = "kategori_urun_satis_raporu_{}_{}.xlsx".format(df, dt)

        self.excel_file = base64.b64encode(output.read())
        self.excel_filename = filename


class MedicalConsumablesSalesReportLine(models.TransientModel):
    _name = 'medical.consumables.sales.report.line'
    _description = 'İki Tarih Aralığında Kategori veya Ürün Bazında Satış Raporu Line'

    report_id = fields.Many2one(
        'medical.consumables.sales.report',
        string='Report',
        ondelete='cascade'
    )
    month = fields.Char(string='Month')
    category_name = fields.Char(string='Category')
    product_name = fields.Char(string='Product')
    amount = fields.Float(string='Amount')
    is_category_total = fields.Boolean(string='Is Category Total')
