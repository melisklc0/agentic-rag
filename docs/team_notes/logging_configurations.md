# Python Logging: Üretim Seviyesinde Rehber

Bu doküman, Python `logging` modülü için gerçek hayatta kullanılan bir yaklaşım sunar. Hedef; sadece log yazdırmak değil, izlenebilirlik (observability), hata analizi, performans, güvenlik ve operasyonel bakım ihtiyaçlarını karşılayan bir sistem kurmaktır.

- `Logger`, `Handler`, `Formatter`, `Filter`, hiyerarşi ve propagation mantığı
- `dictConfig` ile açık, merkezi ve ölçeklendirilebilir konfigürasyon
- Dosyaya yazarken metin yerine JSON Lines (`.jsonl`) tercih etme
- `QueueHandler` ile ana iş parçacığını (main thread) I/O blokajından kurtarma
- Uygulama (application) ve kütüphane (library) loglama sorumluluklarının ayrımı
## 1) Neden Logging?

`print()` geçici debug için yararlı olabilir; fakat aşağıdakileri sağlamaz:
- Standart log seviyeleri (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- Çoklu hedefe çıkış (stdout, stderr, dosya, uzak servis)
- Tutarlı format
- Hata ve stack trace kaydı
- Ortam bazlı konfigürasyon yönetimi

Üretim seviyesinde sistemlerde loglar:
- Olay zinciri takibi (incident debugging)
- Denetim izi (audit trail)
- SLA/SLO takibi
- Güvenlik analizi
için kritik rol oynar.

## 2) Zihinsel Model: Tam Resim

Bir log akışının adımları:
1. Kodunuz bir `logger.info(...)` ya da `logger.error(...)` çağırır.
2. Bir `LogRecord` oluşur.
3. Logger seviyesi ve logger filtreleri uygulanır.
4. Kayıt, logger'ın handler'larına gider.
5. Her handler kendi seviye/filtre kontrolden geçirir.
6. Formatter, `LogRecord` nesnesini metne çevirir.
7. Handler ilgili hedefe yazar (konsol, dosya, vb).
8. `propagate=True` ise kayıt üst logger'lara (ebeveyn) doğru yayılır.

Kritik ayrım:
- Logger bir kaydı elerse, akışın geri kalanı durur.
- Bir handler kaydı elerse, sadece o handler yazmaz; diğer handler'lar çalışmaya devam eder.

## 3) Temel Bileşenler

### 3.1 Logger

Kodunuzdan kullandığınız ana giriş noktası.

```python
import logging

logger = logging.getLogger("my_app.api")
logger.info("API başlatıldı")
```

En iyi pratik:
- `logging.info(...)` gibi root helper fonksiyonları yerine adlandırılmış logger kullanın.
- Küçük/orta uygulamada bir ana uygulama logger'ı yeterli olabilir.
- Büyük uygulamada alt alanlara göre logger adları kullanın (`my_app.api`, `my_app.db`).

### 3.2 Log Seviyeleri

Python standart seviyeler:
- `DEBUG` (10)
- `INFO` (20)
- `WARNING` (30)
- `ERROR` (40)
- `CRITICAL` (50)
- `NOTSET` (0)

`NOTSET` logger seviyesinde "ilk üstte explicit seviye neyse onu miras al" davranışı verir.

### 3.3 Handler

Log kaydının "nereye" gideceğini belirler.

Sık kullanılanlar:
- `StreamHandler` (stdout/stderr)
- `FileHandler`
- `RotatingFileHandler`
- `QueueHandler` (asenkron/multithread çıkış altyapısı)

### 3.3.1 stdout ve stderr: Neden Ayrı Akışlar?

Üretimde konsol loglarını ikiye ayırmak güçlü bir pratiktir:
- `stdout`: normal operasyonel olaylar (`DEBUG`, `INFO`)
- `stderr`: problem sinyalleri (`WARNING`, `ERROR`, `CRITICAL`)

Bu ayrımın kazanımları:
- Container platformlarında (`docker`, `k8s`) hata akışı ayrı toplanabilir.
- Log router/agent tarafında farklı pipeline kurmak kolaylaşır.
- Uyarı/hata oranı gibi metrikler daha temiz hesaplanır.

Bu yaklaşımın tipik uygulaması şudur: `stdout` handler'ında `NonErrorFilter` kullanılarak `WARNING+` satırlar engellenir, `stderr` handler ise `WARNING` seviyesinden itibaren kayıt alır. Böylece duplicate oluşmaz.

### 3.4 Formatter

Kaydın "nasıl" görüneceğini belirler. Metin veya JSON formatı üretebilir.

### 3.5 Filter

Seviyeden daha ince kontrol için kullanılır. Mesajı kabul/red edebilir, hatta kaydı değiştirebilir.

## 4) `lastResort` ve Varsayılan Davranış

Logger hiyerarşisinde hiç handler bulunamazsa `lastResort` handler devreye girer:
- Konsola yazar
- Seviyesi `WARNING`
- Çok temel/formatlanmamış çıkış verir

Bu nedenle "hiç konfigürasyon yokken" sadece warning ve üstü görüyormuş gibi bir davranışla karşılaşırsınız.

## 5) Hiyerarşi ve Propagation

Logger adları nokta ile ağaç oluşturur:
- `my_app`
- `my_app.db`
- `my_app.db.query`

Varsayılan `propagate=True` olduğu için alt logger'da üretilen log üstlere taşınır.

### Önemli Tasarım Kararı

Çoğu uygulamada daha sağlam yaklaşım:
- Handler'ları root logger'da topla
- Çocuk logger'larda handler tanımlama
- `propagate=True` bırak

Avantajlar:
- 3. parti kütüphanelerden gelen loglar da aynı format/akıstan geçer
- Çift loglama ve dağınık konfigürasyon riski azalır

## 6) Neden `basicConfig` Yerine `dictConfig`?

`basicConfig` hızlı başlangıç için yeterli olabilir; ancak kompleks kurulumlarda yetersiz kalır.

`dictConfig` avantajları:
- Bileşenleri açıkça tanımlar (formatter/handler/filter/logger)
- Bakımı kolaydır
- JSON/YAML dosyasına taşınabilir
- Ortam bazlı override kolaylaşır

Aşağıdaki aşamalı akış, en sık kullanılan modern dönüşümü gösterir:

1) Sadece `stdout` ile başla:

```json
{
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        }
    },
    "loggers": {
        "root": {"level": "DEBUG", "handlers": ["stdout"]}
    }
}
```

2) `stderr` + dönen dosya ekle:

```json
{
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "stream": "ext://sys.stderr"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "filename": "logs/my_app.log",
            "maxBytes": 1000000,
            "backupCount": 5
        }
    },
    "loggers": {
        "root": {"level": "DEBUG", "handlers": ["stderr", "file"]}
    }
}
```

3) Kalıcı logları JSONL'e geçir:

```json
{
    "formatters": {
        "json": {
            "()": "mylogger.MyJSONFormatter",
            "fmt_keys": {
                "level": "levelname",
                "message": "message",
                "timestamp": "timestamp"
            }
        }
    },
    "handlers": {
        "file_json": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "logs/my_app.log.jsonl"
        }
    }
}
```

4) `stdout`/`stderr` ayrımını filter ile netleştir:

```json
{
    "filters": {
        "no_errors": {"()": "mylogger.NonErrorFilter"}
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["no_errors"]
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "level": "WARNING"
        }
    }
}
```

5) Non-blocking için queue katmanı ekle:

```json
{
    "handlers": {
        "queue_handler": {
            "class": "logging.handlers.QueueHandler",
            "handlers": ["stderr", "file_json"],
            "respect_handler_level": true
        }
    },
    "loggers": {
        "root": {"level": "DEBUG", "handlers": ["queue_handler"]}
    }
}
```

### 6.1 Üçüncü Parti Loglarını Kendi Formatına Alma (Override)

Uygulamada sık ihtiyaçlardan biri şudur: kütüphane logları da sizin `formatter` ve `handler` zincirinizden geçsin.

Temel prensip:
- Root logger üzerinde kendi handler/formatter yapınızı kurun.
- `disable_existing_loggers` değerini `false` bırakın.
- İlgili üçüncü parti logger'larda `propagate: true` kullanın.
- Kütüphane kendi handler'ını ekliyorsa, o logger için `handlers: []` ile temizleyin.

`dictConfig` ile seçici override örneği:

```json
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "json": {
            "()": "mylogger.MyJSONFormatter",
            "fmt_keys": {
                "level": "levelname",
                "message": "message",
                "timestamp": "timestamp",
                "logger": "name"
            }
        }
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "json",
            "stream": "ext://sys.stderr"
        },
        "file_json": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "logs/app.jsonl",
            "maxBytes": 5000000,
            "backupCount": 5
        }
    },
    "loggers": {
        "urllib3": {
            "level": "INFO",
            "handlers": [],
            "propagate": true
        },
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": [],
            "propagate": true
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["stderr", "file_json"]
    }
}
```

Bu yöntem en güvenli yaklaşımdır; sadece bildiğiniz logger isimlerini hedeflersiniz.

