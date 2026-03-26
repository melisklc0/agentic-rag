# API Standartları, Mimari ve Güvenlik: Mühendislik El Kitabı (V3.0 - The Ultimate Guide)

Bu doküman, bir API'nın sadece "çalışması" için değil; kurumsal seviyede, ölçeklenebilir, güvenli ve sürdürülebilir bir ekosistem yaratması için gereken tüm standartları kapsayan **Nihai Engineering Handbook**'tur. Bu rehber, "sıfır soru işareti" ilkesiyle hazırlanmıştır.

---

## 1) Neden API Standartları? (Zihinsel Model)

API standartları, bir projenin başarısında "opsiyonel" değil, "zorunlu" bir temeldir. Standart yoksa şu sorunlar kaçınılmazdır:

*   **Contract Drift (Sözleşme Bozulması):** Frontend ve Backend arasındaki veri uyumsuzluğu nedeniyle sürekli hata (break) oluşması.
*   **Onboarding Zorluğu:** Yeni katılan mühendislerin her endpoint'i "deneme-yanılma" ile anlamaya çalışması.
*   **Troubleshooting Kabusu:** Traceability (izlenebilirlik) eksikliği nedeniyle bir hatanın kaynağını bulmanın saatler sürmesi.
*   **Security Audit Zafiyeti:** Yetki kontrollerinin dağınık olması sebebiyle veri sızıntısı riskinin artması.
*   **Geriye Uyumluluk (Backward Incompatibility):** Yapılan minik bir değişikliğin mevcut client'ları bozması.

---

## 2) API Katmanları (Request Journey)

İyi bir API projesinde sorumluluklar (Separation of Concerns) katmanlara ayrılır. Bir isteğin uçtan uca yolculuğu şöyledir:

1.  **Network Edge / Load Balancer:** Nginx veya API Gateway isteği karşılar (Rate limiting, TLS termination).
2.  **Middleware Katmanı:** Global hata yönetimi (Exception handler), Request ID üretimi ve CORS kontrolleri yapılır.
3.  **Authentication (Identity):** "Kimsin sen?" (JWT, API Key, OAuth2).
4.  **Authorization (Permission):** "Tamam sen Ayşe'sin ama bu belgeyi silmeye yetkin var mı?" (RBAC/Tenancy/Row-level control).
5.  **Router / Controller:** İstek ilgili endpoint fonksiyonuna yönlendirilir.
6.  **Schema / DTO Katmanı:** Pydantic modelleriyle verinin tipi ve içeriği doğrulanır.
7.  **Service Layer (Business Logic):** Ana iş mantığının (Yemek pişme yerinin) döndüğü yer.
8.  **Repository Layer:** Veritabanı sorgularının (SQL/NoSQL/Vector) soyutlandığı katman.
9.  **External Clients:** OpenAI, Anthropic gibi dış API'larla konuşan katman.
10. **Background Jobs:** Uzun süren işlemler için kuyruk mekanizması.

---

## 3) İletişim Protokolleri Derin Dalış

| Özellik | REST | gRPC | Webhooks | WebSockets |
| :--- | :--- | :--- | :--- | :--- |
| **Protokol** | HTTP/1.1 or 2 | HTTP/2 | HTTP/1.1 | Binary (Full Duplex) |
| **Okunabilirlik** | Yüksek (JSON) | Düşük (Binary) | Yüksek (JSON) | Metin/Binary |
| **Gecikme** | Orta | Çok Düşük | N/A (Async) | Düşük |
| **Streaming** | Sınırlı (SSE) | Mükemmel (Bi-di) | Yok | Çift Yönlü |
| **Kullanım** | Genel Web/Mobile| Mikroservis (S2S) | Event-Push | Canlı Veri / Chat |

**Karar:**
- **Public API:** Daima REST.
- **İç Servisler (Internal):** Yüksek hız için gRPC.
- **Dış Servis Bildirimi:** Webhooks.

---

## 4) HTTP Method Semantiği ve Resource Tasarımı

