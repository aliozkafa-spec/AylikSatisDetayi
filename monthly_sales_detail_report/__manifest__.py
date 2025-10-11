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
* 3 Seviyeli Drill-Down Sistemi (Aylık → Günlük → Fatura Detayı)
* Aylık kategori toplamları ve trend analizi
* Günlük satış detayları ve fatura sayıları
* Detaylı fatura analizi (müşteri, satış temsilcisi, ödeme durumu)
* Ürün bazında maliyet analizi ve kar marjı hesaplama
* Çoklu para birimi desteği
* Excel export özelliği
* Kategori ve ürün filtreleme seçenekleri
* Navigation breadcrumb sistemi

Yeni Özellikler v2.0:
* Alış maliyeti ve kar marjı analizi
* Satış temsilcisi bazında raporlama
* Ödeme durumu takibi
* Faturaya direkt erişim
* Gelişmiş navigasyon sistemi

Teknik Detaylar:
* Veri kaynağı: Account Move Lines (Fatura Kalemleri)
* Sadece onaylanmış müşteri faturaları dahil
* İptal edilmiş ve taslak faturalar hariç
* Otomatik para birimi dönüştürme
* Kategori hiyerarşisi desteği
* Transient model tabanlı (geçici veri saklama)

Kullanım:
* Accounting > Reporting > Aylık Satış Detay Rapor menüsüne gidin
* Tarih aralığınızı ve filtrelerinizi ayarlayın
* "Rapor Oluştur" butonuna tıklayın
* "Bu Ayın Detayları" ile günlük analize geçin
* "Bu Günün Faturalarını Gör" ile fatura detayına inin
* "Faturayı Odoo'da Aç" ile orijinal faturaya erişin

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
        'views/monthly_sales_detail_report_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
