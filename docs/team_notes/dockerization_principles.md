

# 1️⃣ Production Dockerization'ın amacı

Docker kullanmanın gerçek amacı:

| Amaç | Açıklama |
| --- | --- |
| Reproducibility | Her ortamda aynı çalışan sistem |
| Isolation | Host sistemden bağımsız runtime |
| Portability | Laptop → staging → production |
| Scalability | Kubernetes / orchestrator ile scale |
| Security | Runtime yüzeyini küçültme |

Senior engineer şunu sorar:

> "Bu container compromise olursa ne olur?"

Dockerfile bu yüzden **security-first** yazılır.

---

# 2️⃣ Production Docker Image Prensipleri

## 1️⃣ Minimal base image

En kritik karar: **base image**

Önerilen seçenekler:

| Image | Özellik |
| --- | --- |
| python:3.12-slim | iyi denge |
| alpine | çok küçük ama python için zor |
| distroless | en güvenlisi |
| debian-slim | production için stabil |

Genelde Python için:

```
python:3.12-slim
```

veya

```
gcr.io/distroless/python3
```

kullanılır.

### Neden?

Büyük image =

-   daha fazla CVE
    
-   daha fazla attack surface
    
-   daha fazla download time
    

---

# 3️⃣ Multi-stage build (çok aşamalı build)

Sen zaten doğru noktaya değinmişsin.

Production containerlar **her zaman multi-stage build** kullanır.

Mantık:

```
builder image  
   ↓  
compile / install deps  
   ↓  
runtime image  
   ↓  
only artifacts
```

Builder içinde:

-   compiler
    
-   gcc
    
-   build tools
    

Runtime içinde:

-   sadece çalıştırma ortamı
    

Bu security açısından kritik.

---

# 4️⃣ Örnek Production Dockerfile

Şimdi gerçek production seviyesinde bir örnek veriyorum.

```
dockerfile

\# syntax=docker/dockerfile:1.7  
  
############################################  
\# Builder Stage  
############################################  
FROM python:3.12-slim AS builder  
  
ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1  
  
WORKDIR /app  
  
\# system dependencies  
RUN apt-get update && apt-get install -y \\  
    build-essential \\  
    curl \\  
    && rm -rf /var/lib/apt/lists/\*  
  
\# uv package manager  
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv  
  
\# dependency files  
COPY pyproject.toml uv.lock ./  
  
\# dependency install  
RUN --mount=type=cache,target=/root/.cache \\  
    uv sync \\  
    --locked \\  
    --no-dev \\  
    --no-install-project  
  
############################################  
\# Runtime Stage  
############################################  
FROM python:3.12-slim AS runtime  
  
WORKDIR /app  
  
\# create non-root user  
RUN useradd -m appuser  
  
\# copy virtualenv  
COPY --from=builder /app/.venv /app/.venv  
  
\# add path  
ENV PATH="/app/.venv/bin:$PATH"  
  
\# copy application  
COPY src ./src  
  
\# switch user  
USER appuser  
  
EXPOSE 8000  
  
CMD \["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"\]
```

Bu oldukça production ready.

---

# 5️⃣ Docker Layer Cache Optimization

Docker build süresinin %90'ı yanlış layer kullanımından kaynaklanır.

Yanlış:

```
COPY . .  
RUN pip install -r requirements.txt
```

Her kod değiştiğinde dependency tekrar kurulur.

Doğru:

```
COPY requirements.txt .  
RUN pip install -r requirements.txt  
COPY . .
```

Layer cache korunur.

---

# 6️⃣ Dependency Locking

Production container **deterministic build** olmalıdır.

Yani her build aynı dependency'i kurmalı.

Araçlar:

| Tool | Amaç |
| --- | --- |
| pip-tools | requirements lock |
| poetry | dependency management |
| uv | ultra hızlı resolver |
| pipenv | eski |

Modern stack:

```
pyproject.toml  
uv.lock
```

---

# 7️⃣ Container Security Best Practices

## 1️⃣ Non-root user

Kötü:

```
root
```

Doğru:

```
USER appuser
```

Sebep:

Container escape exploitleri.

---

## 2️⃣ Read-only filesystem

Production'da container:

```
\--read-only
```

ile çalıştırılabilir.

---

## 3️⃣ Drop Linux capabilities

Runtime'da:

```
\--cap-drop=ALL
```

---

## 4️⃣ Seccomp profile

Kernel syscall kısıtlama.

---

## 5️⃣ Image signing

Supply chain attack önlemek için:

```
cosign sign image
```

---

# 8️⃣ SBOM (Software Bill of Materials)

Modern şirketlerde zorunlu hale geliyor.

Araçlar:

| Tool | Amaç |
| --- | --- |
| Syft | SBOM oluşturur |
| Grype | vulnerability scan |
| Trivy | security scanner |

Örnek:

```
trivy image my-image
```

