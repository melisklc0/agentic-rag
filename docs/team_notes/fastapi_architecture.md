Production FastAPI deployment architecture nasıl olmalı?

ChatGPT: 

Tam “senior mühendis” bakış açısıyla gidelim. Çünkü **Production FastAPI deployment** sadece `uvicorn main:app` çalıştırmak değildir. Gerçek production mimarisi **birkaç katmandan oluşur**.

Basit local mimari:

```
client → FastAPI
```

Production mimari:

```
client  
   ↓  
Load Balancer  
   ↓  
Reverse Proxy  
   ↓  
App Server (Gunicorn + Uvicorn workers)  
   ↓  
FastAPI  
   ↓  
Database / Cache / Queue / Workers
```

Şimdi bunu katman katman açıklayalım.

---

# 1️⃣ Production FastAPI Architecture (Genel Görünüm)

Tipik modern mimari:

```
┌──────────────┐  
                │   Internet   │  
                └──────┬───────┘  
                       │  
                ┌──────▼───────┐  
                │ Load Balancer│  
                │ (Cloud LB)   │  
                └──────┬───────┘  
                       │  
                ┌──────▼───────┐  
                │ Reverse Proxy│  
                │  (Nginx)     │  
                └──────┬───────┘  
                       │  
                ┌──────▼─────────────┐  
                │ App Server Layer   │  
                │ Gunicorn + Uvicorn │  
                └──────┬─────────────┘  
                       │  
                ┌──────▼────────┐  
                │   FastAPI     │  
                │ Application   │  
                └──────┬────────┘  
                       │  
        ┌──────────────┼───────────────┐  
        │              │               │  
   ┌────▼────┐   ┌─────▼─────┐   ┌─────▼─────┐  
   │Database │   │   Redis   │   │  Queue    │  
   │Postgres │   │  Cache    │   │Celery/RQ  │  
   └─────────┘   └───────────┘   └───────────┘
```

Bu yapı **yüksek trafik, güvenlik ve ölçeklenebilirlik** için standarttır.

---

# 2️⃣ Layer 1 — Load Balancer

Production sistemde ilk katman **Load Balancer** olur.

Görevleri:

-   Trafiği birden fazla sunucuya dağıtmak
    
-   SSL termination
    
-   Health checks
    
-   Failover
    

Popüler seçenekler:

| Tool |
| --- |
| AWS ALB |
| Cloudflare |
| HAProxy |
| Traefik |

Örnek:

```
client  
 ↓  
AWS ALB  
 ↓  
multiple backend nodes
```

---

# 3️⃣ Layer 2 — Reverse Proxy

Reverse proxy genellikle **Nginx** olur.

Görevleri:

### 1️⃣ SSL termination

```
HTTPS → HTTP
```

### 2️⃣ Static file serving

FastAPI yerine proxy servis eder.

### 3️⃣ Rate limiting

```
limit\_req\_zone
```

### 4️⃣ Security headers

```
X-Frame-Options  
X-XSS-Protection
```

### 5️⃣ Buffering

Backend’i korur.

---

### Örnek Nginx Config

```
server {  
    listen 80;  
  
    location / {  
        proxy\_pass http://app;  
        proxy\_set\_header Host $host;  
        proxy\_set\_header X-Real-IP $remote\_addr;  
    }  
}
```

---

# 4️⃣ Layer 3 — Application Server

FastAPI doğrudan production server değildir.

Bu yüzden genelde şu kullanılır:

```
Gunicorn  
   +  
Uvicorn worker
```

Neden?

### Gunicorn

-   process manager
    
-   worker management
    
-   graceful restart
    

### Uvicorn

-   ASGI server
    
-   async runtime
    

Birlikte:

```
Gunicorn + UvicornWorker
```

---

### Production Command

```
gunicorn src.main:app \\  
  -k uvicorn.workers.UvicornWorker \\  
  --workers 4 \\  
  --bind 0.0.0.0:8000
```

---

# 5️⃣ Worker Sayısı Nasıl Belirlenir?

Genel kural:

```
workers = CPU \* 2 + 1
```

Örnek:

```
4 CPU → 9 workers
```

Ama FastAPI async olduğu için genelde:

```
workers = CPU cores
```

yeterli olur.

