#!/bin/bash

echo "🔧 Medical Consumables Report - Model Fix"

# Değişkenler
MODULE_DIR="/opt/odoo16/custom-addons/medical_consumables_report"

# Backup al
sudo cp $MODULE_DIR/models/medical_consumables_sales_report.py $MODULE_DIR/models/medical_consumables_sales_report.py.backup

echo "📝 Model dosyasındaki hata düzeltiliyor..."

# Problematik satırı düzelt
sudo sed -i "s/('exclude_from_invoice_tab', '=', False),/# Removed problematic field/g" $MODULE_DIR/models/medical_consumables_sales_report.py

# Hesap tipi filtresi ekle
sudo sed -i "/# Removed problematic field/a\\            # Sadece ürün satırlarını al (account type kontrolü ile)\\n            ('account_id.account_type', 'in', ['income', 'income_other'])," $MODULE_DIR/models/medical_consumables_sales_report.py

echo "🔒 Dosya izinleri düzeltiliyor..."
sudo chown odoo:odoo $MODULE_DIR/models/medical_consumables_sales_report.py
sudo chmod 644 $MODULE_DIR/models/medical_consumables_sales_report.py

echo "🔄 Odoo servisi restart ediliyor..."
sudo systemctl restart odoo16.service

# Servis durumunu kontrol et
sleep 5
if systemctl is-active --quiet odoo16.service; then
    echo "✅ Model düzeltildi ve Odoo servisi restart edildi"
    echo ""
    echo "📝 Sonraki adımlar:"
    echo "1. Odoo'da Apps menüsüne gidin"
    echo "2. Medical Consumables modülünü bulun"
    echo "3. Upgrade butonuna tıklayın"
    echo "4. Raporu tekrar test edin"
else
    echo "❌ Odoo servisi restart edilemedi!"
    sudo systemctl status odoo16.service --no-pager
    exit 1
fi

echo ""
echo "🎉 Fix tamamlandı!"