Daha agresif bir alternatif olarak, uygulama başlangıcında üçüncü parti logger handler'larını topluca temizleyebilirsiniz:

```python
import logging


def normalize_third_party_loggers() -> None:
    manager = logging.root.manager
    for name, obj in manager.loggerDict.items():
        if not isinstance(obj, logging.Logger):
            continue
        if name.startswith("my_app"):
            continue
        obj.handlers.clear()
        obj.propagate = True
```

Uyarı:
- Toplu temizleme, bazı kütüphanelerin bilerek eklediği özel handler davranışını devre dışı bırakır.
- Bu nedenle önce seçici override ile başlayın; gerçekten gerekirse toplu temizlemeye geçin.

### 6.2 Mantıklı mı? Ne Zaman Yapılmalı?

Kısa cevap: Evet, çoğu uygulamada mantıklıdır. Çünkü gözlemlenebilirlik tarafında en büyük problem, farklı format ve farklı akışlardan gelen parçalı log verisidir.

Ancak "her şeyi zorla tek kalıba sokmak" her zaman doğru değildir. Doğru karar için şu çerçeveyi kullanın:

Yapılması güçlü şekilde önerilen durumlar:
- Merkezi log toplama (ELK, Loki, Splunk, Datadog vb.) kullanıyorsanız
- Olay müdahalesi sırasında tek sorgu diliyle tüm logları taramak istiyorsanız
- Regülasyon veya denetim gereği tutarlı log şeması gerekiyorsa
- SRE/Platform ekibi servisler arası ortak dashboard ve alarm kuruyorsa

Daha dikkatli yaklaşılması gereken durumlar:
- Kütüphane, kendi handler'ı ile kritik bir davranış sağlıyorsa (ör. özel güvenlik/audit hattı)
- Geçici teşhis döneminde kütüphanenin ham çıktısına özellikle ihtiyaç varsa
- Eski sistemlerde beklenen formatlara sıkı bağımlılık varsa

Best practice önerileri:
1. Varsayılan yaklaşım olarak root üzerinde tek biçimlendirme standardı kullanın.
2. `disable_existing_loggers=false` bırakın; logger'ları kapatmayın, yönetin.
3. Önce seçici override yapın (`urllib3`, `sqlalchemy` gibi bilinen isimler).
4. Toplu temizleme yapacaksanız allowlist/denylist stratejisi kullanın.
5. `propagate=true` ve handler seviyesi kombinasyonunu birlikte doğrulayın.
6. Duplicate kontrolünü test edin: aynı olayın hem child hem root handler'da iki kez yazılmadığından emin olun.
7. JSONL şemanızı sabitleyin: `timestamp`, `level`, `logger`, `message`, `trace_id`, `request_id` gibi alanlar standardize olsun.
8. Üretimde log hacmini yönetin: seviye politikası, sampling ve rotasyon limitleri belirleyin.
9. Güvenlik filtresini merkezi uygulayın: PII/secret maskeleme override sürecinin parçası olsun.
10. Değişiklikleri kademeli açın: önce staging, sonra düşük riskli servisler, ardından tüm sistem.

Pratik karar kuralı:
- Amaç operasyonel tutarlılık ise: override edin.
- Amaç kütüphane davranışını olduğu gibi incelemekse: geçici olarak ham akışı koruyun.
- Kararsızsanız: seçici override + ölçüm yaklaşımıyla başlayın (en düşük risk).

## 7) Üretim İçin Başlangıç Konfigürasyonu: Root Üzerinde Merkezi Yapı

Aşağıda, gerçek dünyada sık kullanılan iki minimal örnek var.

### 7.1 Basit başlangıç (`stdout.json`)

```json
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "simple": {
            "format": "%(levelname)s: %(message)s"
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["stdout"]
        }
    }
}
```

### 7.2 Üretim yaklaşımı (`stderr-file.json`)

```json
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "simple": {
            "format": "%(levelname)s: %(message)s"
        },
        "detailed": {
            "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        }
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "simple",
            "stream": "ext://sys.stderr"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/my_app.log",
            "maxBytes": 10000,
            "backupCount": 3
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["stderr", "file"]
        }
    }
}
```

Notlar:
- `maxBytes=10000` eğitim amaçlı küçük verilmiş; gerçek sistemde birkaç MB ve üzeri tercih edilir.
- `datefmt` içinde timezone (`%z`) tutulması, dağıtık sistemlerde olay sıralaması için kritiktir.

## 8) Custom JSON Formatter (JSONL)

Kalıcı loglar için serbest metin yerine JSON Lines çok daha güçlüdür.