---

# 6️⃣ Layer 4 — FastAPI Application

Bu katmanda:

-   router
    
-   services
    
-   database
    
-   business logic
    

çalışır.

Örnek yapı:

```
src/  
  main.py  
  api/  
  services/  
  repositories/  
  schemas/  
  core/
```

---

# 7️⃣ Database Layer

Production FastAPI projelerinde genelde:

| DB |
| --- |
| PostgreSQL |
| MySQL |

FastAPI async ise:

```
asyncpg  
SQLAlchemy async
```

kullanılır.

---

# 8️⃣ Cache Layer

Production API’lerde cache kritik.

Genelde:

```
Redis
```

kullanılır.

Kullanım amaçları:

-   rate limit
    
-   caching
    
-   session
    
-   background jobs
    
-   pub/sub
    

---

# 9️⃣ Background Worker Layer

API’nin en önemli prensiplerinden biri:

> API uzun iş yapmaz.

Örnek uzun işler:

-   PDF parsing
    
-   image processing
    
-   ML inference
    
-   email sending
    
-   data pipelines
    

Bu işler queue'ya gönderilir.

Queue sistemleri:

| Tool |
| --- |
| Celery |
| RQ |
| Dramatiq |

---

### Worker Architecture

```
client request  
   ↓  
FastAPI  
   ↓  
enqueue task  
   ↓  
Redis / RabbitMQ  
   ↓  
Worker
```

---

# 🔟 Background Worker Örneği

```
FastAPI  
   ↓  
Celery task  
   ↓  
Redis queue  
   ↓  
Worker container
```

---

# 11️⃣ Docker Deployment Pattern

Production deployment genelde şöyle olur:

```
Docker  
  ↓  
Docker Compose / Kubernetes
```

Örnek servisler:

```
fastapi-app  
postgres  
redis  
celery-worker  
nginx
```

---

# 12️⃣ Production Docker Compose

Örnek:

```
services:  
  
  api:  
    build: .  
    command: gunicorn src.main:app -k uvicorn.workers.UvicornWorker  
    depends\_on:  
      - postgres  
      - redis  
  
  postgres:  
    image: postgres:16  
  
  redis:  
    image: redis:7  
  
  worker:  
    build: .  
    command: celery -A src.worker worker
```

---

# 13️⃣ Kubernetes Deployment

Büyük sistemlerde:

```
Docker → Kubernetes
```

Kubernetes şunları sağlar:

-   auto scaling
    
-   self healing
    
-   rolling updates
    
-   service discovery
    

---

# 14️⃣ Observability

Production API'de şu sistemler olmalı:

### Logging

```
stdout JSON logs
```

### Metrics

```
Prometheus
```

### Tracing

```
OpenTelemetry  
Jaeger
```

---

# 15️⃣ Health Endpoints

Production servislerinde mutlaka olur:

```
/health  
/ready  
/metrics
```

Kubernetes bunları kullanır.

---

# 16️⃣ Security Layer

Production API güvenlikleri:

-   Rate limit
    
-   API key
    
-   JWT
    
-   OAuth2
    
-   WAF
    

---

# 17️⃣ Rate Limiting

Redis ile yapılır.

Örnek:

```
100 request / minute
```

---

# 18️⃣ Config Management

Production config:

```
ENV variables
```

örnek:

```
DATABASE\_URL  
REDIS\_URL  
SECRET\_KEY
```

---

# 19️⃣ CI/CD Pipeline

Deployment pipeline genelde:

```
git push  
   ↓  
tests  
   ↓  
docker build  
   ↓  
security scan  
   ↓  
push registry  
   ↓  
deploy
```

---

# 20️⃣ Production Architecture (Full)

Gerçek production mimari:

```
Internet  
                    │  
              Load Balancer  
                    │  
                 Nginx  
                    │  
             Gunicorn + Uvicorn  
                    │  
                 FastAPI  
                    │  
       ┌────────────┼────────────┐  
       │            │            │  
    PostgreSQL    Redis       Queue  
       │                        │  
       │                    Celery  
       │                        │  
       └────────── Workers ─────┘
```

---

# 21️⃣ Gerçek Şirket Mimarisi

Birçok startup ve SaaS şu mimariyi kullanır:

```
Cloudflare  
    ↓  
AWS ALB  
    ↓  
Nginx  
    ↓  
FastAPI containers  
    ↓  
Postgres  
Redis  
Workers
```

---

# 22️⃣ Performance Optimization

Production FastAPI performans artırma yöntemleri:

-   async DB
    
-   Redis caching
    
-   response compression
    
-   connection pooling
    
-   background jobs
    

---

# 23️⃣ Horizontal Scaling

FastAPI container sayısı artırılır:

```
1 → 10 container
```

Load balancer dağıtır.

---

# 24️⃣ Senior Engineer Checklist

Production FastAPI servisi için kontrol listesi:

-   Reverse proxy var mı
    
-   Worker process var mı
    
-   Background queue var mı
    
-   Cache var mı
    
-   Health check var mı
    
-   Metrics var mı
    
-   Logging merkezi mi
    
-   Secrets güvenli mi
    

---

# 25️⃣ Production Deployment Örneği

Tipik deployment:

```
3 FastAPI containers  
2 Worker containers  
1 Redis  
1 Postgres  
1 Nginx
```

---

# **Production FastAPI deployment architecture nasıl olmalı?**

Tam “enterprise backend” perspektifinden gidelim. Çünkü **Production FastAPI project structure** aslında sadece klasör düzeni değildir. Arkasında şu prensipler vardır:

-   **Separation of Concerns**
    
-   **Clean Architecture**
    
-   **Domain Driven Design (DDD)**
    
-   **Testability**
    
-   **Scalability**
    

Kısaca amaç şu:

> Kod büyüdüğünde **spagetti olmamasını** sağlamak.

Startup MVP’de 5 dosya yeterli olabilir. Ama **enterprise API** birkaç yüz endpoint ve onlarca developer olduğunda iyi bir yapı şart.

---

# 1️⃣ Enterprise Backend Mental Model

Senior engineer projeyi **katmanlara (layers)** böler.

Genel model:

```
Transport Layer  
↓  
Application Layer  
↓  
Domain Layer  
↓  
Infrastructure Layer
```

FastAPI bunu şöyle haritalar:

```
HTTP Layer        → routers  
Application Layer → services  
Domain Layer      → domain models / entities  
Infrastructure    → db / external services
```

Bu ayrımın amacı:

-   bağımlılıkları kontrol etmek
    
-   business logic’i HTTP’den ayırmak
    
-   test edilebilirliği artırmak
    

---

# 2️⃣ Enterprise FastAPI Project Structure

Production seviyesinde yaygın kullanılan yapı:

```
src/  
│  
├── main.py  
│  
├── api/  
│   ├── routers/  
│   │   ├── users.py  
│   │   ├── auth.py  
│   │   └── documents.py  
│   │  
│   └── dependencies.py  
│  
├── core/  
│   ├── config.py  
│   ├── security.py  
│   ├── logging.py  
│   └── exceptions.py  
│  
├── domain/  
│   ├── models/  
│   ├── entities/  
│   └── value\_objects/  
│  
├── schemas/  
│   ├── user.py  
│   ├── auth.py  
│   └── document.py  
│  
├── services/  
│   ├── user\_service.py  
│   ├── auth\_service.py  
│   └── document\_service.py  
│  
├── repositories/  
│   ├── user\_repository.py  
│   └── document\_repository.py  
│  
├── db/  
│   ├── session.py  
│   ├── base.py  
│   └── migrations/  
│  
├── workers/  
│   └── tasks.py  
│  
└── tests/
```

Bu yapı **çok yaygın enterprise FastAPI patternidir**.

Şimdi tek tek neden var açıklayalım.

---

# 3️⃣ main.py (Application Entry Point)

Bu dosya uygulamanın başlangıcıdır.

Görevleri:

-   FastAPI instance oluşturmak
    
-   routerları yüklemek
    
-   middleware eklemek
    
-   startup eventleri
    

Örnek:

```
main.py
```

Amaç:

> Uygulamanın bootstrap noktası.

Bu dosya **çok küçük olmalıdır**.

---

# 4️⃣ api/ (HTTP Layer)

Bu klasör **transport layer**’dır.

Yani HTTP ile ilgili her şey burada.