CI pipeline içinde çalışır.

---

# 9️⃣ CI/CD Security Pipeline

Tipik pipeline:

```
git push  
   ↓  
build docker image  
   ↓  
dependency scan  
   ↓  
container scan  
   ↓  
SBOM generate  
   ↓  
sign image  
   ↓  
push registry
```

Örnek araçlar:

| Tool | Amaç |
| --- | --- |
| Trivy | vulnerability scan |
| Snyk | dependency scan |
| Grype | container scan |
| Cosign | image signing |

---

# 🔟 Image Size Optimization

Production imaj hedefi:

```
<200MB
```

İdeal:

```
<100MB
```

Optimize etmek için:

-   slim images
    
-   remove cache
    
-   multi-stage
    
-   compile wheels
    

---

# 11️⃣ Python Performance Optimizations

Environment variable optimizasyonları:

```
ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1  
ENV UV\_COMPILE\_BYTECODE=1
```

Avantaj:

-   startup hızlanır
    
-   memory optimize edilir
    

---

# 12️⃣ Healthcheck

Production container health check içermelidir.

Dockerfile:

```
HEALTHCHECK --interval=30s --timeout=5s \\  
CMD curl -f http://localhost:8000/health || exit 1
```

---

# 13️⃣ Proper Entrypoint

Yanlış:

```
CMD python main.py
```

Doğru:

```
CMD \["uvicorn", "src.main:app", "--host", "0.0.0.0"\]
```

Sebep:

-   signal handling
    
-   graceful shutdown
    

---

# 14️⃣ Signal Handling (çok kritik)

Production'da container shutdown olunca:

```
SIGTERM
```

gönderilir.

Uvicorn / Gunicorn bunu düzgün handle etmelidir.

Örnek:

```
gunicorn -k uvicorn.workers.UvicornWorker
```

---

# 15️⃣ Logging Strategy

Container içinde:

❌ log file yazılmaz

✔ stdout yazılır

Sebep:

Docker log driver.

---

# 16️⃣ Runtime Config

Container içinde config olmaz.

Config:

```
ENV variables
```

Örnek:

```
DATABASE\_URL  
REDIS\_URL  
OPENAI\_API\_KEY
```

12-factor app prensibi.

---

# 17️⃣ Secrets Management

Asla:

```
.env commit
```

Secrets:

| Tool | Amaç |
| --- | --- |
| Vault | secret manager |
| AWS Secrets Manager | cloud secret |
| Kubernetes Secrets | cluster |

---

# 18️⃣ Container Registry

Production registry:

| Registry |
| --- |
| ECR |
| GCR |
| GHCR |
| DockerHub |

Image push edilir.

---

# 19️⃣ Tagging Strategy

Yanlış:

```
latest
```

Doğru:

```
app:1.3.2  
app:git-sha
```

---

# 20️⃣ Production Container Runtime

Container şu şekilde çalıştırılabilir:

```
docker run \\  
\--read-only \\  
\--cap-drop ALL \\  
\--memory 512m \\  
\--cpus 1 \\  
\--pids-limit 100 \\  
app:1.0
```

---

# 21️⃣ Kubernetes düşünülerek Docker yazılmalı

Container şunları desteklemeli:

```
readiness probe  
liveness probe  
graceful shutdown
```

---

# 22️⃣ Observability

Production container şu bilgileri vermeli:

```
/health  
/metrics  
/version
```

Metrics genelde:

```
Prometheus
```

ile scrape edilir.

---

# 23️⃣ Docker Ignore

Çok unutulan şey.

`.dockerignore`

```
.git  
tests  
node\_modules  
.env  
\_\_pycache\_\_
```

---

# 24️⃣ Production Dockerfile Checklist

Senior engineer checklist:

-    multi-stage build
    
-    minimal base image
    
-    dependency lock
    
-    non-root user
    
-    healthcheck
    
-    cache optimization
    
-    security scan
    
-    SBOM
    
-    image signing
    
-    observability endpoints
    

---

# 25️⃣ Senin verdiğin örneğin güçlü tarafları

Senin metnin zaten iyi bir seviyede.

Doğru noktalar:

✔ multi-stage build  
✔ dependency caching  
✔ uv package manager  
✔ distroless runtime  
✔ non-root user  
✔ security scanning

Bunlar **modern DevSecOps** yaklaşımına uyuyor.

---

# 26️⃣ En advanced production pattern

Büyük şirketlerde şu model görülür:

```
repo  
  ↓  
docker build  
  ↓  
trivy scan  
  ↓  
sbom generate  
  ↓  
cosign sign  
  ↓  
push registry  
  ↓  
kubernetes deploy
```

---

# 27️⃣ Senior Engineer Mental Model

Dockerfile yazarken şu sorular sorulur:

1️⃣ Image compromise olursa zarar ne olur?  
2️⃣ Build reproducible mi?  
3️⃣ Build hızlı mı?  
4️⃣ Runtime secure mu?  
5️⃣ Dependency supply chain güvenli mi?

---

💡 Sana önerim:

Bir sonraki soruda şu konuyu sor:

**“Production FastAPI deployment architecture nasıl olmalı?”**

Çünkü gerçek mimari şu 4 parçadan oluşur:

```
Docker  
↓  
Reverse proxy  
↓  
App server  
↓  
Workers
```

ve burada:

-   Nginx
    
-   Gunicorn
    
-   Uvicorn
    
-   Celery
    
-   Redis
    

gibi kritik parçalar devreye girer.


### Dockerfile Optimizasyon Katmanları

1. **Birinci aşama olan Derleyici Katmanı (Builder Stage):** Uygulamanın çalışması için gereken C uzantılı Python kütüphanelerinin derlendiği ortamdır. Burada genellikle `python:3.12-slim` gibi bir temel imaj seçilir ve işletim sistemi seviyesindeki bağımlılıklar (örneğin `build-essential`) kurulur. Daha sonra `uv` aracı, resmi Astral Docker imajından kopyalanarak ortama dahil edilir (`COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv`).
2. **İkinci ve en kritik adım olan Bağımlılık Katmanı:** Kod değişikliklerinden etkilenmemesi için uygulama kaynak kodundan önce çalıştırılır. `pyproject.toml` ve `uv.lock` dosyaları kopyalandıktan sonra, Docker'ın bağlama (bind) ve önbellek (cache) özellikleri kullanılarak bağımlılıklar `/app` dizini altındaki bir sanal ortama kurulur. Bu işlem `RUN --mount=type=cache,target=/root/.cache... uv sync --locked --no-dev --no-install-project` komutuyla gerçekleştirilir. Bu teknik sayesinde, kaynak kodda yapılan ufak bir değişiklikte bile binlerce paketin tekrar indirilmesi engellenerek derleme süreleri dakikalardan saniyelere düşürülür.
3. **Üçüncü aşama olan Çalışma Zamanı Katmanı (Runtime Stage):** Son ürünün oluşturulduğu aşamadır. Güvenliği maksimize etmek için bu aşamada "Distroless" imajlar (örneğin Google'ın paket yöneticisi ve kabuğu olmayan imajları) veya sadece gerekli kütüphaneleri içeren çok hafif slim imajlar tercih edilir. Derleyici katmanında oluşturulan `.venv` klasörü ve kaynak kodlar, doğrudan bu imaja kopyalanır (`COPY --from=builder /app /app`).

### Konteyner Güvenlik Önlemleri

| Konteyner Güvenlik Önlemi | Uygulama Yöntemi | Sentinel-MCP Sistemine Faydası |
| :--- | :--- | :--- |
| **Çok Aşamalı Derleme** | Builder ve Runtime aşamalarını ayırmak | Derleme araçlarını imajdan çıkararak saldırı yüzeyini küçültür. |
| **Kök Olmayan Kullanıcı (Non-root)** | `USER app` ataması ve yetkilendirme | Konteynerden kaçış (container breakout) zafiyetlerinin etkisini sınırlar. |
| **Bayt Kodu Derlemesi** | `ENV UV_COMPILE_BYTECODE=1` kullanımı | Python dosyalarının okuma hızını artırır ve bellek tüketimini optimize eder. |
| **Salt Okunur Dosya Sistemi** | Kod dizininin değiştirilmesini engellemek | Uygulama çalışırken zararlı yazılım enjeksiyonunu önler. |

### CI/CD Boru Hattında Güvenlik Taramaları (Security Scanning)

Konteynerin çalışır durumda olması yeterli değildir; içerdiği kütüphanelerin bilinen zafiyetler barındırmaması kurumsal denetim standartlarının temel şartıdır. Sentinel-MCP CI/CD boru hattına (örneğin GitHub Actions), Aqua Security tarafından sağlanan Trivy veya Anchore tarafından sağlanan Grype gibi güvenlik tarayıcıları entegre edilmelidir.

Sisteme her yeni kod itildiğinde (push), bu araçlar Docker imajının işletim sistemi seviyesini ve içerisindeki Python kütüphanelerini (SBOM - Software Bill of Materials aracılığıyla) analiz eder. Eğer `uv.lock` dosyasında yer alan bir kütüphanede (örneğin FastAPI'nin eski bir sürümü) veya işletim sistemi çekirdeğinde Kritik (CRITICAL) veya Yüksek (HIGH) seviyeli bir CVE (Common Vulnerabilities and Exposures) zafiyeti tespit edilirse, süreç `exit-code: 1` döndürerek derlemeyi anında iptal eder. Bu proaktif mekanizma, zafiyetli kodların hiçbir zaman üretim ortamına, Sivas merkezli sunuculara veya bulut altyapısına ulaşmamasını sağlar.
