#!/bin/bash

# Medical Consumables Report - Deployment Script
# Sunucunuz için özel deployment scripti

set -e

echo "🚀 Medical Consumables Report - Deployment başlatılıyor..."

# Değişkenler
ODOO_PATH="/opt/odoo16"
CUSTOM_ADDONS_PATH="/opt/odoo16/custom-addons"
MODULE_NAME="medical_consumables_report"
ODOO_USER="odoo"
ODOO_SERVICE="odoo16.service"

# Root kullanıcı kontrolü
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Bu script root olarak çalıştırılmalıdır"
    echo "Kullanım: sudo ./deploy.sh"
    exit 1
fi

# Adım 1: Custom addons dizinini oluştur
echo "📁 Custom addons dizini kontrol ediliyor..."
if [ ! -d "$CUSTOM_ADDONS_PATH" ]; then
    echo "📁 Custom addons dizini oluşturuluyor..."
    mkdir -p "$CUSTOM_ADDONS_PATH"
fi

# Adım 2: Eski modülü temizle (varsa)
if [ -d "$CUSTOM_ADDONS_PATH/$MODULE_NAME" ]; then
    echo "🧹 Eski modül temizleniyor..."
    rm -rf "$CUSTOM_ADDONS_PATH/$MODULE_NAME"
fi

# Adım 3: Mevcut modülü kopyala
echo "📥 Modül kopyalanıyor..."
CURRENT_DIR=$(pwd)
cp -r "$CURRENT_DIR" "$CUSTOM_ADDONS_PATH/$MODULE_NAME"

# Adım 4: İzinleri düzelt
echo "🔒 Dosya izinleri ayarlanıyor..."
chown -R $ODOO_USER:$ODOO_USER "$CUSTOM_ADDONS_PATH/$MODULE_NAME"
chmod -R 755 "$CUSTOM_ADDONS_PATH/$MODULE_NAME"

# Adım 5: Python bağımlılıklarını yükle
echo "📦 Python bağımlılıkları yükleniyor..."
sudo -u $ODOO_USER $ODOO_PATH/venv/bin/pip install xlsxwriter

# Adım 6: Odoo config dosyasını kontrol et
echo "⚙️ Odoo config dosyası kontrol ediliyor..."
CONFIG_FILE="/etc/odoo16.conf"
if grep -q "custom-addons" "$CONFIG_FILE"; then
    echo "✅ Custom addons path zaten config'de mevcut"
else
    echo "📝 Config dosyasına custom addons path ekleniyor..."
    # Backup al
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    
    # addons_path satırını güncelle
    if grep -q "^addons_path" "$CONFIG_FILE"; then
        sed -i "s|^addons_path.*|addons_path = /opt/odoo16/src/addons,$CUSTOM_ADDONS_PATH|" "$CONFIG_FILE"
    else
        echo "addons_path = /opt/odoo16/src/addons,$CUSTOM_ADDONS_PATH" >> "$CONFIG_FILE"
    fi
fi

# Adım 7: Odoo servisini restart et
echo "🔄 Odoo servisi restart ediliyor..."
systemctl restart "$ODOO_SERVICE"

# Servis durumunu kontrol et
sleep 5
if systemctl is-active --quiet "$ODOO_SERVICE"; then
    echo "✅ Odoo servisi başarıyla restart edildi"
else
    echo "❌ Odoo servisi restart edilemedi!"
    systemctl status "$ODOO_SERVICE" --no-pager
    exit 1
fi

# Adım 8: Modül dosyalarını listele
echo "📋 Yüklenen modül dosyaları:"
ls -la "$CUSTOM_ADDONS_PATH/$MODULE_NAME"

echo ""
echo "🎉 Deployment tamamlandı!"
echo ""
echo "📝 Sonraki adımlar:"
echo "1. Browser'da Odoo'ya giriş yapın"
echo "2. Apps > Update Apps List tıklayın"
echo "3. 'Medical Consumables' aratın ve Install edin"
echo "4. Accounting > Reporting > Medical Consumables Sales Report menüsüne gidin"
echo ""
echo "🔗 Modül yolu: $CUSTOM_ADDONS_PATH/$MODULE_NAME"
echo "📊 Database: odoo_test"
echo "🌐 Odoo URL: http://localhost:8069 (veya server IP'niz)"
