# 🔗 Frontend-Backend Bağlantı Durumu

## ✅ Bağlantı Durumu: **TAMAMEN BAĞLI**

Frontend ve backend birbirine bağlı ve çalışır durumda!

## 📡 Bağlantı Detayları

### 1. **CORS (Cross-Origin Resource Sharing)**
- ✅ Backend'de CORS aktif (`app/main.py`)
- ✅ Tüm origin'lerden istek kabul ediliyor
- ✅ Production'da spesifik domain belirtilebilir

### 2. **API Endpoints**
Frontend şu endpoint'leri kullanıyor:

| Endpoint | Method | Kullanım |
|----------|--------|----------|
| `/` | GET | Ana sayfa (frontend HTML) |
| `/health` | GET | API durumu kontrolü |
| `/upload` | POST | Video yükleme ve storyboard oluşturma |

### 3. **Frontend Yapılandırması**
- ✅ API URL ayarlanabilir (varsayılan: `http://localhost:8080`)
- ✅ FormData ile dosya ve parametreler gönderiliyor
- ✅ Hata yönetimi ve loading durumları mevcut

### 4. **Backend Parametreleri**
- ✅ `file`: Video dosyası (multipart/form-data)
- ✅ `interval_seconds`: Frame aralığı (Form parametresi)

## 🚀 Nasıl Kullanılır?

### Yöntem 1: Backend üzerinden (Önerilen)

1. **Backend'i başlat:**
```bash
cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

2. **Tarayıcıda aç:**
```
http://localhost:8080
```

Backend otomatik olarak frontend'i sunar!

### Yöntem 2: Ayrı sunucular

1. **Backend'i başlat:**
```bash
cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

2. **Frontend'i ayrı sun:**
```bash
cd web
python -m http.server 8000
```

3. **Frontend'de API URL'yi ayarla:**
- `index.html` açıldığında "API Endpoint" alanına `http://localhost:8080` yaz

### Yöntem 3: Docker ile

```bash
# Docker build
docker build -f Dockerfile.cpu -t frameforge:latest .

# Docker run
docker run -p 8080:8080 frameforge:latest

# Tarayıcıda aç
http://localhost:8080
```

## 🔍 Test Etme

### 1. API Health Check
```bash
curl http://localhost:8080/health
```

### 2. Frontend Test
1. Tarayıcıda `http://localhost:8080` aç
2. Bir video dosyası seç (≤10 saniye önerilir)
3. "Generate Storyboard" butonuna tıkla
4. Sonuçları görüntüle

### 3. API Test (curl)
```bash
curl -X POST "http://localhost:8080/upload" \
  -F "file=@test_video.mp4" \
  -F "interval_seconds=2.0"
```

## 📝 Önemli Notlar

1. **Model Yükleme**: İlk başlatmada model yüklenir (biraz zaman alabilir)
2. **GCS Bucket**: GCS bucket adı belirtilmediyse stub modda çalışır
3. **GPU**: Local'de GPU yoksa CPU modda çalışır (stub captions)
4. **CORS**: Development için tüm origin'ler açık, production'da kısıtlanmalı

## 🐛 Sorun Giderme

### Frontend API'ye bağlanamıyor
- ✅ Docker Desktop çalışıyor mu?
- ✅ Backend çalışıyor mu? (`http://localhost:8080/health` kontrol et)
- ✅ API URL doğru mu? (varsayılan: `http://localhost:8080`)

### CORS hatası
- ✅ Backend'de CORS middleware aktif mi?
- ✅ Frontend ve backend farklı portlarda mı? (normal)

### Upload hatası
- ✅ Video dosyası çok büyük mü? (≤50MB önerilir)
- ✅ Video formatı destekleniyor mu? (mp4, avi, mov, vb.)

## ✨ Sonuç

Frontend ve backend **tamamen entegre** ve çalışır durumda! 🎉

