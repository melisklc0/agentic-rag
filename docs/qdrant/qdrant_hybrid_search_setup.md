# Qdrant Hybrid Search & Vector DB Mimari Rehberi (v2)

Bu doküman, kurumsal seviyede bir RAG (Retrieval-Augmented Generation) sistemi için Qdrant üzerinde kurduğumuz **Hybrid Search** mimarisini, "Senior" seviyedeki teknik kararları, hata yönetimini ve standartları kapsar.

---

## 🚀 1. Amaç: Neyi Çözüyoruz?

Modern AI sistemlerinde sadece "benzerlik" (semantic) aramak yeterli değildir. Biz iki farklı sinyali birleştirerek en doğru veriyi bulmayı hedefliyoruz:

| Sinyal Türü | Alan Adı | Teknoloji | Güçlü Yanı |
| :--- | :--- | :--- | :--- |
| **Dense (Yoğun)** | `dense-text` | Embedding (384d) | Anlamı ve bağlamı yakalar. |
| **Sparse (Seyrek)** | `sparse-text` | BM25/SPLADE uyumlu | Exact match, ürün kodu, özel isim. |

---

## 🏗️ 2. Mimari Kararlar ve "Neden?" (Rationales)

2.1 ### 🔹 Named Vectors Standardı
**Karar:** `vectors_config`'i isimlendirilmiş (`dense-text`) olarak tanımladık.
**Neden?** Qdrant varsayılan olarak isimsiz tek bir vektör alanı sunar. Ancak production'da yarın bir gün embedding modelini değiştirmek veya görsel arama (image vector) eklemek istediğimizde, isimlendirilmiş yapı sayesinde mevcut veriyi bozmadan yeni alanlar ekleyebiliriz.

2.2 ### 🔹 Proaktif Şema Doğrulama (Fail-Fast)
**Karar:** `init_collection` sırasında mevcut koleksiyonun ayarlarını (size, distance) kontrol ediyoruz.
**Neden?** RAG sistemlerinde embedding boyutu (örn: 384 vs 768) değişirse eski vektörler anlamsızlaşır. Uygulamanın yanlış veriyle çalışıp sessizce hata üretmesi yerine, startup anında hata verip durması (Fail-Fast) veri bütünlüğü için kritiktir.

2.3 ### 🔹 Payload Indexing (Multi-Tenancy)
**Karar:** `tenant_id`, `document_id` ve `created_at` gibi alanlara otomatik index tanımladık.
**Neden?** Milyonlarca doküman arasında sadece "A şirketinin verilerini getir" dediğimizde, vektör araması öncesinde hızlı bir ön-filtreleme (filtering) yapılması gerekir. Bu index'ler performansın $O(n)$ yerine $O(\log n)$ seviyesinde kalmasını sağlar.

---

## 🛡️ 3. Hata Yönetimi Standardı (Custom Exceptions)

Sistemi daha dirençli kılmak için `src.core.exceptions` altında özel hata sınıfları tanımladık:

- `VectorStoreInitializationError (VEC_01)`: Bootstrap sırasında Qdrant kapalıysa veya şema uyumsuzsa fırlatılır.
- `VectorStoreOperationError (VEC_02)`: `upsert` veya `search` sırasında oluşan çalışma zamanı hatalarını sarmalar.

---

## 📈 4. Gözlemlenebilirlik (Logging & Health)

### 🔹 Structured Logging
Loglarımız artık ham metin yerine bağlamsal veri içerir. Hatalar oluştuğunda detail'lar loglara eklenerek hata tespiti (debug) kolaylaştırılır.

### 🔹 Health Check
`QdrantManager.health_check()` metodu ile sistemin sağlık durumu şu şekilde sorgulanabilir:
- **healthy**: Bağlantı var ve hedef koleksiyon hazır.
- **degraded**: Bağlantı var ama koleksiyon henüz oluşmamış.
- **unhealthy**: Qdrant servisine erişilemiyor.

---

## 💻 5. Terminal ile Doğrulama (Verification)

### A. Koleksiyon Şemasını İnceleme
```bash
curl http://localhost:6333/collections/company_documents
```
**Beklenen Yanıt (Özet):**
```json
{
  "config": {
    "params": {
      "vectors": { "dense-text": { "size": 384, "distance": "Cosine" } },
      "sparse_vectors": { "sparse-text": { } }
    }
  },
  "payload_schema": {
     "tenant_id": { "data_type": "keyword" },
     "document_id": { "data_type": "keyword" }
  }
}
```

---

## ⚙️ 6. Önemli Yapılandırma (Config)

`src/core/config.py` içindeki kritik parametreler:
- `QDRANT_VECTOR_SIZE`: Embedding modelinin boyutu (MiniLM için 384).
- `QDRANT_COLLECTION_NAME`: Verilerin saklandığı fiziksel tablo adı.
- `QDRANT_HOST / PORT`: Bağlantı adresleri (Docker için `qdrant-db` kullanılır).

---

## 📚 7. Ek Kaynaklar
- [Qdrant Mesafe Metrikleri Rehber](./qdrant_metrics_guide.md): Hangi metrik ne zaman kullanılır?
- [Qdrant Deep Dive (Derinlemesine Bakış)](./qdrant_deep_dive.md): Üretim seviyesinde optimizasyon ve mimari detaylar.

---
