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
- ✅ `interval_seconds`: Frame extraction interval (default: 2.0)
- ✅ `use_scene_detection`: Intelligent scene detection (default: true)
- ✅ `scene_threshold`: Scene change threshold (default: 27.0)
- ✅ `enable_audio_analysis`: Audio transcription (default: false)
- ✅ `whisper_model`: Whisper model size - base/small/medium (default: base)
- ✅ `enable_narrative_analysis`: Screenplay generation (default: true)
- ✅ `narrative_method`: "captions" or "video" (default: captions)

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

Backend otomatik olarak frontend'i `app/static/index.html` dosyasından sunar!

### Yöntem 2: Docker ile (Önerilen - Production benzeri)

1. **Docker build:**
```bash
docker build -f Dockerfile.cpu -t frameforge:latest .
```

2. **Docker run:**
```bash
docker run -p 8080:8080 frameforge:latest
```

3. **Tarayıcıda aç:**
```
http://localhost:8080
```

### Yöntem 3: Cloud Run'da (Production)

```bash
# Build and deploy to Cloud Run GPU
gcloud builds submit --tag europe-west4-docker.pkg.dev/frameforge-477214/frameforge-repo/frameforge-gpu:latest

gcloud run deploy frameforge-gpu \
  --image europe-west4-docker.pkg.dev/frameforge-477214/frameforge-repo/frameforge-gpu:latest \
  --region europe-west4 \
  --gpu=1 \
  --gpu-type=nvidia-l4 \
  --memory=16Gi \
  --cpu=4 \
  --allow-unauthenticated \
  --set-env-vars GCS_BUCKET_NAME=frameforge-bucket,GOOGLE_API_KEY=your_key
```

## 🔍 Test Etme

### 1. API Health Check
```bash
curl http://localhost:8080/health
```

### 2. Frontend Test
1. Tarayıcıda `http://localhost:8080` aç
2. Bir video dosyası seç (≤150MB önerilir)
3. İsteğe bağlı olarak ayarları yapılandır:
   - **Scene Detection**: Intelligent frame extraction
   - **Audio Analysis**: Whisper ile transcription
   - **Narrative Analysis**: Gemini ile screenplay generation
4. "Generate Storyboard" butonuna tıkla
5. Sonuçları görüntüle:
   - Frame thumbnails ve captions
   - Screenplay (logline, synopsis, scenes)
   - Audio transcription (eğer aktifse)

### 3. API Test (curl)

**Basit test (sadece frame extraction ve captioning):**
```bash
curl -X POST "http://localhost:8080/upload" \
  -F "file=@test_video.mp4" \
  -F "interval_seconds=2.0" \
  -F "use_scene_detection=false" \
  -F "enable_audio_analysis=false" \
  -F "enable_narrative_analysis=false"
```

**Tam özellikli test:**
```bash
curl -X POST "http://localhost:8080/upload" \
  -F "file=@test_video.mp4" \
  -F "use_scene_detection=true" \
  -F "scene_threshold=27.0" \
  -F "enable_audio_analysis=true" \
  -F "whisper_model=base" \
  -F "enable_narrative_analysis=true" \
  -F "narrative_method=captions"
```

## 📝 Önemli Notlar

1. **Frontend Konumu**: Frontend dosyası `app/static/index.html` konumundadır (artık `web/` klasörü yok)
2. **Model Yükleme**: İlk başlatmada BLIP modeli yüklenir (~30-60 saniye sürebilir)
3. **GCS Bucket**: Production'da GCS bucket (`frameforge-bucket`) gereklidir
4. **GPU**: Local development için `Dockerfile.cpu` kullanın (GPU Dockerfile sadece Cloud Run için)
5. **CORS**: Development için tüm origin'ler açık, production'da kısıtlanmalı
6. **Narrative Analysis**: `GOOGLE_API_KEY` environment variable gerektirir (Gemini API)
7. **Max File Size**: Video dosyası maksimum 150MB olabilir
8. **Processing Time**:
   - Frame extraction: ~2-5 saniye
   - Captioning: ~0.5-1 saniye/frame (GPU)
   - Audio transcription: ~5-10 saniye (optional)
   - Narrative generation: ~3-5 saniye (optional)

## 🐛 Sorun Giderme

### Frontend API'ye bağlanamıyor
- ✅ Docker Desktop çalışıyor mu?
- ✅ Backend çalışıyor mu? (`http://localhost:8080/health` kontrol et)
- ✅ API URL doğru mu? (varsayılan: `http://localhost:8080`)

### CORS hatası
- ✅ Backend'de CORS middleware aktif mi?
- ✅ Frontend ve backend farklı portlarda mı? (normal)

### Upload hatası
- ✅ Video dosyası çok büyük mü? (≤150MB limit)
- ✅ Video formatı destekleniyor mu? (mp4, avi, mov, webm, vb.)
- ✅ Model yüklendi mi? (`/health` endpoint'ini kontrol et)

### Narrative analysis çalışmıyor
- ✅ `GOOGLE_API_KEY` environment variable set edildi mi?
- ✅ Gemini API quota'nız doldu mu?
- ✅ `enable_narrative_analysis=true` parametresi gönderildi mi?

## ✨ Sonuç

Frontend ve backend **tamamen entegre** ve çalışır durumda! 🎉