Endpoint naming'de "Resource endpoint" ve "Action endpoint" ayrımı hayat kurtarır.

### 4.1 Resource Endpoint (Noun-based)
Daima isim kullanılır, fiil kullanılmaz.
*   `GET /documents`: Bütün belgeler.
*   `GET /documents/{id}`: Tek belge.
*   `POST /documents`: Yeni belge.
*   `DELETE /documents/{id}`: Belgeyi sil.

### 4.2 Action Endpoint (Verb-based)
CRUD'a sığmayan özel eylemler için kullanılır.
*   `POST /documents/{id}/parse`: Belgeyi ayrıştır (Fiil sonunda).
*   `POST /search/hybrid`: Hibrit arama yap.
*   **Kural:** Action endpoint'ler daima **POST** olmalıdır (Safe olmadıkları için).

### 4.3 Safe vs Unsafe, Idempotent vs Non-Idempotent
| Metod | Safe | Idempotent | Senaryo |
| :--- | :--- | :--- | :--- |
| **GET** | ✅ Evet | ✅ Evet | Okuma işlemleri. Yan etki yaratamaz. |
| **POST** | ❌ Hayır| ❌ Hayır| Yeni kayıt. 10 kere basarsan 10 kayıt oluşur. |
| **PUT** | ❌ Hayır| ✅ Evet | Kaydı tamamen değiştirme. 10 kere de aynı şeyi yazar. |
| **PATCH** | ❌ Hayır| ❌ Hayır| Kısmi güncelleme (Eski veriye bağlıysa değişebilir). |
| **DELETE** | ❌ Hayır| ✅ Evet | 1. silmede silinir, sonrakilerde "zaten yok" döner. |

---

## 📦 5) Request / Response Standartları (The Contract)

Her yanıt, frontend'in beklediği bir "Zarf (Envelope)" içinde olmalıdır.

### 5.1 Success Envelope
```json
{
  "success": true,
  "data": { "id": 1, "name": "Test" },
  "meta": {
    "request_id": "req-01",
    "timestamp": "2024-03-26T12:00:00Z"
  }
}
```

