# PreventA — Yol Haritası (Roadmap)

> Durum tarihi: 2026-06-13 (son güncelleme: 2026-07-09). Bu doküman, ürünü
> "kutu işaretleme %72"den **uçtan uca çalışan, bütünlüklü bir ürüne** taşıyan
> görev-görev plandır. Onaylandıktan sonra fazlar sırayla uygulanır; her görevin
> bir kabul kriteri (AC) vardır.
>
> **2026-07-09 notu:** OpenPHA uyumluluk incelemesinin 7 maddesi tamamlandı ve
> production'a deploy edildi (bkz. **Faz 5**). Canlı: **`prevent-a.vercel.app`**.

## 0. Mevcut durum (dürüst başlangıç çizgisi)

**Çalışan:**
- Deploy sağlam: `prevent-a.vercel.app` (frontend + serverless API same-origin; `vercel --prod` CLI ile).
- Workspace CRUD (SQLite/Postgres, geçici) — studies/nodes/rows/LOPA API'leri çalışıyor.
- **OpenPHA `.opha` import/export** — gerçek studies'i yükler ve düzenlenmiş çalışmayı `.opha` olarak yeniden üretir (Faz 5).
- Backend testleri yeşil: `pytest` 82/82 (+gated Postgres entegrasyon), `ruff`, `mypy --strict` temiz.
- Risk matrisi ACWA 5×5 (Kritik≥12 / Yüksek≥8 / Orta≥4) — backend `risk_label` ↔ frontend `RiskMatrix` senkron.

**Yüzeysel / eksik (gerçek bütünlük açıkları):**
- `frontend/src/App.tsx` ~1.310 satır, 16 component → tek dosya monolit, modülerlik yok.
- **Ürünün çekirdeği AI önerileri UI'a bağlı değil:** `workspaceSuggestions = useState([])`, setter yok; `EvidencePanel` boş; `/api/v1/rag/deviation-assist` UI'dan hiç çağrılmıyor.
- Frontend hâlâ `fallbackStudy` / `fallbackStatus` + `data.ts` mock'una yaslanıyor.
- Backend RAG (Postgres+pgvector+Ollama) gerçek ortamda hiç çalıştırılmadı (untested).
- Tip sözleşmesi kopuk: backend `DeviationAssistResponse.candidates` ↔ frontend `Suggestion` uyuşmuyor.
- `/api/v1/status` ilerlemeyi şişiriyor (gerçeği yansıtmıyor).

## Yön veren kısıtlar (PRODUCT.md / DESIGN.md)

1. Worksheet komutada — navigasyon ve asistan tabloyu destekler, onunla yarışmaz.
2. Kanıt denetlenebilir — AI adayları daima kaynak + güven + tam eylemi gösterir.
3. Taslak ≠ karar — generated/accepted/edited/rejected durumları görünür biçimde ayrı ve denetlenebilir.
4. On-prem + müşteri sahipliği — yerel çalışma ve export görünür ürün nitelikleri.
5. Erişilebilirlik WCAG 2.2 AA — risk/durum rengin yanında metin+şekille de kodlanır.
6. Estetik: sessiz/yoğun engineering workbench; beyaz zemin, ölçülü yeşil, Inter, 64/248/fluid/336 shell.

---

## Faz 1 — Frontend zemin & bütünlük (önce frontend)

| # | Görev | Kabul kriteri (AC) |
|---|-------|--------------------|
| P1.1 | Canlı UI'yi screenshot'la, somut görsel/hiyerarşi/bütünlük problemlerini listele | İşaretli problem checklist'i çıkar |
| P1.2 | `App.tsx` monolitini modüllere böl: `layout/` (AppRail, StudyNavigator, TopBar), `worksheet/` (HazopTable, WorksheetToolbar), `evidence/`, `lopa/`, `matrix/`, `sources/`, `status/`, `landing/`, `dialogs/`; `data.ts` → `types.ts` | `App.tsx` < 150 satır (sadece kompozisyon); build+lint temiz |
| P1.3 | `DESIGN.md`'yi gerçek CSS token'a çevir: oklch renk seti, tipografi ölçeği (Inter + sabit skala), 4px spacing token'ları | Hardcoded hex yok; token'lar kullanılıyor |
| P1.4 | Dokümante shell'i birebir uygula: 64px rail · 248px navigator · fluid worksheet · 336px evidence; study context + worksheet aksiyonları sticky | Desktop ölçüleri DESIGN.md ile eşleşiyor |
| P1.5 | Responsive: <1180px evidence → overlay drawer; <860px nav → drawer + worksheet yatay scroll | 3 breakpoint'te doğrulandı |
| P1.6 | Mock/fallback'i sök: `fallbackStudy`/`fallbackStatus` → dürüst empty/loading/error state'leri (sahte veri değil) | API kapalıyken UI sahte satır değil, dürüst boş/hata gösterir |
| P1.7 | Risk yalnız renkle kodlanmasın: badge'ler metin+şekil+renk | Renk olmadan da risk okunur |

