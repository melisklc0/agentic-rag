# Kurumsal API standardı kurmak

Soru şu:

> “Bir API’yi production’da nasıl tasarlarız ki; okunabilir, sürdürülebilir, gözlemlenebilir, test edilebilir ve hata anında kontrollü davransın?”

OpenAI tarafında da resmi dokümantasyon mantığı buna çok benzer: endpoint’ler açık tanımlanır, request/response şemaları nettir, hata bilgisi yapılandırılmıştır, rate-limit ve request-id gibi operasyonel bilgiler önemlidir. OpenAI ayrıca yeni projelerde Responses API’yi öneriyor; resmi API referansı endpoint, parametre ve response yapılarının merkezi kaynak olarak kullanılmasını sağlıyor. Production troubleshooting için de `x-request-id` ve rate-limit header’larının loglanmasını öneriyor. [OpenAI Platform+1](https://platform.openai.com/docs/api-reference/chat/completions?utm_source=chatgpt.com)

Şimdi bunu sana “OpenAI seviyesinde düşünerek ama FastAPI üzerinde uygulanabilir şekilde” anlatayım.

---

# 1) Aslında amaç ne?

Bu yapının amacı 6 şeydir:

## A. API’nin kendini anlatabilmesi

API’yi kullanan frontend, mobile, başka backend veya partner ekip şu soruların cevabını hemen bulmalı:

-   Bu servis ne işe yarıyor?
    
-   Hangi endpoint var?
    
-   Hangi input bekliyor?
    
-   Hangi output dönüyor?
    
-   Hangi hata kodlarını üretiyor?
    

Bunun için:

-   OpenAPI metadata
    
-   `/docs`
    
-   response model’leri
    
-   error model’leri
    

gerekir.

---

## B. Hata anında sistemin “kontrollü” kalması

Production’da en kötü şeylerden biri şudur:

-   exception fırlar
    
-   stack trace dökülür
    
-   response standardı bozulur
    
-   frontend ne geldiğini anlayamaz
    
-   log korelasyonu kaybolur
    

Kurumsal sistemde bunun yerine şunu istersin:

```
JSON

{  
  "success": false,  
  "error": {  
    "code": "DB\_01",  
    "message": "Database connection failed",  
    "details": null  
  },  
  "request\_id": "8d6b3d84-6a41-4baf-b9b0-7d37e9ecf7f3"  
}
```

Yani:

-   sistem çökmüyor
    
-   istemci tutarlı cevap alıyor
    
-   log ile response eşleşiyor
    
-   destek ekibi request’i takip edebiliyor
    

Bu mantık, OpenAI’nin request id ve yapılandırılmış hata yaklaşımıyla da uyumludur. [OpenAI Platform+1](https://platform.openai.com/docs/api-reference/chat/completions?utm_source=chatgpt.com)

---

## C. Domain hata yönetimi

Her hata aynı değildir.

Örnek:

-   dosya parse edilemedi
    
-   veritabanı bağlantısı koptu
    
-   kullanıcı yetkisiz
    
-   dış servis timeout verdi
    
-   validation hatası oldu
    

Bunların hepsine düz `500 Internal Server Error` dönmek kötü pratiktir.

Doğru yaklaşım:

-   **domain exception**
    
-   **infra exception**
    
-   **client error**
    
-   **unexpected error**
    

ayrımı yapmaktır.

---

## D. Geliştirici deneyimi

Senior mühendis açısından iyi API sadece çalışan API değildir.  
Aynı zamanda yeni gelen bir developer’ın 10 dakikada okuyup anlayabildiği API’dir.

Bu yüzden:

-   `main.py` sadece uygulama kurar
    
-   `exceptions.py` hata sınıflarını taşır
    
-   `handlers.py` global handler’ları içerir
    
-   `schemas/` response modellerini içerir
    
-   `routers/` endpoint’leri içerir
    

---

## E. Gözlemlenebilirlik

API response’u kadar log da önemlidir.

Her request için idealde:

-   request\_id
    
-   path
    
-   method
    
-   status\_code
    
-   latency
    
-   error\_code
    

kayıt altına alınır.

---

## F. Sözleşme tabanlı geliştirme

API bir “kod parçası” değil, bir **kontrat**tır.

Frontend/backend arasındaki sözleşme:

-   başarı cevabı nasıl?
    
-   hata cevabı nasıl?
    
-   alanlar zorunlu mu?
    
-   null olabilir mi?
    

Bu yüzden response formatı her yerde standart olmalıdır.

---

# 2) “OpenAI standartlarında API” derken neyi kastetmeliyiz?

Bunu birebir “OpenAI’nin aynısı” gibi değil, şu prensipler olarak okumak daha doğru:

## OpenAI tarzı güçlü API prensipleri

-   iyi tanımlanmış endpoint yapısı
    
-   açık request/response şemaları
    
-   standardize hata nesnesi
    
-   request tracing (`x-request-id`)
    
-   rate limit bilgileri
    
-   resmi dokümantasyonla uyumlu davranış
    
-   sürümlenebilir yapı
    
-   istemcinin güvenle parse edebileceği response sözleşmesi
    

OpenAI’nin resmi API referansı endpoint, parametre ve response tanımlarını merkezi biçimde sunuyor; ayrıca rate-limit header’ları ve request-id bilgisinin üretimde loglanmasını özellikle öneriyor. [OpenAI Platform+1](https://platform.openai.com/docs/api-reference/chat/completions?utm_source=chatgpt.com)

Senin projene çevrilmiş hali şu olur:

> “Benim API’m kendi içinde bir platform API gibi davranmalı.”

---

# 3) Senin verdiğin task’ın gerçek anlamı

Şu task:

> Asenkron API Kurulumu ve Global Exception Handling

aslında aşağıdaki alt parçaları içeriyor:

## Parça 1 — Uygulama kimliğinin tanımlanması

`src/main.py` içinde:

-   title
    
-   description
    
-   version
    
-   docs\_url
    
-   redoc\_url
    
-   openapi\_tags
    

tanımlanır.

Bu, API’nin dış dünyaya “Ben neyim?” demesidir.

---

## Parça 2 — Hata sınıflarının modellenmesi

`src/core/exceptions.py`

Burada sistemin iş diline ait hata sınıfları tanımlanır.

Örnek:

-   `DocumentParseError`
    
-   `DatabaseConnectionError`
    
-   `ExternalServiceTimeoutError`
    
-   `ResourceNotFoundError`
    

Bu katman çok önemli.  
Çünkü burada exception sadece Python exception değil, aynı zamanda **iş anlamı taşıyan bir olay** olur.

---

## Parça 3 — Global exception handler

FastAPI’de bütün hataları merkezi yakalarsın.

Bu sayede:

-   endpoint içinde her yerde try/except yazmazsın
    
-   tekrar azalır
    
-   response formatı standart kalır
    

---

## Parça 4 — Standart error response şeması

Tek format kullanırsın.

Örnek:

```
JSON

{  
  "success": false,  
  "error": {  
    "code": "DOC\_01",  
    "message": "Document could not be parsed",  
    "details": {  
      "filename": "contract.pdf"  
    }  
  },  
  "request\_id": "..."  
}
```

---

## Parça 5 — Beklenmeyen hatalar için fallback

Her şey domain exception olmayabilir.

Örneğin:

-   bug
    
-   NoneType error
    
-   yanlış import
    
-   runtime beklenmedik exception
    

Bu durumda da sistem kontrollü response vermeli.

---

# 4) Hangi bilgi nerede yazar?

Bu soru çok önemli. Senior seviyede proje düzeni tam burada başlar.

Ben sana ideal bir klasör yapısı vereyim:

```
Bash

src/  
├── main.py  
├── api/  
│   ├── routers/  
│   │   └── documents.py  
│   └── deps.py  
├── core/  
│   ├── config.py  
│   ├── exceptions.py  
│   ├── exception\_handlers.py  
│   └── logging.py  
├── schemas/  
│   ├── common.py  
│   ├── error.py  
│   └── document.py  
├── services/  
│   └── document\_service.py  
└── db/  
    └── session.py
```

Şimdi tek tek:

## `src/main.py`

Burada şunlar olur:

-   FastAPI app oluşturma
    
-   metadata
    
-   router include etme
    
-   middleware ekleme
    
-   exception handler register etme
    
-   startup/shutdown event
    

**Amaç:** uygulamanın giriş noktası

---

## `src/core/exceptions.py`

Burada şunlar olur:

-   custom exception class’ları
    
-   error\_code
    
-   default\_message
    
-   http\_status
    

**Amaç:** sistemin hata sözlüğü

---

## `src/core/exception_handlers.py`

Burada şunlar olur:

-   custom exception handler’lar
    
-   `RequestValidationError` handler
    
-   `HTTPException` handler
    
-   generic `Exception` handler
    

**Amaç:** her hatayı standardize response’a çevirmek

---

## `src/schemas/error.py`

Burada şunlar olur:

-   Pydantic error response modelleri
    

**Amaç:** response contract tanımı

---

## `src/services/...`

Burada iş mantığı olur.

Mesela:

-   parse document
    
-   validate file
    
-   save metadata
    
-   call OCR service
    

**Amaç:** business logic

---

## `src/api/routers/...`

Burada endpoint olur.

Örnek:

-   `POST /documents/parse`
    
-   `GET /documents/{id}`
    

**Amaç:** HTTP katmanı

---

# 5) Neden asenkron?

FastAPI’de async kullanmak özellikle şu durumlarda mantıklıdır:

-   DB sorguları async ise
    
-   dış API çağrısı varsa
    
-   dosya okuma/yükleme varsa
    
-   I/O ağırlıklı iş varsa
    

Ama kritik nokta şu:

> Her şeyi `async` yapmak tek başına “performanslı” demek değildir.

Eğer içeride CPU-heavy iş yapıyorsan:

-   büyük PDF parse
    
-   OCR
    
-   embedding üretimi
    
-   büyük transform
    

o zaman async yetmez; worker/celery/rq/background queue gerekir.

Yani:

## Async iyi olduğu yerler

-   ağ çağrısı
    
-   DB
    
-   dosya I/O
    
-   external API
    

## Async’in yetmediği yerler

-   ağır CPU işlemleri
    
-   uzun parsing pipeline
    
-   model inference
    
-   video/image processing
    

Senior bakış açısı:  
**API hızlı cevap verir, ağır işleri background worker yapar.**

---

# 6) Senin verdiğin task için production-grade tasarım

Aşağıda bunu temiz bir şekilde kuruyorum.

---

## A. Error schema

### `src/schemas/error.py`

```
Python

Çalıştır

from typing import Any, Optional  
from pydantic import BaseModel, Field  
  
  
class ErrorDetail(BaseModel):  
    code: str \= Field(..., examples\=\["DB\_01"\])  
    message: str \= Field(..., examples\=\["Database connection failed"\])  
    details: Optional\[Any\] \= Field(default\=None)  
  
  
class ErrorResponse(BaseModel):  
    success: bool \= Field(default\=False)  
    error: ErrorDetail  
    request\_id: Optional\[str\] \= None
```

### Neden burada?

Çünkü response sözleşmesini burada tanımlarsın.  
Frontend bu modeli bilir.

---

## B. Custom exception hierarchy

### `src/core/exceptions.py`

```
Python

Çalıştır

from typing import Any, Optional  
  
  
class AppException(Exception):  
    def \_\_init\_\_(  
        self,  
        code: str,  
        message: str,  
        status\_code: int \= 400,  
        details: Optional\[Any\] \= None,  
    ):  
        self.code \= code  
        self.message \= message  
        self.status\_code \= status\_code  
        self.details \= details  
        super().\_\_init\_\_(message)  
  
  
class DocumentParseError(AppException):  
    def \_\_init\_\_(self, details: Optional\[Any\] \= None):  
        super().\_\_init\_\_(  
            code\="DOC\_01",  
            message\="Document could not be parsed",  
            status\_code\=422,  
            details\=details,  
        )  
  
  
class DatabaseConnectionError(AppException):  
    def \_\_init\_\_(self, details: Optional\[Any\] \= None):  
        super().\_\_init\_\_(  
            code\="DB\_01",  
            message\="Database connection failed",  
            status\_code\=503,  
            details\=details,  
        )  
  
  
class ResourceNotFoundError(AppException):  
    def \_\_init\_\_(self, resource: str, details: Optional\[Any\] \= None):  
        super().\_\_init\_\_(  
            code\="RES\_404",  
            message\=f"{resource} not found",  
            status\_code\=404,  
            details\=details,  
        )
```

---

# 7) Buradaki mantık ne?

Burada çok önemli bir tasarım kararı var:

## Kötü yaklaşım

```
Python

Çalıştır

raise Exception("db bozuldu")
```

Bu kötü. Çünkü:

-   kod yok
    
-   status yok
    
-   client için anlamlı değil
    
-   merkezi yönetilemiyor
    

## Doğru yaklaşım

```
Python

Çalıştır

raise DatabaseConnectionError(details\={"db\_host": "postgres"})
```

Bu iyi. Çünkü:

-   domain anlamı var
    
-   operasyonel takip kolay
    
-   response standardı bozulmuyor
    

---

# 8) Global exception handling

### `src/core/exception_handlers.py`

```
Python

Çalıştır

import uuid  
import logging  
  
from fastapi import Request, HTTPException  
from fastapi.exceptions import RequestValidationError  
from fastapi.responses import JSONResponse  
  
from src.core.exceptions import AppException  
  
logger \= logging.getLogger(\_\_name\_\_)  
  
  
def get\_request\_id(request: Request) -> str:  
    return getattr(request.state, "request\_id", str(uuid.uuid4()))  
  
  
async def app\_exception\_handler(request: Request, exc: AppException):  
    request\_id \= get\_request\_id(request)  
  
    logger.warning(  
        "Application exception occurred",  
        extra\={  
            "request\_id": request\_id,  
            "path": request.url.path,  
            "method": request.method,  
            "error\_code": exc.code,  
            "details": exc.details,  
        },  
    )  
  
    return JSONResponse(  
        status\_code\=exc.status\_code,  
        content\={  
            "success": False,  
            "error": {  
                "code": exc.code,  
                "message": exc.message,  
                "details": exc.details,  
            },  
            "request\_id": request\_id,  
        },  
    )  
  
  
async def validation\_exception\_handler(request: Request, exc: RequestValidationError):  
    request\_id \= get\_request\_id(request)  
  
    logger.warning(  
        "Validation exception occurred",  
        extra\={  
            "request\_id": request\_id,  
            "path": request.url.path,  
            "method": request.method,  
            "errors": exc.errors(),  
        },  
    )  
  
    return JSONResponse(  
        status\_code\=422,  
        content\={  
            "success": False,  
            "error": {  
                "code": "REQ\_422",  
                "message": "Request validation failed",  
                "details": exc.errors(),  
            },  
            "request\_id": request\_id,  
        },  
    )  
  
  
async def http\_exception\_handler(request: Request, exc: HTTPException):  
    request\_id \= get\_request\_id(request)  
  
    return JSONResponse(  
        status\_code\=exc.status\_code,  
        content\={  
            "success": False,  
            "error": {  
                "code": f"HTTP\_{exc.status\_code}",  
                "message": str(exc.detail),  
                "details": None,  
            },  
            "request\_id": request\_id,  
        },  
    )  
  
  
async def unhandled\_exception\_handler(request: Request, exc: Exception):  
    request\_id \= get\_request\_id(request)  
  
    logger.exception(  
        "Unhandled exception occurred",  
        extra\={  
            "request\_id": request\_id,  
            "path": request.url.path,  
            "method": request.method,  
        },  
    )  
  
    return JSONResponse(  
        status\_code\=500,  
        content\={  
            "success": False,  
            "error": {  
                "code": "SRV\_500",  
                "message": "An unexpected server error occurred",  
                "details": None,  
            },  
            "request\_id": request\_id,  
        },  
    )
```

---

# 9) Neden 4 farklı handler var?

Çünkü her hata türünün anlamı farklıdır:

## `AppException`

Senin sistemine ait kontrollü hata

## `RequestValidationError`

Pydantic/FastAPI request body/query/path validation hatası

## `HTTPException`

FastAPI/Starlette’nin HTTP odaklı standard exception’ı

## `Exception`

Yakalanmamış tüm beklenmedik hatalar

Bu ayrım çok profesyoneldir.  
Çünkü hem business error hem framework error hem de unknown error ayrı ele alınır.

---

# 10) Request ID middleware

OpenAI resmi dokümanlarında request-id loglamanın troubleshooting için önemli olduğu açıkça belirtiliyor. Benzer şekilde kendi API’nda da request id üretmek çok doğru pratiktir. [OpenAI Platform](https://platform.openai.com/docs/api-reference/chat/completions?utm_source=chatgpt.com)

### `src/main.py` içine middleware

```
Python

Çalıştır

import uuid  
from contextlib import asynccontextmanager  
  
from fastapi import FastAPI, Request  
from fastapi.responses import JSONResponse  
  
from src.core.exceptions import AppException  
from src.core.exception\_handlers import (  
    app\_exception\_handler,  
    validation\_exception\_handler,  
    http\_exception\_handler,  
    unhandled\_exception\_handler,  
)  
from fastapi.exceptions import RequestValidationError  
from fastapi import HTTPException  
  
  
@asynccontextmanager  
async def lifespan(app: FastAPI):  
    \# startup  
    print("Application is starting...")  
    yield  
    \# shutdown  
    print("Application is shutting down...")  
  
  
app \= FastAPI(  
    title\="Enterprise Document Processing API",  
    description\="""  
    Kurumsal seviyede doküman işleme ve veri servisleri sunan API.  
  
    Özellikler:  
    - Asenkron endpoint desteği  
    - Global exception handling  
    - Standart JSON hata formatı  
    - OpenAPI dokümantasyonu  
    - Request tracing  
    """,  
    version\="1.0.0",  
    docs\_url\="/docs",  
    redoc\_url\="/redoc",  
    openapi\_tags\=\[  
        {"name": "Health", "description": "Servis sağlık kontrolü endpointleri"},  
        {"name": "Documents", "description": "Doküman işleme işlemleri"},  
    \],  
    lifespan\=lifespan,  
)  
  
  
@app.middleware("http")  
async def add\_request\_id\_middleware(request: Request, call\_next):  
    request.state.request\_id \= str(uuid.uuid4())  
    response \= await call\_next(request)  
    response.headers\["X-Request-Id"\] \= request.state.request\_id  
    return response  
  
  
app.add\_exception\_handler(AppException, app\_exception\_handler)  
app.add\_exception\_handler(RequestValidationError, validation\_exception\_handler)  
app.add\_exception\_handler(HTTPException, http\_exception\_handler)  
app.add\_exception\_handler(Exception, unhandled\_exception\_handler)
```

---

# 11) `main.py` içindeki metadata ne işe yarar?

Burada yazdığın bilgiler `/docs` ve OpenAPI şemasında görünür.

## `title`

API adı

## `description`

API’nin ne yaptığı

## `version`

sürüm

## `docs_url`

Swagger UI adresi

## `redoc_url`

ReDoc adresi

## `openapi_tags`

endpoint gruplarının anlamlı görünmesi

Yani bu alanlar “süs” değildir.  
Bunlar API’nin dış dünyadaki kimliğidir.

OpenAI’nin resmi API referansı da aynı mantıkla endpoint, parametre ve response tanımlarını merkezi biçimde yayınlar. [OpenAI Platform](https://platform.openai.com/docs/api-reference/realtime-beta-sessions?ref=aarondevelops.com&utm_source=chatgpt.com)

---

# 12) Örnek router

### `src/api/routers/documents.py`

```
Python

Çalıştır

from fastapi import APIRouter  
from pydantic import BaseModel  
  
from src.core.exceptions import DocumentParseError, DatabaseConnectionError  
  
router \= APIRouter(prefix\="/documents", tags\=\["Documents"\])  
  
  
class DocumentParseRequest(BaseModel):  
    filename: str  
    content: str  
  
  
@router.post("/parse")  
async def parse\_document(payload: DocumentParseRequest):  
    if payload.filename.endswith(".broken"):  
        raise DocumentParseError(details\={"filename": payload.filename})  
  
    if payload.filename \== "db\_fail.pdf":  
        raise DatabaseConnectionError(details\={"service": "postgres"})  
  
    return {  
        "success": True,  
        "data": {  
            "filename": payload.filename,  
            "status": "parsed",  
        },  
    }
```

Ve bunu `main.py` içine:

```
Python

Çalıştır

from src.api.routers.documents import router as documents\_router  
  
app.include\_router(documents\_router)
```

eklarsın.

---

# 13) Bilerek hata ürettik, ne olacak?

İstek:

```
http

POST /documents/parse  
Content-Type: application/json
```

Body:

```
JSON

{  
  "filename": "db\_fail.pdf",  
  "content": "dummy"  
}
```

Response:

```
JSON

{  
  "success": false,  
  "error": {  
    "code": "DB\_01",  
    "message": "Database connection failed",  
    "details": {  
      "service": "postgres"  
    }  
  },  
  "request\_id": "6d59f1d7-f0a8-4a0c-8f93-66d222f112c1"  
}
```

Sistem ne yapmış oldu?

-   çökmedi
    
-   stack trace client’a saçılmadı
    
-   standart sözleşmede cevap verdi
    
-   request izlenebilir oldu
    

İşte DoD tam budur.

---

# 14) Senin verdiğin DoD’yi daha profesyonel hale çevireyim

Senin DoD iyi ama biraz daha enterprise hale şöyle yazılır:

## Definition of Done

-   FastAPI uygulaması `title`, `description`, `version`, `tags` ile OpenAPI uyumlu şekilde tanımlanmış olmalı.
    
-   `/docs` ve `/redoc` erişilebilir olmalı.
    
-   Tüm custom exception’lar `src/core/exceptions.py` içinde merkezi olarak tanımlanmış olmalı.
    
-   `AppException` taban sınıfı üzerinden sistem içi exception standardı kurulmuş olmalı.
    
-   `AppException`, `RequestValidationError`, `HTTPException` ve generic `Exception` için global handler tanımlanmış olmalı.
    
-   Tüm hata yanıtları aynı JSON sözleşmesine uymalı.
    
-   Her response’a `X-Request-Id` header’ı eklenmeli.
    
-   Beklenmeyen hatalarda sistem 500 dönmeli ancak proses çökmemeli.
    
-   Hata anları loglanmalı ve loglarda `request_id` ile `error_code` bulunmalı.
    

Bu artık staj görevinden çıkıp gerçek production standardına yaklaşır.

---

# 15) Hata kodu standardı nasıl olmalı?

Bu da çok önemli.

Ben sana önerilen pattern vereyim:

## Domain bazlı kodlar

-   `DOC_01` → document parse error
    
-   `DOC_02` → unsupported document type
    
-   `DB_01` → db connection failed
    
-   `DB_02` → query timeout
    
-   `AUTH_01` → invalid credentials
    
-   `AUTH_02` → token expired
    
-   `REQ_422` → validation failed
    
-   `SRV_500` → unexpected internal server error
    

## Neden önemli?

Çünkü frontend metni değil **error code**’u parse etmelidir.

Yanlış:

-   `"message": "veritabanı bozuldu"`
    

Doğru:

-   `"code": "DB_01"`
    

Message değişebilir, localization olabilir.  
Ama code sabit kalır.

---

# 16) `message`, `details`, `code` farkı ne?

Bu da çok karıştırılır.

## `code`

makine dostu sabit anahtar

## `message`

insan dostu özet açıklama

## `details`

ek bağlam

Örnek:

```
JSON

{  
  "code": "DOC\_01",  
  "message": "Document could not be parsed",  
  "details": {  
    "filename": "invoice.pdf",  
    "reason": "invalid pdf structure"  
  }  
}
```

---

# 17) 500 dönüp “çökmemek” ne demek?

Buradaki “çökmemek” şunu ifade eder:

-   uygulama process’i tamamen kapanmasın
    
-   uvicorn worker yok olmasın
    
-   request exception yüzünden servis unavailable hale gelmesin
    
-   response client’a kontrolsüz stack trace yerine düzenli JSON dönsün
    

Ama dikkat:  
Bir request hata aldıysa o request başarısız olabilir.  
Bu normaldir. Mesele o request’in başarısız olurken sistemi dağıtmamasıdır.

---

# 18) OpenAPI standardına uygun başlık/açıklama nasıl yazılır?

Kötü örnek:

```
Python

Çalıştır

app \= FastAPI(title\="My API")
```

Yetersiz.

Daha iyi örnek:

```
Python

Çalıştır

app \= FastAPI(  
    title\="Enterprise Document Processing API",  
    description\="""  
    This API provides asynchronous document ingestion, parsing, and metadata processing capabilities.  
  
    Error Handling:  
    - Standardized JSON error responses  
    - Global exception handling  
    - Request tracing with request IDs  
  
    Intended Consumers:  
    - Frontend applications  
    - Internal backend services  
    - Automation pipelines  
    """,  
    version\="1.0.0",  
)
```

Burada şu bilgiler yazılır:

-   servis ne yapıyor
    
-   hedef kullanıcı kim
    
-   kritik davranışlar neler
    
-   hata yaklaşımı nasıl
    
-   varsa auth bilgisi
    
-   varsa rate limit bilgisi
    

---

# 19) Bence burada eksik olan şeyler

Senin örneğin iyi ama production için 5 kritik parça daha eklenmeli:

## 1\. Response envelope standardı

Sadece hata değil başarı cevabı da standart olmalı.

Örnek:

```
JSON

{  
  "success": true,  
  "data": {...},  
  "meta": null,  
  "request\_id": "..."  
}
```

---

## 2\. Logging standardı

Sadece JSON dönmek yetmez. Log şart.

---

## 3\. Validation error standardizasyonu

FastAPI default validation response’u da tek formata indirilmeli.

---

## 4\. Request ID

Troubleshooting için kritik.

OpenAI de request-id loglamayı öneriyor. [OpenAI Platform](https://platform.openai.com/docs/api-reference/chat/completions?utm_source=chatgpt.com)

---

## 5\. Versioning

İleride `/api/v1/...` yaklaşımı kullanılmalı.

Örnek:

-   `/api/v1/documents/parse`
    

---

# 20) Sana önerdiğim final proje standardı

Ben olsam bunu şöyle kurarım:

## Dosya yapısı

```
Bash

src/  
├── main.py  
├── api/  
│   └── routers/  
│       └── documents.py  
├── core/  
│   ├── exceptions.py  
│   ├── exception\_handlers.py  
│   └── config.py  
├── schemas/  
│   ├── error.py  
│   └── response.py  
└── services/  
    └── document\_service.py
```

## Error response standardı

```
JSON

{  
  "success": false,  
  "error": {  
    "code": "DB\_01",  
    "message": "Database connection failed",  
    "details": null  
  },  
  "request\_id": "..."  
}
```

## Success response standardı

```
JSON

{  
  "success": true,  
  "data": {},  
  "meta": null,  
  "request\_id": "..."  
}
```

## Handler katmanları

-   AppException
    
-   RequestValidationError
    
-   HTTPException
    
-   Exception
    

## Middleware

-   request id
    
-   logging
    
-   timing
    

---

# 21) Kısacası bu task ne işe yarar?

Bu task’ın gerçek faydası şudur:

-   API profesyonel görünür
    
-   frontend/backend entegrasyonu kolaylaşır
    
-   hata ayıklama kolaylaşır
    
-   log korelasyonu mümkün olur
    
-   bakım maliyeti düşer
    
-   ekip standardı oluşur
    
-   yeni endpoint yazmak hızlanır
    

Yani bu task “küçük bir setup işi” değil.  
Bu task, API’nin **omurgasıdır**.

---

# 22) Sana senior notu

Birçok junior geliştirici exception handling’i “hata mesajı dönmek” sanır.  
Senior mühendis şunu bilir:

> Exception handling aslında sistemin hata anındaki davranış sözleşmesidir.

Bu yüzden bu yapı:

-   sadece backend konusu değil
    
-   aynı zamanda DX, ops, observability ve platform design konusudur.
    

---

# 23) Sana önerdiğim görev tanımının zenginleştirilmiş hali

Bunu ekibine böyle yazabilirsin:

### Asenkron API Kurulumu ve Global Exception Handling

**Amaç:**  
FastAPI tabanlı servisin kurumsal seviyede standartlaştırılması; uygulamanın OpenAPI uyumlu metadata ile kendini tanımlaması, tüm hata senaryolarında kontrollü ve standardize JSON response üretmesi, beklenmeyen exception’larda dahi servis bütünlüğünün korunması.

**Kapsam:**

-   `src/main.py` içinde FastAPI uygulamasının `title`, `description`, `version`, `docs_url`, `redoc_url`, `tags` ile tanımlanması
    
-   `src/core/exceptions.py` içinde `AppException` taban sınıfı ve domain-specific exception’ların oluşturulması
    
-   `src/core/exception_handlers.py` içinde global exception handler’ların tanımlanması
    
-   request bazlı `request_id` üretimi ve response header’a eklenmesi
    
-   validation, framework ve unknown exception’ların tek error contract altında toplanması
    
-   `/docs` üzerinden erişilebilir API dokümantasyonunun sağlanması
    

**Beklenen Çıktı:**

-   API standardize hata sözleşmesi ile yanıt vermeli
    
-   frontend tüm hata cevaplarını tek formatta parse edebilmeli
    
-   loglar request bazlı izlenebilir olmalı
    
-   servis beklenmeyen exception’larda proses seviyesinde çökmeden 500 dönebilmeli
    

**DoD:**

-   `/docs` ve `/redoc` aktif
    
-   Bilerek fırlatılan `DocumentParseError` uygun status code ve JSON body ile dönüyor
    
-   Bilerek fırlatılan `DatabaseConnectionError` uygun status code ve JSON body ile dönüyor
    
-   Validation hataları standart JSON formatında dönüyor
    
-   Beklenmeyen exception’lar `SRV_500` ile dönüyor
    
-   Her response’ta `X-Request-Id` bulunuyor
    

---

İstersen bir sonraki mesajda sana bunun üzerine doğrudan **tam production-ready FastAPI starter template** çıkarayım: `main.py`, `exceptions.py`, `exception_handlers.py`, `response.py`, `router`, `test` dosyalarıyla birlikte.