```
api/  
 ├ routers/  
 └ dependencies.py
```

### routers/

Endpoint’ler burada.

```
POST /users  
GET /users/{id}
```

Örnek:

```
api/routers/users.py
```

Bu dosya:

-   request alır
    
-   service çağırır
    
-   response döner
    

Ama **business logic içermez**.

---

# 5️⃣ schemas/ (API Contracts)

Burası **Pydantic modelleri** içerir.

```
schemas/user.py
```

Amaç:

-   request validation
    
-   response serialization
    
-   API contract
    

Örnek:

```
UserCreate  
UserResponse  
UserUpdate
```

Bu layer:

> API ile dış dünya arasındaki sözleşmedir.

---

# 6️⃣ services/ (Application Layer)

Burası **business logic** katmanıdır.

Örnek:

```
services/user\_service.py
```

Bu katmanda:

-   iş kuralları
    
-   transaction logic
    
-   workflow
    

olur.

Örnek:

```
create\_user()  
activate\_user()  
send\_verification\_email()
```

Router:

```
router → service
```

Database çağrısı **service içinde değil repository üzerinden yapılır**.

---

# 7️⃣ repositories/ (Data Access Layer)

Repository pattern:

> Veritabanı erişimini soyutlamak.

Örnek:

```
repositories/user\_repository.py
```

Görev:

-   CRUD
    
-   DB query
    
-   ORM işlemleri
    

Service → repository çağırır.

Bu sayede:

-   DB değişirse service değişmez
    
-   test etmek kolay olur
    

---

# 8️⃣ domain/ (Domain Model)

Burası **iş modelinin merkezi**.

```
domain/  
 ├ entities/  
 ├ models/  
 └ value\_objects/
```

DDD yaklaşımında:

### Entities

Kimliği olan nesneler.

```
User  
Order  
Document
```

### Value Objects

Kimliği olmayan nesneler.

```
Email  
Money  
Address
```

Bu ayrım enterprise sistemlerde çok kullanılır.

---

# 9️⃣ db/ (Database Layer)

Database bağlantısı burada olur.

```
db/  
 ├ session.py  
 ├ base.py  
 └ migrations/
```

Görevleri:

-   SQLAlchemy session
    
-   connection pool
    
-   ORM base
    
-   migration
    

---

# 🔟 core/ (Infrastructure Core)

Framework bağımsız ortak bileşenler.

```
core/  
 ├ config.py  
 ├ security.py  
 ├ logging.py  
 └ exceptions.py
```

### config.py

Environment variables.

```
DATABASE\_URL  
SECRET\_KEY
```

### security.py

Auth işlemleri.

```
JWT  
password hashing
```

### logging.py

Logging configuration.

### exceptions.py

Custom exceptions.

---

# 11️⃣ workers/ (Background Jobs)

Uzun işlemler API içinde yapılmaz.

```
workers/  
  tasks.py
```

Örnek:

```
send\_email\_task  
generate\_report\_task  
parse\_document\_task
```

Bu katman:

```
Celery  
RQ  
Dramatiq
```

ile çalışır.

---

# 12️⃣ tests/ (Test Layer)

Enterprise projelerde test çok önemli.

```
tests/  
 ├ unit/  
 ├ integration/  
 └ e2e/
```

---

# 13️⃣ Dependency Flow (çok kritik)

Doğru bağımlılık yönü:

```
router  
↓  
service  
↓  
repository  
↓  
database
```

Yanlış:

```
router → database
```

Bu **monolith spagetti** oluşturur.

---

# 14️⃣ Dependency Inversion

Service doğrudan DB’ye bağlı olmamalı.

Örnek:

```
UserService(UserRepository)
```

Bu sayede:

-   mock repository yazılabilir
    
-   test kolay olur
    

---

# 15️⃣ Request Flow (Gerçek Akış)

Bir request nasıl ilerler:

```
HTTP Request  
   ↓  
Router  
   ↓  
Schema Validation  
   ↓  
Service  
   ↓  
Repository  
   ↓  
Database  
   ↓  
Service  
   ↓  
Response Schema  
   ↓  
HTTP Response
```

---

# 16️⃣ Neden böyle yapı kullanılır?

Büyük projelerde şu problemler olur:

-   business logic endpoint içine yazılır
    