**Faz 1 doğrulama:** `pnpm run build` + `pnpm run lint` temiz; canlı preview'da shell + responsive ekran görüntüleri.

---

## Faz 2 — Çekirdek döngüyü canlı bağla

| # | Görev | Kabul kriteri (AC) |
|---|-------|--------------------|
| P2.1 | Studies/nodes/rows CRUD tam canlı (create/edit/delete) + optimistic update + autosave toast | Tüm CRUD API'ye karşı çalışır, fallback yok |
| P2.2 | Tip sözleşmesi: backend `DeviationAssistResponse` (suggestion_id, candidates[]) → frontend evidence modeli eşlemesi; `api.ts`'e `fetchDeviationAssist()` | Tipli istemci çağrısı mevcut |
| P2.3 | `EvidencePanel`'i `/api/v1/rag/deviation-assist`'e bağla: seçili satırdan tetikle, adayları kaynak/güven/section chip'leriyle göster | Panel gerçek (grounded) adayları gösterir |
| P2.4 | Kabul/düzenle/reddet akışı: kabul → seçili taslak satıra (cause/consequence/safeguard) yazar; taslak↔karar görünür ayrı | Kabul satırı günceller; reddet atılır; denetlenebilir |
| P2.5 | Atıf gösterimi + guardrail: her aday citation chip'i (tam referans title'da); 422 ungrounded → net mesaj | Ungrounded öneri guardrail mesajı gösterir |
| P2.6 | Evidence akışı için loading/empty/error state'leri | Üç durum da tasarlı |

**Faz 2 doğrulama:** Faz 3 backend ayakta iken EvidencePanel'de gerçek atıflı öneri → taslağa ekleme ekran kaydı.

---

## Faz 3 — Backend RAG canlı & test

| # | Görev | Kabul kriteri (AC) |
|---|-------|--------------------|
| P3.1 | `docker compose up` postgres+ollama; `nomic-embed-text` + chat modeli çek; `alembic upgrade head` | Stack healthy, migration uygulandı |
| P3.2 | Corpus ingestion smoke: `/rag/corpus/documents` ile örnek kontrollü-kaynak doküman; chunk'lar embed+store | Doküman + chunk'lar DB'de |
| P3.3 | Deviation-assist uçtan uca smoke: dense+sparse+RRF+rerank+generation+citation guardrail+trace | Atıflı adaylar döner; trace satırları yazılır |
| P3.4 | Guardrail negatif test: grounded bağlam yok → 422 ungrounded | Guardrail doğru bloklar |
| P3.5 | `scripts/evaluate_retrieval.py` held-out sette çalıştır | Retrieval metrikleri üretildi |
| P3.6 | Prod kalıcılık: managed Postgres + pgvector (Neon/Supabase); Vercel'de RAG stratejisi kararı (serverless pgvector limiti) ya da ayrı API host | Karar dokümante; (ops.) DB bağlı |

**Faz 3 doğrulama:** `/api/v1/rag/deviation-assist` canlı 201 + atıflar; guardrail 422 negatif test.

---

## Faz 4 — Derinlik & cila

| # | Görev | Kabul kriteri (AC) |
|---|-------|--------------------|
| P4.1 | LOPA/IPL gerçek: katman CRUD canlı, PFD matematiği, SIL hedefi | LOPA canlı veriden hesaplar |
| P4.2 | Kaynak envanteri: corpus'tan (`KnowledgeDocument`) kontrollü-kaynak listesi, aktif/pasif | Kaynaklar DB'den |
| P4.3 | DOCX rapor cilası + PDF | Müşteriye hazır rapor |
| P4.4 | WCAG 2.2 AA geçişi: klavye yolları, görünür focus, 200% zoom, reduced-motion | A11y checklist |
| P4.5 | Excel / geçmiş çalışma import | Import studies/nodes/rows'a eşler |
| P4.6 | Pilot hazırlığı: gerçek müşteri çalışması uçtan uca (Anar) | Bir gerçek çalışma tamamlanıp export edildi |

---