```python
import datetime as dt
import json
import logging
from typing import override

LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class MyJSONFormatter(logging.Formatter):
    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
    ):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord):
        always_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: msg_val
            if (msg_val := always_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val

        return message
```

Neden JSONL?
- Her satır bağımsız bir JSON nesnesidir.
- Arama/filtreleme/parsing otomasyonu kolaydır.
- Traceback gibi çok satırlı veriler bile tek kayıtta güvenle saklanır.

Önemli `dictConfig` detayı:
- `"class"` anahtarı, built-in arayüzlerle daha rahattır.
- Custom formatter için `"()": "mylogger.MyJSONFormatter"` kullanımı özellikle doğrudur.

## 9) `extra` ile İş Bağlamı (Context) Ekleme

En sade kullanım örneği:

```python
logger.debug("debug message", extra={"x": "hello"})
```

Gerçek projede bunu daha operasyonel hale getirin:

```python
logger.info(
    "Sipariş oluşturuldu",
    extra={
        "request_id": "req-9f2",
        "user_id": 42,
        "order_id": "ord-2026-0001",
        "component": "checkout",
    },
)
```

Bu alanlar JSON formatter tarafında otomatik alınıyorsa, sonradan korelasyon çok kolaylaşır.

## 10) Özel Filter Örneği

Sade bir filtre örneği:

```python
import logging
from typing import override


class NonErrorFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= logging.INFO
```

Bu filtre, `DEBUG` ve `INFO` kayıtlarını geçirir; `WARNING+` kayıtlarını engeller.

### 10.1 stdout/stderr ayrımına uygulama

Tipik `stdout`/`stderr` ayrımı yaklaşımı:
- `stdout` handler: `NonErrorFilter` ile sadece `DEBUG/INFO`
- `stderr` handler: `level=WARNING`

Böylece:
- normal akış terminalin standart çıktısında kalır,
- hata sinyalleri standart hata akışına düşer,
- aynı kaydın iki stream'e birden yazılması engellenir.

### 10.2 Güvenlik filtresi (ek öneri)

Üretimde ek olarak PII maskeleme filtresi de önerilir (e-posta, token, kimlik numarası gibi alanları redakte etmek için).

## 11) Non-Blocking Logging: `QueueHandler` + `QueueListener`

Web API, worker veya yüksek trafikli servislerde handler I/O'su ana akışı yavaşlatabilir. Çözüm:
- Üretici tarafta queue'ya yaz
- Arka planda listener thread gerçek handler'lara yazsın

### 11.1 `dictConfig` Parçası

```python
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
        "json": {
            "()": "mylogger.MyJSONFormatter",
            "fmt_keys": {
                "level": "levelname",
                "message": "message",
                "timestamp": "timestamp",
                "logger": "name",
                "module": "module",
                "function": "funcName",
                "line": "lineno",
                "thread_name": "threadName",
            },
        },
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "simple",
            "stream": "ext://sys.stderr",
        },
        "file_json": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "logs/my_app.log.jsonl",
            "maxBytes": 10000,
            "backupCount": 3,
        },
        "queue_handler": {
            "class": "logging.handlers.QueueHandler",
            "handlers": ["stderr", "file_json"],
            "respect_handler_level": True,
        },
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["queue_handler"],
        },
    },
}
```

### 11.2 Başlatma/Kapatma Akışı

`dictConfig` sonrası queue handler üzerinden listener başlatma stratejisi kurun. Bir uygulama iskeleti:

```python
import atexit
import json
import logging
import logging.config
import pathlib

logger = logging.getLogger("my_app")


def configure_logging() -> None:
    config_file = pathlib.Path("logging_configs/5-queued-stderr-json-file.json")
    with open(config_file) as f_in:
        config = json.load(f_in)
    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)
```

Kritik notlar:
- `respect_handler_level=true` verilmezse queue listener beklenmeyen şekilde fazla kayıt dağıtabilir.
- Bu yaklaşım Python 3.12+ için uygundur; daha düşük sürümlerde `QueueListener` bağlama işlemi manuel olabilir.

## 12) Uygulama ve Kütüphane Ayrımı

### Uygulama (Application) yazıyorsanız
- `dictConfig` veya eşdeğeri ile logging'i siz konfigüre edin.
- Handler/formatter/filter kararlarını uygulama sahibi olarak siz verin.

### Kütüphane (Library) yazıyorsanız
- Logger kullanın ama konfigürasyon yapmayın.
- Handler eklemeyin, root ayarı değiştirmeyin.
- Son kullanıcı uygulamasının konfigürasyonuna saygı duyun.