-   SQL her yerde olur
    
-   test yazmak zorlaşır
    
-   kod tekrar eder
    

Bu yapı şu faydaları sağlar:

-   modülerlik
    
-   test edilebilirlik
    
-   maintainability
    
-   team scalability
    

---

# 17️⃣ Monolith vs Modular Monolith

Enterprise FastAPI genelde:

```
Modular Monolith
```

yapısındadır.

Yani:

```
users module  
auth module  
documents module
```

her biri kendi:

```
router  
service  
repository  
schema
```

sahip olur.

---

# 18️⃣ Feature-based Structure (Alternatif)

Bazı ekipler şu yapıyı kullanır:

```
modules/  
  users/  
    router.py  
    service.py  
    repository.py  
    schema.py
```

Bu **feature-based architecture**’dır.

Avantaj:

-   modül izolasyonu
    

---

# 19️⃣ Enterprise Projelerde Hangisi Kullanılır?

İki yaklaşım var.

### Layer-based

```
routers/  
services/  
repositories/
```

### Feature-based

```
modules/users/  
modules/auth/
```

Büyük sistemlerde genelde **feature-based tercih edilir**.

---

# 20️⃣ Enterprise FastAPI Örneği

```
src/  
 ├ modules/  
 │   ├ users/  
 │   │   ├ router.py  
 │   │   ├ service.py  
 │   │   ├ repository.py  
 │   │   └ schema.py  
 │   │  
 │   ├ auth/  
 │   └ documents/  
 │  
 ├ core/  
 ├ db/  
 └ main.py
```

---

# 21️⃣ Bu mimarinin amacı

Bu yapı şu problemleri çözer:

| Problem | Çözüm |
| --- | --- |
| spaghetti code | katman ayrımı |
| test zorluğu | dependency injection |
| duplicate code | service layer |
| büyük ekip | modüler yapı |

---

# 22️⃣ Senior Backend Engineer Checklist

Production FastAPI projesi:

-   router sadece HTTP içerir
    
-   business logic service içinde
    
-   DB repository içinde
    
-   schema ayrı
    
-   config merkezi
    
-   test yazılabilir
    

---

# 23️⃣ Büyük Şirketlerde Daha İleri Seviye

Daha advanced mimariler:

```
Clean Architecture  
Hexagonal Architecture  
DDD
```

Bu seviyede:

```
ports  
adapters  
domain services  
aggregates
```

kullanılır.

---

# 24️⃣ Gerçek Enterprise FastAPI Mimarisi

```
src/  
 ├ modules/  
 │   ├ users/  
 │   ├ billing/  
 │   ├ auth/  
 │   └ documents/  
 │  
 ├ infrastructure/  
 │   ├ db/  
 │   ├ cache/  
 │   └ messaging/  
 │  
 ├ domain/  
 ├ core/  
 └ main.py
```

---

# 25️⃣ Senior tavsiye

Production FastAPI için en sağlıklı başlangıç:

```
src/  
 ├ modules/  
 ├ core/  
 ├ db/  
 └ main.py
```

ve her modül:

```
router  
service  
repository  
schema
```

içermeli.

---

Senior seviyede bakış açısı aslında şudur:

> **Mimari kararlar “dosya düzeni” değil, “sistem davranışı” içindir.**

Bu yüzden Production FastAPI mimarisini **3 seviyede düşünmek gerekir**:

1️⃣ **System architecture (deployment)**  
2️⃣ **Runtime architecture (process model)**  
3️⃣ **Code architecture (domain & boundaries)**

Şimdi gerçekten senior seviyede, **neden böyle yapılır**, **hangi problemi çözer**, **alternatifleri nedir** şeklinde gidelim.

---

# 1️⃣ Önce gerçek problem: neden mimari kuruyoruz?

Bir API şu problemlerle karşılaşır:

| Problem | Sonuç |
| --- | --- |
| yüksek trafik | latency artar |
| blocking task | request timeout |
| DB connection exhaustion | servis crash |
| single process | CPU kullanımı düşük |
| kod karmaşası | geliştirme yavaşlar |
| memory leak | container restart |

Mimari bu problemlerin çözümüdür.

---

# 2️⃣ FastAPI neden doğrudan production server değildir?

