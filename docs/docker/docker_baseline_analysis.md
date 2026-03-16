# Docker Baseline Analysis

## Amaç

Bu not, projede uygulanan Docker ve Docker Compose kararlarını iki açıdan özetler:

1. Dokümandaki production dockerization prensipleriyle ne kadar uyumlu olduğumuz
2. Mevcut dosya yerleşiminin enterprise-ready bir temel için doğru olup olmadığı

Bu analiz şu dosyaların mevcut haline dayanır:

- `Dockerfile`: `infra/api/Dockerfile`
- service compose: `infra/api/docker-compose.yml`
- root compose: `docker-compose.yml`

## Dokümandaki Ana Prensipler

`docs/team_notes/dockerization_principles.md` içindeki temel yaklaşım şu:

- Multi-stage build kullanılmalı
- Minimal runtime image tercih edilmeli
- Dependency kurulumu deterministic olmalı
- Runtime non-root user ile çalışmalı
- Healthcheck olmalı
- Image küçük ve saldırı yüzeyi dar tutulmalı
- Runtime security ayarları düşünülmeli
- İleride CI security scan, SBOM ve image signing eklenmeli

Bu yaklaşım açık biçimde security-first ve enterprise-ready temel hedefliyor.

## Bu Projede Uygulanan Kararlar

### 1. Multi-stage build kullanıldı

Builder ve runtime ayrıldı.

Sonuç:

- Build araçları runtime image'a taşınmıyor
- Runtime daha temiz kalıyor
- Attack surface küçülüyor

Bu, dokümandaki multi-stage build prensibiyle doğrudan uyumlu.

### 2. Python sürümü proje ile hizalandı

`pyproject.toml` içinde proje `>=3.13` istiyor. Docker image başlangıçta `python:3.12-slim` idi. Bu, dependency çözümünde ve runtime'da tutarsızlık üretme riski taşıyordu.

Bu yüzden Dockerfile şu hale çekildi:

- builder: `python:3.13-slim`
- runtime: `python:3.13-slim`

Sonuç:

- Build ortamı ile proje kontratı hizalandı
- `uv sync` sırasında sessiz dependency sapmaları önlendi
- Runtime sürprizleri azaldı

### 3. Dependency install lock file ile korunuyor

Builder stage içinde `pyproject.toml` ve `uv.lock` kopyalanıp `uv sync --locked --no-dev --no-install-project` çalıştırılıyor.

Sonuç:

- Reproducible build elde ediliyor
- Dependency sürümleri sabitleniyor
- Kod değiştiğinde dependency layer cache korunabiliyor

Bu, dokümandaki deterministic build ve layer cache optimizasyonu ile uyumlu.

### 4. Runtime non-root user ile çalışıyor

Runtime içinde `app` kullanıcısı tanımlandı ve container bu kullanıcıyla çalışıyor.

Sonuç:

- Root yetkisiyle çalışan container riski azaltıldı
- Runtime güvenliği iyileştirildi

Bu, dokümandaki non-root user prensibiyle uyumlu.

### 5. Permission denied hatası kökten ele alındı

İlk hata şuydu:

`/app/.venv/bin/uvicorn: Permission denied`

Bu durum, kopyalanan `.venv` içindeki executable dosyaların çalıştırma izniyle ilgiliydi.

Uygulanan çözüm:

- `.venv` içeriği runtime image'a kopyalandı
- `.venv/bin` altındaki runtime entrypoint dosyaları için çalıştırma izni garanti edildi
- Uygulama doğrudan script yerine venv içindeki Python ile başlatıldı

Başlatma komutu şu şekilde sabitlendi:

`/app/.venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8089`

Sonuç:

- PATH çözümlemesine bağımlılık azaltıldı
- Doğru Python interpreter ile doğru environment çalıştırıldı
- Permission kaynaklı entrypoint sorunu kapatıldı

Not:

İlk sürümde sabit uid/gid, ek PATH ayarı ve daha geniş bir permission düzeltmesi vardı. Bunlar bazı kurumsal ortamlarda faydalı olabilir, ancak bu repo için okunabilirliği artırmak adına runtime bloğu sadeleştirildi. Şu an bırakılan parçalar gerçekten gerekli olan minimum settir: non-root user, venv kopyası, uygulama kodu ve `.venv/bin` için hedefli executable izin düzeltmesi.

### 6. Healthcheck için curl yerine Python kullanıldı

Healthcheck şu nedenle Python ile yazıldı:

- Runtime image'a ekstra `curl` paketi eklememek
- Minimal image yaklaşımını korumak
- Mevcut runtime toolchain dışında bağımlılık getirmemek

Bu yaklaşım security-first ve minimal runtime mantığına uygundur.

Not:

`curl` kullanmak teknik olarak yanlış değildir. Ancak bu projedeki mevcut hedef daha dar runtime ve daha az paket olduğu için Python healthcheck daha tutarlı bir seçimdir.

### 7. Compose tarafında runtime hardening eklendi

Service compose içinde şu ayarlar var:

- `init: true`
- `security_opt: no-new-privileges:true`
- `stop_grace_period: 30s`

Sonuç:

- Container davranışı development için fazla sertleşmeden daha kontrollü hale geldi
- Privilege escalation yüzeyi daraltıldı
- Uygulamaya kapanış sırasında kontrollü shutdown süresi bırakıldı

Bu, dokümandaki runtime security yaklaşımıyla uyumludur; ancak bilinçli olarak düşük sürtünmeli bir development baseline seviyesinde tutulmuştur.

## Docker Ayarların Genel Mühendislik Mantığı

Bu ayarların çoğu üç ana hedefe hizmet eder:

1. Güvenlik
- non-root user
- no-new-privileges