Bu ayrım, ekosistemde log kirliliği ve beklenmeyen davranışları ciddi biçimde azaltır.

Pratik özet:
- `main.py` bir uygulama giriş noktasıdır; burada `dictConfig` yapılması doğrudur.
- `mylogger.py` ise tekrar kullanılabilir formatter/filter kodunu içerir; bu ayrım temizdir.

## 13) Güvenlik ve Veri Koruma

Log güvenliği için temel kurallar:
- Parola, token, kart bilgisi, kimlik numarası gibi verileri loglamayın.
- Kullanıcı girdisini doğrudan loglamadan önce sanitize/mask uygulayın.
- PII/secret maskeleme için merkezi filter kullanın.
- Log retention süresini ve erişim izinlerini politika ile yönetin.

Ek not:
- `makeLogRecord` gibi API'ler gelen ham veriden `LogRecord` türetebilir. Dış kaynaktan gelen verileri doğrulamadan güvenilir log kaydı gibi işlemeyin.

## 14) Sık Hatalar ve Anti-Pattern'ler

- Her dosyada ayrı handler tanımlamak
- Çocuk logger'larda `propagate=False` verip fark etmeden log kaybetmek
- Hem çocukta hem root'ta aynı hedefe yazıp duplicate log üretmek
- Her log satırında `f"...{agir_hesap()}"` ile gereksiz maliyet yaratmak
- `exception` yerine sadece mesaj loglayıp stack trace kaybetmek

Doğru kullanım:

```python
logger.debug("Hesaplandı: %s", expensive_value)
```

Böylece mesaj formatlaması log seviyesi uygunsa yapılır.

## 15) Kurumsal Başlangıç Şablonu (Özet)

1. Tüm handler'ları root logger'da topla.
2. `disable_existing_loggers=False` ile 3. parti loglarını da gör.
3. Konsol için okunabilir text, kalıcı depolama için JSONL kullan.
4. `RotatingFileHandler` veya merkezi log platformu kullan.
5. `request_id`, `trace_id`, `user_id` gibi context alanlarını `extra` ile geç.
6. Performans kritikse `QueueHandler` kullan.
7. Uygulama konfigüre etsin, kütüphane konfigüre etmesin.
8. Hassas veri maskesini zorunlu kıl.

## 16) Aşamalı Uygulama Rehberi

Eğitim sırasında şu sırayı izlemek en verimlisidir:
1. Tek bir `stdout` handler ile minimum çalışan yapı kur.
2. `stderr` ve `RotatingFileHandler` ekleyerek akışları ayır.
3. Kalıcı dosya çıktısını JSONL formatına geçir.
4. Gerekirse `NonErrorFilter` benzeri filtre ile duplicate'i önle.
5. Trafik arttığında root'ta `QueueHandler` kullan ve listener yaşam döngüsünü yönet.

## 17) Kısa Üç Senaryo Örneği

### Senaryo A: Geliştirme Ortamı
- Root level: `DEBUG`
- Handler: `StreamHandler(sys.stdout)`
- Formatter: sade text

### Senaryo B: Üretim Ortamı
- Root level: `INFO`
- Handler-1: `StreamHandler(sys.stderr)` level `WARNING`
- Handler-2: `RotatingFileHandler` level `DEBUG`, formatter JSON

### Senaryo C: Yüksek Trafikli API
- Root level: `INFO`
- Tek root handler: `QueueHandler`
- Arka planda `QueueListener` ile çoklu hedefe dispatch

## 18) Hata Ayıklama Kontrol Listesi

Log görünmüyorsa:
1. Logger seviyesi beklediğinizden yüksek mi?
2. Handler seviyesi kaydı eliyor mu?
3. Filter `False` dönüyor mu?
4. `propagate=False` sebebiyle root'a ulaşmıyor mu?
5. `disable_existing_loggers=True` yanlışlıkla logger'ları kapattı mı?
6. Dosya handler path/izin hatası var mı?
7. `stdout`/`stderr` ayrımı beklediğiniz gibi mi, yoksa duplicate var mı?
8. Queue kullanıyorsanız listener gerçekten başlatıldı mı?

## 19) Sonuç

Python `logging`, ilk bakışta dağınık görünse de doğru modelle çok güçlü bir sistemdir. Üretim kalitesinde bir yaklaşım için ana prensipler:
- Konfigürasyonu merkezileştir (`dictConfig`)
- Handler'ları root'ta topla
- Kalıcı loglarda JSONL kullan
- `extra` ile bağlam zenginleştir
- Gerekirse queue tabanlı non-blocking mimariye geç

Bu prensiplerle loglama altyapınız hem daha sade hem daha güvenilir hale gelir.