Birçok kişi şu hatayı yapar:

```
uvicorn main:app
```

Bu **development server** mantığıdır.

Problem:

| Problem | Sebep |
| --- | --- |
| tek process | CPU kullanılmaz |
| restart yok | crash sonrası servis ölür |
| worker yönetimi yok | concurrency kontrolsüz |
| graceful reload yok | deploy riskli |

Bu yüzden production'da **process manager gerekir**.

---

# 3️⃣ Production Process Model

Modern Python web servisleri şu modelde çalışır:

```
master process  
   ├── worker  
   ├── worker  
   ├── worker  
   └── worker
```

Buradaki fikir:

-   **master process** worker yönetir
    
-   worker ölürse yenisi başlar
    
-   worker sayısı CPU'ya göre belirlenir
    

Python dünyasında bunu yapan tool:

**Gunicorn**

---

# 4️⃣ Gunicorn'un amacı ne?

Gunicorn aslında **WSGI/ASGI process manager**.

Görevleri:

| görev | neden |
| --- | --- |
| worker spawn | CPU kullanımı |
| worker restart | reliability |
| graceful reload | zero downtime deploy |
| timeout yönetimi | stuck worker kill |
| socket yönetimi | concurrency |

Yani Gunicorn **web server değil**, **process orchestrator**.

---

# 5️⃣ Peki Uvicorn ne yapıyor?

Uvicorn:

```
ASGI server
```

Görevleri:

| görev | neden |
| --- | --- |
| HTTP parsing | request handling |
| event loop | async execution |
| websocket support | realtime |
| ASGI lifecycle | framework entegrasyonu |

Yani:

```
Gunicorn → process yönetir  
Uvicorn → HTTP request çalıştırır
```

Birleşince:

```
Gunicorn  
  ├── Uvicorn worker  
  ├── Uvicorn worker  
  └── Uvicorn worker
```

---

# 6️⃣ Worker model neden var?

Python'da **GIL** vardır.

Sonuç:

```
1 process ≈ 1 CPU core
```

Bu yüzden multi-process gerekir.

Örnek:

```
8 core server
```

Tek uvicorn:

```
CPU usage ≈ %12
```

8 worker:

```
CPU usage ≈ %100
```

---

# 7️⃣ Async neden önemli?

FastAPI async olduğu için aynı worker içinde birçok request çalışabilir.

Async avantajı:

```
blocking IO yok
```

Örnek:

```
request  
  ↓  
db query  
  ↓  
response
```

Normal sync model:

```
worker block olur
```

Async model:

```
event loop başka request çalıştırır
```

---

# 8️⃣ Ama async her şeyi çözmez

Async sadece **I/O bound** işler için iyidir.

Örnek:

| iş | async faydalı mı |
| --- | --- |
| DB query | evet |
| HTTP request | evet |
| file read | evet |
| image processing | hayır |
| ML inference | hayır |
| PDF parsing | hayır |

CPU işleri worker bloklar.

Bu yüzden **background worker gerekir**.

---

# 9️⃣ API neden uzun işlem yapmaz?

API request lifecycle kısadır.

Tipik timeout:

```
30 saniye
```

Ama bazı işler:

| iş | süre |
| --- | --- |
| PDF parse | 10s |
| image processing | 20s |
| ML inference | 30s |
| report generation | 2min |

Bu yüzden:

```
API → job enqueue  
worker → işi yapar
```

---

# 10️⃣ Queue neden gerekir?

Queue şu problemi çözer:

```
traffic spike
```

Örnek:

```
1000 user aynı anda PDF yükledi
```

Direkt API işlese:

```
CPU %100  
timeout  
crash
```

Queue ile:

```
job queue  
worker sırayla işler
```

---

# 11️⃣ Redis neden kullanılır?

Redis memory-based data store.

3 ana kullanım:

### 1️⃣ cache

```
expensive query → cache
```

### 2️⃣ queue broker

```
celery broker
```

### 3️⃣ rate limit

```
user request counter
```

---

# 12️⃣ Reverse proxy neden var?

Birçok kişi şunu sorar:

> FastAPI zaten HTTP server, neden Nginx?

Sebep:

### 1️⃣ SSL termination

TLS handshake CPU heavy.