2. Öngörülebilirlik
- sabit Python sürümü
- lock file
- explicit venv interpreter
- healthcheck

3. Operasyonel kalite
- init
- stop_grace_period
- restart policy
- stdout odaklı runtime davranışı

Buradaki esas fikir şudur:

Container sadece çalışan bir kutu değil, davranışı sınırlandırılmış ve işletmesi kolay bir çalışma birimi olmalıdır.

## Hangi Ayarlar Development, Hangileri Production'a Yakın?

Bugünkü compose dosyasında ikisi karışık halde bulunuyor. Bu bilinçli ve normal bir durumdur.

Development ağırlıklı ayarlar:

- `ports`
- `volumes`
- sabit `container_name`

Production'a yakın hardening ayarları:

- `no-new-privileges`
- `stop_grace_period`
- `healthcheck`

Bu yüzden mevcut compose dosyası tam production compose değildir. Ama production düşünülerek yazılmış, sürtünmesi azaltılmış bir development baseline'dır.

### 8. Root compose dosyası orchestration entrypoint olarak eklendi

Proje kökündeki `docker-compose.yml`, doğrudan servis tanımlamak yerine include ile `infra/api/docker-compose.yml` dosyasını çağırıyor.

Sonuç:

- Kökten ayağa kaldırma kolaylaşıyor
- Altyapı dosyaları `infra` altında tutuluyor
- İleride başka servisleri eklemek için genişleme alanı bırakılıyor

## Şu Anki Yapının Güçlü Yanları

- Multi-stage build var
- Python sürümü proje ile uyumlu
- Lock file tabanlı deterministic dependency kurulumu var
- Runtime non-root user ile çalışıyor
- Compose tarafında düşük sürtünmeli temel hardening var
- Root compose giriş noktası oluşturulmuş durumda
- Healthcheck ve restart politikası tanımlı

Bu haliyle yapı, küçük bir demo Docker setup'ından çıkıp gerçek bir enterprise başlangıç çizgisine yaklaşmış durumda.

## Şu Anki Yapının Zayıf veya Eksik Yanları

Bu yapı iyi bir temel olsa da henüz tam production standardı değildir. Eksik kalan başlıklar:

- CI içinde image vulnerability scan yok
- SBOM üretimi yok
- Image signing yok
- `latest` dışı resmi tag stratejisi tanımlı değil
- Dev, stage, prod için compose katman ayrımı henüz net değil
- Reverse proxy, metrics, readiness/liveness ayrımı yok
- Compose hardening seviyesi şu an bilinçli olarak minimal tutuluyor

Bunlar sonraki aşamada eklenmesi gereken enterprise katmanlarıdır.

## Docker Compose Konumu İyi Mi?

Kısa cevap:

- Bugünkü hali yanlış değil
- Ama uzun vadeli enterprise düzen için daha iyi bir yapı kurulabilir

Şu anki yerleşim:

- root: `docker-compose.yml`
- service compose: `infra/api/docker-compose.yml`
- image build: `infra/api/Dockerfile`

Bu yapı bugünkü repo ölçeği için mantıklı çünkü:

- Şu anda tek ana servis var
- Ekip için giriş noktası kökte kalıyor
- Dockerfile ve servis compose aynı yerde olduğu için keşfetmesi kolay
- Klasör derinliği gereksiz yere büyümüyor

Bu nedenle `infra/api` yerleşimi, şu aşamada daha sade ve daha okunur bir tercih.

## Seçilen Yapı

Şimdilik seçilen yapı şu:

```text
docker-compose.yml
infra/
  api/
    Dockerfile
    docker-compose.yml
```

Bu yapının artıları:

- Yol daha kısa ve anlaşılır
- Tek servis için gereksiz environment klasörü taşımıyor
- Dockerfile ve compose aynı sorumluluk alanında bulunuyor
- Root compose korunarak ekip kullanım akışı sade kalıyor

Bu yapının bedeli:

- İleride `dev`, `stage`, `prod` ayrımı büyürse yeniden organizasyon gerekebilir
- Compose ile image artifact ayrımı şu an aynı klasörde duruyor

## Nihai Tavsiye

Bugünkü karar için tavsiyem şu:

1. Root `docker-compose.yml` dosyasını koru
2. Dockerfile ve servis compose dosyalarını `infra/api` altında tut
3. Environment bazlı compose katmanlarını ancak gerçekten ihtiyaç doğduğunda ayır

İleride büyüme ihtiyacı doğarsa şu yapıya geçilebilir:

```text
docker-compose.yml
infra/
  docker/
    api/
      Dockerfile
  compose/
    base.yml
    dev.yml
    prod.yml
```

Sebep:

- Bugün sade yapı daha hızlı anlaşılır
- Yarın ihtiyaç büyürse sorumluluk bazlı ayrım yapılabilir
- Erken aşamada fazla klasörleme de bir maliyettir

## Sonuç

Şu an yaptığımız çalışma dokümandaki production dockerization prensipleriyle büyük ölçüde uyumludur. Özellikle şu başlıklarda doğru zemindeyiz:

- reproducibility
- minimal runtime
- non-root execution
- multi-stage build
- ölçülü runtime hardening
- healthcheck

Klasör yerleşiminde şu anki tercih, mevcut repo ölçeği için rasyonel ve temizdir.

Bugün için en doğru mimari karar:

- root compose'u bırakmak
- `infra/api` altında Dockerfile ve servis compose'u birlikte tutmak
- ileride ihtiyaç büyürse `infra/docker` ve `infra/compose` ayrımına geçmek

Bu yaklaşım hem bugünü gereksiz karmaşıklaştırmaz hem de yarın yeniden taşıma maliyetini düşürür.