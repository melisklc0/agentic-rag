# Qdrant: Üretim Seviyesinde Derinlemesine Bakış (Deep Dive)

Bu doküman, Qdrant vektör veritabanı için kurumsal seviyede bir rehber sunar. Hedef; sadece veri yüklemek değil, yüksek performanslı, ölçeklenebilir ve güvenilir bir RAG altyapısı kurmaktır.

---

## 1) Zihinsel Model: Qdrant Mimarisi

Qdrant'ın hiyerarşisi şu şekildedir:
- **Collection (Koleksiyon):** Verilerin mantıksal grubudur (SQL tablosu gibi).
- **Point (Nokta):** Tek bir kayıt. İçeriğinde bir `id`, vektörler (isimlendirilmiş) ve payloada (metadata) sahiptir.
- **Shard (Parça):** Koleksiyonun yatayda bölünmüş halidir. Veri miktarı arttıkça yükü dağıtmak için kullanılır.
- **Replica (Kopya):** Hata toleransı için shard'ların kopyalarıdır.

---

## 2) Vektör Optimizasyonu ve HNSW

Qdrant, benzerlik araması için **HNSW (Hierarchical Navigable Small World)** algoritmasını kullanır. Bu algoritmanın en kritik iki parametresi şunlardır:

### 2.1 `m` (Graph Connectivity)
*   **Nedir?** Her düğümün (noktanın) graf üzerinde kaç komşuya sahip olacağını belirler.
*   **Production Kararı:** Varsayılan (16), çoğu RAG sistemi için yeterlidir. Ancak çok boyutlu (1024+) vektörlerde bu değeri 32-64'e çıkarmak "Recall"ı (doğruluk oranını) artırır.
*   **Maliyet:** RAM kullanımı artar, indeksleme süresi uzar.

### 2.2 `ef_construct` (Build Thoroughness)
*   **Nedir?** İndeks oluşturulurken kaç tane potansiyel komşunun değerlendirileceğini belirler.
*   **Production Kararı:** 100-200 arası güvenli bir başlangıçtır. Çok yüksek doğruluk gerekiyorsa 500'e kadar çıkılabilir.
*   **Püf Noktası:** İndeksleme bittikten sonra bu değeri değiştirmenin bir maliyeti yoktur, ancak arama hızını etkilemez; sadece indeks kalitesini etkiler.

---

## 3) Quantization (Sıkıştırma) - RAM Canavarlarını Dizginlemek

Milyonlarca vektörünüz varsa RAM maliyeti ciddi bir sorun haline gelir. Qdrant burada üç çözüm sunar:

| Yöntem | Sıkıştırma Oranı | Doğruluk Kaybı | Hız Kazancı |
| :--- | :--- | :--- | :--- |
| **Scalar (Int8)** | 4x | < %1 | 2x |
| **Binary (1-bit)** | 32x | %10-15 | 40x |
| **Product (PQ)** | 8-16x | Değişken | 3x |

**Best Practice:** Genelde `Scalar Quantization (int8)` üretimde en dengeli yöntemdir. `Binary Quantization` sadece çok yüksek boyutlu (OpenAI 1536 gibi) ve doğruluğun hıza göre bir tık geride olduğu durumlarda kullanılmalıdır.

---

## 4) Payload Indexing (Hızlı Filtreleme)

Vektör araması yapmadan önce `tenant_id` veya `created_at` gibi alanlarla filtreleme yapıyorsanız, bu alanları **mutlaka** indekslemelisiniz.

```python
# Örnek: Keyword Index (tenant_id için)
client.create_payload_index(
    collection_name="docs",
    field_name="tenant_id",
    field_schema="keyword" # keyword, integer, float, geo, datetime
)
```

Eğer indeksleme yapmazsanız, Qdrant her aramada tüm payloada bakmak zorunda kalır (Full Scan) ve performans felaketi yaşanır.

---

## 5) Ölçeklenebilirlik: Sharding ve Replication

### 5.1 Sharding Stratejisi
*   **Automatic:** Qdrant veriyi rastgele shard'lara dağıtır.
*   **User-defined (Multi-tenancy):** Bir tenant'ın tüm verisini aynı shard'a koyabilirsiniz. Bu, küçük tenant'lar için arama hızını artırır (Query Shard Limit).

### 5.2 Replication Factor
Üretim ortamında `replication_factor: 2` veya `3` kullanılmalıdır. Bu sayede bir Qdrant düğümü çöksene sistem çalışmaya devam eder.

---

## 6) Hybrid Search: Sparse + Dense Birleşimi

Bizim sistemimizde RAG doğruluğunu artıran ana unsur budur. 
1.  **Dense:** Anlamsal benzerlik (Semantic).
2.  **Sparse:** Anahtar kelime eşleşmesi (Lexical - BM25 benzeri).

Qdrant bu ikisini **Reciprocal Rank Fusion (RRF)** algoritmasıyla birleştirerek en iyi sonucu döndürür.

---

## 7) Üretim (Production) Kontrol Listesi

- [ ] **On-Disk Storage:** RAM yetmiyorsa `hnsw_config` içerisinde `on_disk: true` ayarını yapın.
- [ ] **Snapshots:** Her gece otomatik snapshot alın. Qdrant canlı sistemden snapshot alabilir.
- [ ] **Health Check:** Liveness ve Readiness proplarını mutlaka ekleyin (HTTP 200 `/health`).
- [ ] **Consistency:** Yazma işlemlerinde `wait=true` kullanarak verinin tüm replikalara gittiğinden emin olun.
- [ ] **Memory Mapping:** Linux mmap limitlerini (`vm.max_map_count`) yüksek tutun.

---

## 8) Örnek: Profesyonel Koleksiyon Kurulumu

```python
await client.create_collection(
    collection_name="rag_collection",
    vectors_config={
        "dense-text": VectorParams(
            size=1536,
            distance=Distance.COSINE,
            hnsw_config=HnswConfigDiff(m=32, ef_construct=200, on_disk=True)
        )
    },
    quantization_config=ScalarQuantization(
        scalar=ScalarType.INT8,
        quantile=0.99,
        always_ram=True
    ),
    replication_factor=2,
    shard_number=2
)
```

---

> [!IMPORTANT]
> Bu doküman, koddaki `QdrantManager` sınıfının neden bu şekilde yapılandırıldığının teorik ve operasyonel temelini oluşturur.