### 5.2 Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "AUTH_01",
    "message": "Detailed public error message",
    "details": null
  },
  "request_id": "req-01"
}
```

### 5.3 Validation Error (422)
```json
{
  "success": false,
  "error": {
    "code": "VAL_01",
    "message": "Validation failed",
    "details": [
      { "loc": ["body", "email"], "msg": "value is not a valid email" }
    ]
  }
}
```

### 5.4 Pagination Formatları
**Page-based:**
```json
"pagination": {
  "total": 100,
  "page": 1,
  "limit": 10,
  "pages": 10
}
```
**Cursor-based (Recommended for RAG):**
```json
"pagination": {
  "next_cursor": "c29tZV9pZA==",
  "has_next": true
}
```

---

## ❌ 6) Error Handling ve Error Code Taksonomisi

HTTP status kodları tek başına yetersizdir. Uygulama bazlı namespace yapısı zorunludur.

### 6.1 Hata Kodu Yapısı
*   `AUTH_`: Kimlik/Yetki (`AUTH_01`: Expired Token).
*   `DOC_`: Doküman işlemleri (`DOC_01`: PDF Error).
*   `QDR_`: Qdrant/Vektör DB hataları.
*   `SYS_`: Altyapı hataları (`SYS_500`: DB Connection).

### 6.2 HTTP Status İlişkisi
- **400 Bad Request:** Yanlış parametre, anlamsız istek.
- **401 Unauthorized:** Kimlik yok veya geçersiz.
- **403 Forbidden:** Kimlik var ama yetki yok.
- **404 Not Found:** Kaynak yok.
- **422 Unprocessable Entity:** Veri tipi doğru ama iş mantığına aykırı (Örn: Boş PDF).
- **429 Too Many Requests:** Rate limit aşımı.
- **500 Internal Server Error:** Beklenmedik teknik hata.

---

## 🔄 7) Versiyonlama ve Geriye Uyumluluk

### 7.1 URI Versioning
Standart olarak URI kullanılır: `/api/v1/...`. Header versioning sadece çok özel durumlarda (Proxy uyumluluğu vb.) tercih edilir.

### 7.2 Breaking vs Non-Breaking Changes
*   **Breaking (V2 Gerekir):** Alan silme, Alan ismi değiştirme (`document_id` -> `doc_id`), Zorunlu alan ekleme.
*   **Non-Breaking (V1 Devam):** Yeni opsiyonel alan ekleme, Yeni endpoint ekleme.

### 7.3 Sunset & Deprecation Policy
1.  **Deprecated:** Response Header: `Deprecation: true`.
2.  **Sunset:** Response Header: `Sunset: 2024-12-31`.
3.  Minimum 6 ay geçiş süresi verilir.

---

## 🛡️ 8) Authorization ve Multi-Tenancy

### 8.1 RBAC vs ABAC
*   **RBAC (Role-Based):** Admin, User, Viewer.
*   **ABAC (Attribute-Based):** "Sadece kendi oluşturduğu belgeleri görebilir."

### 8.2 Tenant Isolation (Aşırı Kritik!)
Sisteme giren her kullanıcı bir `tenant_id`'ye bağlıdır. 
- **Kural:** Her veritabanı sorgusunda `WHERE tenant_id = <X>` filtresi zorunludur.
- **Row-level Security:** Veritabanı seviyesinde izolasyon her zaman tercih edilir.

---

## 🚦 9) Rate Limiting, Retry ve Timeout

### 9.1 Rate Limiting (Throttling)
*   **Limit:** Kullanıcı başına 100 req/min.
*   **Burst:** Ani 10 isteğe izin, sonra sınırlama.
*   **Header:** `X-RateLimit-Remaining`, `Retry-After`.

### 9.2 Retry & Circuit Breaker
Dış servislere (OpenAI/Qdrant) atılan isteklerde:
- **Exponential Backoff:** 1s, 2s, 4s bekleyerek tekrar dene.
- **Circuit Breaker:** Eğer bir servis sürekli 500 veriyorsa, sistemi korumak için istekleri 60 saniye boyunca hiç gönderme.

---

## 🔍 10) Pagination, Filtering ve Sorting Standardı

### 10.1 List Standardı
*   **Filter:** `GET /docs?status=indexed&type=pdf`.
*   **Sort:** `GET /docs?sort=-created_at,title` (Eksi: Descending).
*   **Pagination:** `GET /docs?limit=20&offset=40`.

---

## ⚙️ 11) Browser Güvenliği (CORS / CSRF)

*   **CORS:** `Allow-Origin` kısmına asla `*` konulmaz. Sadece staging ve prod domain'leri.
*   **CSRF:** JWT kullanılıyorsa `Cookie` yerine `Authorization: Bearer <TOKEN>` header'ı tercih edilir (CSRF'i doğal olarak engeller). Cookie kullanılacaksa `SameSite=Strict` ve `HttpOnly` zorunludur.

---

## ☁️ 12) API Gateway ve Network Edge

*   **Reverse Proxy (NGINX):** IP bazlı yasaklama, TLS sonlandırma, İstek boyutu sınırı (Max Client Body Size: 50MB).
*   **Timeout Policy:** Gateway timeout (60s) uygulamanın timeout değerinden büyük olmalıdır.

---

## 💾 13) Caching Stratejisi

*   **Response Cache:** `/config` gibi statik veriler Redis'te tutulur.
*   **Browser Cache:** `Cache-Control: public, max-age=3600`.
*   **ETag:** Dosya değişmediyse `304 Not Modified` dönerek trafik tasarrufu sağlanır.

---

## ⏱️ 14) Async Processing & Job APIs

Uygulamamızdaki ağır işler için:
1.  **İstek:** `POST /documents/upload` -> **202 Accepted**.
2.  **Yanıt:** `{ "job_id": "xyz", "status": "processing" }`.
3.  **Polling:** `GET /jobs/xyz` ile durum kontrolü (`queued`, `processing`, `completed`, `failed`).

---

## 🩺 15) Health, Readiness, Liveness Farkı

*   **Liveness:** Uygulama yaşıyor mu? Öldüyse restart at.
*   **Readiness:** Uygulama DB ve Qdrant'a bağlı mı? Cevap veremeyecekse trafik gönderme.
*   **Startup:** Uygulama ilk ayağa kalktı mı? (Büyük modeller yüklenene kadar bekler).

---

## 📊 16) Observability Implementation (Teknik Uygulama)

*   **Structured Logging:** Mesajlar değil, veriler loglanır (JSON formatı).
*   **Correlation ID:** API Gateway -> Service A -> Service B -> DB zincirini takip eden `X-Request-ID`.
*   **PII Masking:** Loglarda e-posta, şifre ve token'lar REDACTED olarak görünmelidir.
*   **Metric Naming:** `api_request_duration_seconds_bucket{endpoint="/search"}`.

---

## 🧪 17) Testing Strategy (Derinlemesine)

1.  **Unit Tests:** Sadece o fonksiyon (Tüm bağımlılıklar Mock).
2.  **Integration Tests:** Gerçek Test-DB ile endpoint testi.
3.  **Contract Tests:** Swagger şemasına (OpenAPI) gerçekten uyuyor muyuz?
4.  **Load Test (k6/Locust):** 1000 kullanıcıda API nerede kırılıyor?
5.  **Smoke Test:** Deployment sonrası en temel feature'lar çalışıyor mu?

---

## 🚢 18) Deployment ve Runtime Standards

*   **Uvicorn/Gunicorn:** `--workers (2 * CPU + 1)` formülüyle çalıştırılır.
*   **Graceful Shutdown:** `SIGTERM` sinyali geldiğinde o anki istekleri bitirip güvenli kapanma.
*   **Env Precedence:** Secret Manager (Vault) > Environment Variables > YAML.

---

## 🤖 19) AI / RAG Spesifik API Standartları (The AI Layer)

RAG projemiz için özel kurallar:

### 19.1 Indexing & Chunking Metadata
Dokümanlar parçalandığında (chunk), her parça şu metadata'ya sahip olmalıdır:
```json
{
  "doc_id": "uuid",
  "page_no": 1,
  "chunk_index": 5,
  "source_type": "PDF",
  "hash": "sha256_of_content"
}
```

### 19.2 Search Citation Standardı
Bir arama veya chat yanıtında, bilginin nereden geldiği mutlaka belirtilmelidir:
```json
{
  "answer": "Qdrant is fast",
  "sources": [
    { "doc_id": "doc_1", "page": 2, "score": 0.99 }
  ]
}
```

### 19.3 Streaming Chat (SSE)
FastAPI `StreamingResponse` kullanılarak `text/event-stream` formatında token-by-token yanıt.

---

## 🚫 20) Naming Conventions ve Anti-Patterns

### Naming
- **URL Path:** lowercase-kebab-case (`/document-processing`).
- **Query Params:** snake_case (`?tenant_id=1`).
- **JSON Keys:** snake_case (`"user_first_name": "..."`).

### Anti-Patterns
- Router içine ağır `for` loopları veya ağır I/O yazmak.
- Exception'ları yakalamayıp ham traceback'i kullanıcıya göstermek.
- Veritabanı modellerini direkt API'den dışarı açmak (Daima DTO/Schema kullan!).

---

## 🧩 21) Karar Matrisi (Final)

*   **Latency-Critical S2S:** gRPC.
*   **Web Frontend Connection:** REST.
*   **10 saniyeden uzun süren iş:** Async Job (202 Accepted).
*   **Canlı Bildirim:** Webhooks.

---

> [!IMPORTANT]
> **Son Söz:** İyi bir API tasarımı, senin yazdığın kodun değil, verdiğin sözün (Contract) kalitesidir. Bu standartlara uymak ekibi bir arada tutar. 😎✨🚀
