# Aylık Satış Detay Rapor - Odoo 16 Module

## 📋 Proje Açıklaması

Bu modül Odoo 16 Community Edition için tasarlanmış, aylık satış detaylarını 3 seviyeli drill-down sistemi ile analiz eden kapsamlı bir raporlama sistemidir.

## 🚀 Özellikler

### 🎯 Ana Özellikler
- ✅ **3 Seviyeli Drill-Down Sistemi** (Aylık → Günlük → Fatura Detayı)
- ✅ **Aylık kategori toplamları** ve trend analizi
- ✅ **Günlük satış detayları** ve fatura sayıları  
- ✅ **Detaylı fatura analizi** (müşteri, satış temsilcisi, ödeme durumu)
- ✅ **Alış maliyeti ve kar marjı** analizi
- ✅ **Çoklu para birimi** desteği
- ✅ **Excel export** özelliği
- ✅ **Navigation breadcrumb** sistemi

### 🆕 Yeni Özellikler v2.0
- ✅ **Satış temsilcisi** bazında raporlama
- ✅ **Ödeme durumu** takibi
- ✅ **Faturaya direkt erişim** (Odoo'da aç)
- ✅ **Gelişmiş navigasyon** sistemi
- ✅ **Kar marjı hesaplama** (alış fiyatı - satış fiyatı)

## 📁 Proje Yapısı

```
medical_consumables_report/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── medical_consumables_sales_report.py
├── views/
│   └── medical_consumables_sales_report_views.xml
├── security/
│   └── ir.model.access.csv
├── static/
│   └── description/
│       ├── icon.png
│       └── index.html
├── README.md
└── LICENSE
```

## 🛠️ Kurulum (Sunucunuza Özel)

### Mevcut Sunucu Detayları
- **Odoo Path:** `/opt/odoo16/`
- **Venv Path:** `/opt/odoo16/venv/`
- **Config:** `/etc/odoo16.conf`
- **Service:** `odoo16.service`
- **Database:** `odoo_test`
- **Python Version:** 3.10

### Kurulum Adımları

1. **Repository'yi klonlayın:**
```bash
cd /opt/odoo16/
git clone https://github.com/aliozkafa-spec/medical-consumables-report.git
```

2. **Modülü custom addons dizinine taşıyın:**
```bash
# Önce custom addons dizini oluşturun (yoksa)
sudo mkdir -p /opt/odoo16/custom-addons

# Modülü kopyalayın
sudo cp -r medical-consumables-report /opt/odoo16/custom-addons/medical_consumables_report

# İzinleri düzeltin
sudo chown -R odoo:odoo /opt/odoo16/custom-addons/
```

3. **Python bağımlılıklarını yükleyin:**
```bash
# Virtual environment'a geçin
sudo -u odoo /opt/odoo16/venv/bin/pip install xlsxwriter
```

4. **Odoo config dosyasını güncelleyin:**
```bash
sudo nano /etc/odoo16.conf

# Şu satırı bulun ve güncelleyin:
# addons_path = /opt/odoo16/src/addons,/opt/odoo16/custom-addons
```

5. **Odoo servisini restart edin:**
```bash
sudo systemctl restart odoo16.service
sudo systemctl status odoo16.service --no-pager
```

6. **Modülü aktive edin:**
- Browser'da Odoo'ya giriş yapın
- Apps > Update Apps List
- "Kategori/Ürün Satış Raporu" aratın ve Install edin

## 📊 Kullanım

1. **Accounting > Reporting > Kategori/Ürün Satış Raporu** menüsüne gidin
2. Tarih aralığınızı ve filtrelerinizi ayarlayın
3. "Rapor Oluştur" tıklayın
4. Sonuçları görüntüleyin ve Excel'e export edin

## ⚙️ Teknik Detaylar

### Veri Kaynağı
- **Model:** account.move.line (Fatura Kalemleri)
- **Filtreler:** 
  - Sadece müşteri faturaları (`move_type='out_invoice'`)
  - Sadece onaylanmış faturalar (`state='posted'`)
  - İptal edilmiş faturalar hariç

### Hesaplamalar
- Parasal tutarlar USD'ye çevrilir
- Negatif tutarlar pozitife çevrilir (satış faturaları için)
- Kategori ve ürün bazında toplama işlemleri

### Excel Export
- Dinamik sütun genişlikleri
- Formatlanmış sayısal değerler
- Kategori ve ürün hiyerarşisi

## 🔧 Geliştirme

### Development Setup

1. **Development branch oluşturun:**
```bash
git checkout -b feature/your-feature-name
```

2. **Değişikliklerinizi commit edin:**
```bash
git add .
git commit -m "feat: your feature description"
```

3. **Pull request oluşturun**

### Code Style
- PEP 8 Python standartları
- Odoo development guidelines
- Meaningful commit messages

## 📝 API Referansı

### Ana Model: `medical.consumables.sales.report`

#### Metodlar:
- `generate_report()` - Raporu oluşturur ve Excel dosyası üretir
- `_get_selected_categories()` - Seçilen kategorileri döndürür
- `_get_report_data()` - Ham rapor verilerini hesaplar
- `_generate_excel_report()` - Excel dosyasını oluşturur

#### Alanlar:
- `date_from`, `date_to` - Tarih aralığı
- `category_ids` - Seçili kategoriler
- `product_ids` - Seçili ürünler
- `currency_id` - Hedef para birimi
- `excel_file` - Export edilen Excel dosyası

## 🤝 Katkı Sağlama

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'inizi push edin (`git push origin feature/AmazingFeature`)
5. Pull Request açın

## 📄 Lisans

Bu proje LGPL-3.0 lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 👥 İletişim

- **Proje Sahibi:** Ali Ozkafa
- **Email:** Ali.ozkafa@gmail.com
- **GitHub:** [@aliozkafa-spec](https://github.com/aliozkafa-spec)

## 📈 Versiyon Geçmişi

- **v1.0.0** - İlk sürüm
  - Temel rapor fonksiyonları
  - Excel export
  - Kategori ve ürün filtreleme

- **v1.1.0** - İsim ve Kapsam Güncellemesi
  - İsim değiştirildi: "İki Tarih Aralığında Kategori veya Ürün Bazında Satış Raporu"
  - Medical Consumables özel kısıtlaması kaldırıldı
  - Tüm kategoriler için uyumlu hale getirildi

---

⭐ **Bu projeyi beğendiyseniz yıldızlamayı unutmayın!**
