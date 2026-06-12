from preventa.features.workspace.schemas import (
    DeliveryModule,
    ProductStatusResponse,
    WorkspaceNode,
    WorkspaceResponse,
    WorkspaceRow,
    WorkspaceStudy,
    WorkspaceSuggestion,
)


def get_workspace() -> WorkspaceResponse:
    return WorkspaceResponse(
        source="api_seed",
        study=WorkspaceStudy(
            id="study-reactor-2026",
            title="Ünite 200 HAZOP",
            client="ACWA Power",
            facility="Konya",
            progress=62,
            reviewed_scenarios=89,
            total_scenarios=143,
        ),
        active_node_id="node-p101",
        nodes=[
            WorkspaceNode(
                id="node-t100",
                code="N-01",
                name="Hammadde tankı T-100",
                equipment_type="Atmosferik tank",
                design_intent="Hammaddeyi güvenli işletme sınırlarında depolamak.",
                scenario_count=18,
                state="complete",
            ),
            WorkspaceNode(
                id="node-p101",
                code="N-02",
                name="Besleme pompası P-101",
                equipment_type="Santrifüj pompa",
                design_intent=(
                    "T-100 hammadde tankından R-201 reaktörüne kesintisiz ve "
                    "kontrollü besleme sağlamak."
                ),
                scenario_count=24,
                state="active",
            ),
            WorkspaceNode(
                id="node-e102",
                code="N-03",
                name="Isı eşanjörü E-102",
                equipment_type="Kabuk-boru eşanjör",
                design_intent="Besleme sıcaklığını reaksiyon giriş koşuluna getirmek.",
                scenario_count=16,
                state="review",
            ),
            WorkspaceNode(
                id="node-r201",
                code="N-04",
                name="Reaktör R-201",
                equipment_type="Karıştırıcılı reaktör",
                design_intent="Reaksiyonu tanımlı sıcaklık ve basınç aralığında yürütmek.",
                scenario_count=31,
                state="review",
            ),
            WorkspaceNode(
                id="node-v301",
                code="N-05",
                name="Ayırıcı V-301",
                equipment_type="Basınçlı kap",
                design_intent="Gaz ve sıvı fazlarını güvenli biçimde ayırmak.",
                scenario_count=0,
                state="empty",
            ),
        ],
        rows=[
            WorkspaceRow(
                id=1,
                guideword="Yok",
                deviation="Akış yok",
                cause=(
                    "P-101A/B pompalarının ortak emiş hattında izolasyon vanasının "
                    "kapalı kalması"
                ),
                consequence=(
                    "Reaktör beslemesinin kesilmesi; sıcaklık kontrolünün bozulması "
                    "ve plansız duruş"
                ),
                safeguard=(
                    "Düşük akış alarmı FAL-101; yedek pompa otomatik devreye alma "
                    "prosedürü"
                ),
                severity=3,
                likelihood=2,
                risk="Orta",
                status="İncelendi",
            ),
            WorkspaceRow(
                id=2,
                guideword="Fazla",
                deviation="Yüksek akış",
                cause="Kontrol vanası FV-101'in tam açık konumda arızalanması",
                consequence=(
                    "Reaktörde besleme oranının artması; sıcaklık yükselmesi ve ürün "
                    "spesifikasyon dışı üretim"
                ),
                safeguard=(
                    "Yüksek akış alarmı FAH-101; bağımsız yüksek sıcaklık tripi "
                    "TSHH-204"
                ),
                severity=4,
                likelihood=2,
                risk="Yüksek",
                status="Taslak",
            ),
            WorkspaceRow(
                id=3,
                guideword="Ters",
                deviation="Ters akış",
                cause="Pompa duruşunda çekvalfin sızdırması veya açık kalması",
                consequence=(
                    "Proses akışkanının depolama tankına geri dönmesi; tankta aşırı "
                    "basınç ve kontaminasyon"
                ),
                safeguard="Çekvalf bakım programı; pompa çıkışında motorlu izolasyon vanası",
                severity=4,
                likelihood=3,
                risk="Kritik",
                status="Eksik",
            ),
            WorkspaceRow(
                id=4,
                guideword="Az",
                deviation="Düşük akış",
                cause="Emiş filtresinin kısmi tıkanması veya tank seviyesinin düşmesi",
                consequence="Pompa kavitasyonu; mekanik hasar ve yanıcı akışkan kaçağı",
                safeguard="Düşük tank seviye alarmı LAL-100; titreşim izleme",
                severity=3,
                likelihood=3,
                risk="Yüksek",
                status="Taslak",
            ),
        ],
        suggestions=[
            WorkspaceSuggestion(
                id="s1",
                kind="Neden",
                text="Ortak emiş süzgecinin polimer birikimi nedeniyle tıkanması",
                confidence="Yüksek",
                source="HAZOP-2024-018",
                section="Node 12 · P-204",
                target="cause",
            ),
            WorkspaceSuggestion(
                id="s2",
                kind="Önlem",
                text="Pompa emiş ve basma basınç farkı için yüksek fark basınç alarmı",
                confidence="Yüksek",
                source="HAZOP-2023-041",
                section="Node 07 · Santrifüj pompa",
                target="safeguard",
            ),
            WorkspaceSuggestion(
                id="s3",
                kind="Sonuç",
                text=(
                    "Kavitasyon kaynaklı mekanik salmastra hasarı ve yanıcı akışkan "
                    "salımı"
                ),
                confidence="Orta",
                source="IEC 61882",
                section="§6.3.4 · Consequences",
                target="consequence",
            ),
        ],
    )