## Faz 5 — OpenPHA Uyumluluğu (TAMAM ✅ · 2026-07-09)

İşveren incelemesi (`openpha-mapping/` Drive klasörü: karşılaştırma + 7 maddelik
öneri listesi, commit `0cdb973` temelli) doğrultusunda PreventA "OpenPHA dosyası
okuyan araç"tan "**bir OpenPHA aracı**"na taşındı. Gerçek çalışma dosyası
(ANAGOLD `.opha`) ile kayıpsıza yakın round-trip hedeflenir.

| # | Madde | Ne yapıldı | AC | Durum |
|---|-------|-----------|----|-------|
| 1 | Ters export ORM→`.opha` | `features/opha/export.py::orm_to_opha` DB'den `.opha` yeniden kurar; async eager-load `repository.py::export_opha_study` | import→DB→export→compare testi geçer | ✅ |
| 2 | Recommendations m2m | `consequence_recommendation` link tablosu (tek FK kaldırıldı) | Paylaşılan öneri tüm senaryolara bağlanır | ✅ |
| 3 | Severity/likelihood → sayı | `features/opha/risk.py::RiskMatrixResolver` kodları ordinal'e çözer + çok-kategorili severity JSON | Sayısal risk hesaplanır/sıralanır | ✅ |
| 4 | LOPA doğrulayıcı | `features/opha/lopa_check.py::recompute_lopa` (freq×IPL PFD×modifiers vs TMEL); `LopaModifier` tablosu; `mel_calc`/`meets_tmel` | Import'ta LOPA aritmetiği yeniden hesaplanır | ✅ |
| 5 | `Ds_Rev` sürümleme | `Study.ds_rev` + `features/opha/versioning.py::check_ds_rev` | Bilinmeyen sürümde sessiz kırılma yok | ✅ |
| 6 | Destek register'ları | `db/models/registers.py`: Team, Session(+attendance), Drawing, ParkingLot, MOC, SCAI, Incident, Checklist — her biri `raw` JSON ile kayıpsız | Register'lar DB'de + export'ta korunur | ✅ |
| 7a | Worksheet hiyerarşisi | Cause `rowSpan` ile gruplanır → consequence'lar altında; "＋ consequence" aksiyonu | Cause tekrar edilmez; consequence eklenir | ✅ |
| 7b | Üç-durumlu risk | Flat grid'de Before/Current/After sütun-grupları; `mvp_rows` 4 kolon + idempotent `_migrate_mvp_rows` (Postgres `ADD COLUMN IF NOT EXISTS`) | Grid üç risk durumunu gösterir | ✅ (canlı doğrulandı) |

Migration: `migrations/versions/20260708_0004_opha_review_items.py` (yapısal ORM
şeması). Flat MVP store kolonları cold-start'ta `initialize_store` içinde
idempotent eklenir.

**Faz 5 doğrulama:** 82 unit test + gated Postgres entegrasyon testi; canlı
production'da `.opha` import → grid con1'i **Critical → High → Low** (üç durum)
render eder; ruff+mypy+frontend `tsc`/`vite build` temiz.

---

## Çapraz kesen işler (cross-cutting)

| # | Görev | AC |
|---|-------|----|
| C1 | Vercel↔GitHub Git entegrasyonunu yeniden bağla (repo `dev-chron→tarikdeveci` taşınınca koptu) → `git push` otomatik deploy | ⚠️ Hâlâ kopuk; deploy `vercel --prod` CLI ile yapılıyor |
| C2 | Risk matrisi eşiklerini senkron tut (store.py ↔ App.tsx) | ✅ Tamam (12/8/4) |
| C3 | `pytest`+`ruff`+`mypy` yeşil kalsın; Faz 2'den itibaren frontend testleri ekle | ✅ Backend 82/82 + ruff + mypy yeşil; frontend `tsc`/`vite build` yeşil (birim testleri hâlâ eksik) |
| C4 | `/api/v1/status`'u gerçek tamamlanmayı yansıtacak şekilde dürüstleştir | Status şişirilmemiş |

---

## Bağımlılık sırası (özet)

```
P1 (frontend zemin) ──┐
                      ├─► P2 (UI ↔ API döngü)  ──► P4 (derinlik & cila)
P3 (backend RAG) ─────┘   (P2.3–P2.5 tam testi P3'e bağlı)
```

P3, P1/P2'ye paralel ilerleyebilir (ayrı backend işi). P2'nin AI kısmının
**tam doğrulaması** P3'ün ayakta olmasına bağlıdır.