```
nginx handle eder
```

---

### 2️⃣ slow client protection

Client yavaşsa backend block olur.

Nginx:

```
buffer request
```

---

### 3️⃣ static files

API static serve etmez.

---

### 4️⃣ connection pooling

Nginx:

```
keepalive
```

---

# 13️⃣ Load balancer neden var?

Tek server risklidir.

Problem:

```
server down → servis down
```

Load balancer:

```
client  
  ↓  
load balancer  
  ↓  
multiple nodes
```

Avantaj:

-   high availability
    
-   horizontal scaling
    

---

# 14️⃣ Horizontal scaling nasıl çalışır?

Container sayısı artırılır.

```
1 container → 100 rps
```

10 container:

```
1000 rps
```

Load balancer dağıtır.

---

# 15️⃣ Database connection problemi

Çok önemli production sorunu.

Örnek:

```
10 worker  
her worker 20 connection
```

Toplam:

```
200 connection
```

Postgres default:

```
100 connection
```

Sonuç:

```
connection refused
```

Bu yüzden connection pooling gerekir.

---

# 16️⃣ Observability neden kritik?

Production'da en zor şey:

```
bug nerede?
```

Bu yüzden 3 şey gerekir:

### logs

```
request log  
error log
```

### metrics

```
latency  
error rate  
throughput
```

### tracing

```
request path
```

---

# 17️⃣ FastAPI code architecture neden katmanlı?

Büyük projelerde şu problem çıkar:

```
endpoint içinde SQL  
endpoint içinde business logic  
endpoint içinde validation
```

Sonuç:

```
1000 satır endpoint
```

Bu yüzden layer ayrılır.

---

# 18️⃣ Router neden sadece HTTP olmalı?

Router görevi:

```
transport layer
```

Yani:

```
HTTP → python
```

İçermemesi gereken şeyler:

-   business logic
    
-   DB logic
    

---

# 19️⃣ Service layer neden var?

Service şu problemi çözer:

```
business logic reuse
```

Örnek:

```
create\_user
```

Kullanılabilir:

```
API  
admin panel  
worker  
CLI
```

Business logic HTTP'den bağımsız olur.

---

# 20️⃣ Repository neden var?

Repository şu problemi çözer:

```
DB bağımlılığı
```

Örnek:

Bugün:

```
PostgreSQL
```

Yarın:

```
DynamoDB
```

Service değişmez.

---

# 21️⃣ Domain layer neden var?

Domain layer:

```
business model
```

Örnek:

```
User  
Invoice  
Order
```

Bu layer:

-   framework bağımsızdır
    
-   DB bağımsızdır
    

---

# 22️⃣ Enterprise mimaride dependency yönü

Kritik kural:

```
outer layer → inner layer
```

Yani:

```
router → service → domain
```

ama:

```
domain → fastapi
```

olamaz.

---

# 23️⃣ Bu mimari neden ölçeklenebilir?

Çünkü modülerdir.

Yeni feature:

```
modules/payment  
modules/invoice  
modules/analytics
```

Eklenir.

Kod bozulmaz.

---

# 24️⃣ Real production FastAPI stack

Gerçek hayatta sık görülen stack:

```
Cloudflare  
↓  
Load balancer  
↓  
Nginx  
↓  
Gunicorn  
↓  
Uvicorn workers  
↓  
FastAPI  
↓  
Redis  
↓  
Postgres  
↓  
Celery workers
```

---

# 25️⃣ Senior engineer neye bakar?

Bir backend mimarisini değerlendirirken:

1️⃣ failure mode nedir  
2️⃣ scaling strategy nedir  
3️⃣ latency nerede oluşur  
4️⃣ bottleneck nerede  
5️⃣ observability var mı

---

# 26️⃣ En kritik production prensibi

Şudur:

> API **stateless** olmalıdır.

Bu sayede:

```
container kill  
container restart  
horizontal scale
```

sorunsuz olur.

---

# 27️⃣ Bu mimarinin gerçek amacı

Asıl amaç:

| hedef | nasıl |
| --- | --- |
| yüksek trafik | horizontal scaling |
| hata toleransı | process manager |
| yüksek performans | async IO |
| uzun işlemler | worker queue |
| maintainability | layered architecture |

---