def get_product_status() -> ProductStatusResponse:
    return ProductStatusResponse(
        release="MVP foundation",
        stage="Entegre prototip",
        overall_progress=46,
        api_connected=True,
        persistence="seed",
        ai_runtime="contract_ready",
        deployment="Vercel frontend + serverless API",
        modules=[
            DeliveryModule(
                id="ui",
                name="Ürün arayüzü",
                status="complete",
                progress=100,
                detail="HAZOP, LOPA, risk matrisi, kaynaklar ve responsive çalışma alanı.",
            ),
            DeliveryModule(
                id="api",
                name="Frontend API bağlantısı",
                status="complete",
                progress=100,
                detail="Workspace ve ürün durumu aynı domain üzerindeki API'den yükleniyor.",
            ),
            DeliveryModule(
                id="database",
                name="PostgreSQL kalıcılık",
                status="in_progress",
                progress=55,
                detail="Şema ve migration hazır; production veritabanı bağlantısı bekliyor.",
            ),
            DeliveryModule(
                id="rag",
                name="Kaynaklı RAG önerileri",
                status="in_progress",
                progress=60,
                detail=(
                    "Retrieval, citation ve Ollama sözleşmesi hazır; canlı corpus "
                    "ingestion eksik."
                ),
            ),
            DeliveryModule(
                id="crud",
                name="Study ve HAZOP CRUD",
                status="in_progress",
                progress=35,
                detail="Read API bağlı; create/update persistence endpoint'leri sıradaki iş.",
            ),
            DeliveryModule(
                id="report",
                name="DOCX/PDF rapor",
                status="planned",
                progress=10,
                detail="Rapor aksiyonu UI'da; gerçek şablon üreticisi henüz bağlı değil.",
            ),
            DeliveryModule(
                id="import",
                name="Excel ve geçmiş çalışma import",
                status="planned",
                progress=5,
                detail="Veri eşleme ve doğrulama akışı tasarlanacak.",
            ),
            DeliveryModule(
                id="pilot",
                name="Gerçek pilot çalışma",
                status="planned",
                progress=0,
                detail="Anar ile gerçek müşteri çalışmasında uçtan uca doğrulama.",
            ),
        ],
    )
