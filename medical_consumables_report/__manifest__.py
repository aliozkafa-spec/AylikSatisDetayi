# -*- coding: utf-8 -*-
{
    'name': 'Aylık Satış Detay Rapor',
    'version': '16.0.2.0.0',
    'category': 'Accounting/Reporting',
    'summary': 'Aylık Satış Detay Raporu - Kategori, Ürün, Günlük ve Fatura Detayları',
    'description': """
Aylık Satış Detay Rapor
=======================

Bu modül Odoo 16 Community Edition için tasarlanmış, aylık satış detaylarını 3 seviyeli drill-down 
sistemi ile analiz eden kapsamlı bir raporlama sistemidir.

Temel Özellikler:
* Aylık satış analizi (tarih aralığı seçilebilir)
* Hiyerarşik kategori raporlaması (alt kategoriler dahil)
* İsteğe bağlı tekil ürün analizi
* Çoklu para birimi desteği (USD dönüştürme)
* Tarih aralığı filtreleme
* Excel export özelliği
* Kategori ve ürün filtreleme seçenekleri

Teknik Detaylar:
* Veri kaynağı: Account Move Lines (Fatura Kalemleri)
* Sadece onaylanmış müşteri faturaları dahil
* İptal edilmiş ve taslak faturalar hariç
* Otomatik para birimi dönüştürme
* Kategori hiyerarşisi desteği

Kullanım:
* Accounting > Reporting > Kategori/Ürün Satış Raporu menüsüne gidin
* Tarih aralığınızı ve filtrelerinizi ayarlayın
* "Rapor Oluştur" butonuna tıklayın
* Sonuçları görüntüleyin ve Excel'e aktarın

Gereksinimler:
* Ürün kategorileri düzgün tanımlanmış olmalı
* Ürünler uygun kategorilerde olmalı
* Onaylanmış müşteri faturalarının mevcut olması
    """,
    'author': 'Ali Ozkafa',
    'website': 'https://github.com/aliozkafa-spec',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account', 
        'product',
        'sale',
    ],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/medical_consumables_sales_report_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
