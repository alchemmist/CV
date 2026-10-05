# Масштаб User Sessions RT и HitMaster для резюме

Собрано 21 сентября 2026 через MCP Monium и InfraCtl. Только локальные материалы.

## Период и результаты

Трафик: 14 сентября 00:00 — 21 сентября 00:00 UTC, семь полных суток.
Средние рассчитаны по 168 часовым значениям с агрегацией avg, без заполнения пропусков предыдущим значением.

| Проект | Вход решардеров, млн записей/с | Чтение основных consumers из Logbroker, ГБ/с | Запись в наблюдаемые выходные топики, ГБ/с |
|---|---:|---:|---:|
| User Sessions RT | 2.896 | 4.330 | 2.897 |
| HitMaster / Money RT | 2.901 | 6.823 | 4.305 |
| Суммарно | 5.797 | 11.153 | 7.202 |

В пересчёте на сутки: около 964 ТБ чтения и 622 ТБ записи. ГБ и ТБ — десятичные единицы.
Это транспортный оборот наблюдаемых потоков, а не объём уникальных пользовательских данных.

## Ресурсы из действующих спецификаций InfraCtl

| Контур | Подов по спецификации | Ядер CPU по compute.vcpu | Память по compute.memory, ТиБ |
|---|---:|---:|---:|
| User Sessions RT, основной production | 2148 | 12056.700 | 29.943 |
| HitMaster, основной production | 2646 | 35288.652 | 28.140 |
| Основной production суммарно | 4794 | 47345.352 | 58.083 |
| HitMaster Phoenix (отдельно) | 418 | 4526.500 | 3.826 |
| User Sessions RT hamster + prestable-zero | 858 | 1284.204 | 5.758 |
| HitMaster prestable | 768 | 3880.935 | 4.564 |
| Все перечисленные контуры | 6838 | 57036.991 | 72.231 |

Основной production — 13 RuntimeGroup, 164 DU, размещение в KLG/SAS/VLA.
Дополнительно в основных контурах объявлено 82.831 ТиБ корневого диска и 342.176 ГБ/с гарантии сети. Это не полный объём хранения: отдельные диски REX, служебные диски платформы и YT сюда не включены.
CPU/RAM — объявленные ресурсы подов, не измеренное потребление, не свободная квота ABC и не физические серверы. Не суммировались повторно compute.boxes и sidecars.
Количество подов — целевая конфигурация, не доказательство одновременной готовности каждого пода. Часть RuntimeGroup в момент проверки имела статус InProgress.

## Методика и ограничения

- Не использовать термин HTTP RPS: records.input измеряет входные записи решардеров. Это не уникальные запросы пользователей. Суммируются только production-решардеры, а не все ступени обработки.
- Для records.input выбраны host=TOTAL, location=TOTAL, supplier=TOTAL: итоговые ряды не складываются с их детализациями. Суммарный поток может включать повторную обработку и не является дедуплицированным числом бизнес-событий.
- Вход Logbroker: уникальные TopicPath из production topic-lags, основной consumer каждого проекта. Дополнительные PubRtabtConsumer/PubRtabtChaosConsumer не включены. Это основной наблюдаемый вход, а не исчерпывающая инвентаризация каждого транспорта проекта.
- Выход Logbroker: уникальные TopicPath из production lb-write-quotas, исключены /prestable/. 126 путей User Sessions и 38 HitMaster. Исторические пути без данных не считаются нулевыми подтверждёнными потоками. Внутренние топики между компонентами также входят в этот каталог: показатель нельзя называть чистым внешним выходом.
- Для Logbroker использованы host=cluster и точные списки TopicPath, а не сумма отдельных хостов и итоговых рядов одновременно. OriginDC оставлен как разрез источника данных; значения суммируются. Физическую репликацию хранения отдельно не умножали.
- ReadBytesPerSec и WriteBytesPerSec — байты транспортных метрик Logbroker. Нельзя без дополнительных данных называть их несжатыми байтами бизнес-событий или коэффициентом сжатия. Прикладные roren.input.uncompressed_bytes и bytes.input в итоговую пару чтение/запись не включены.
- Ресурсы: число подов суммируется по per_cluster.replicas.*.pods; у profile-manager используется multi_cluster.replicas. Ресурс одного пода умножается на число подов. 1000 compute.vcpu = 1 ядро; memory — байты, ТиБ = 2^40 байт.
- Phoenix, hamster и prestable исключены из цифр production в резюме. YT-бандлы, Logbroker-серверы и другие соседние сервисы не включены в ресурсные итоги.

## Источники

- [User Sessions throughput](https://monitoring.yandex-team.ru/projects/user_sessions/dashboards/mon9f89k0uvvn3nk6ue5)
- [HitMaster throughput](https://monitoring.yandex-team.ru/projects/money_rt/dashboards/mon8fhs94bvni4tev14s)
- [User Sessions input topics](https://monitoring.yandex-team.ru/projects/user_sessions/dashboards/mon94p9ttbvtr2qhq06n)
- [HitMaster input topics](https://monitoring.yandex-team.ru/projects/money_rt/dashboards/monb1u7hejevgec259nb)
- [User Sessions output topics](https://monitoring.yandex-team.ru/projects/user_sessions/dashboards/monmgt0brn1k2avi7c59)
- [HitMaster output topics](https://monitoring.yandex-team.ru/projects/money_rt/dashboards/mon49s77f53d3jabrfb5)
- [Единицы compute в InfraCtl](https://docs.yandex-team.ru/infractl/objects/runtime#pod-computing-resources)

MCP InfraCtl: group=k.yandex-team.ru, version=v1, kind=RuntimeGroup; namespaces user-sessions-rt и rt-money; поля spec.runtimes и status.deployed.

## Запросы Monium

Для каждого запроса: from=2026-09-14T00:00:00Z, to=2026-09-21T00:00:00Z, grid_millis=3600000, aggregation=avg.

### us_events_full

```text
series_sum({project="user_sessions",service="user_sessions_resharder-*",cluster="yp_user-sessions-rt_resharder-*",host="TOTAL",location="TOTAL",supplier="TOTAL",sensor="records.input"})
```

### hm_events_full

```text
series_sum({project="money_rt",service="money_rt_resharder-*",cluster="yp_money-rt-production_resharder-*",host="TOTAL",location="TOTAL",supplier="TOTAL",sensor="records.input"})
```

### us_lb_in_bytes

```text
series_sum({project="kikimr",service="pqtabletAggregatedCounters",cluster="lbk|lbkx",host="cluster",partition="-",ConsumerPath="user-sessions/production/user-sessions-consumer",TopicPath="yandex/access-log|search/search-blockstat-log|search/splitted-proto-reqans/rt-reqans-log|redir/redir-log|mmetasearch/web-meta-search-props-rt-log|search-web/redir-perf-log|search-web/redir-log|search-web/redir-tech-log|bar_navig/bar-navig-log|superapp-logs/browser_metrika_mobile_log|yabs-rt/bs-watch-log|images/redir-log|images/images_http_adapter_access_log|images/blockstat-log|images/redir-perf-log|images/img-reqans-proto-log|images/redir-tech-log|superapp-logs/superapp_metrika_mobile_log|search-video/access-event-log|search-video/blockstat-log|search-video/redir-perf-log|search/video-reqans-log|search-video/redir-log|search-video/redir-tech-log|cvsearch/logs/cbir-proto-reqans-log|collections/collections-redir-log|search/direct-proto-reqans-log|images/redir-misc/error-client-redir-log|images/redir-misc/rum-cls-redir-log|images/redir-misc/rum-delta-redir-log|images/redir-misc/rum-navigation-redir-log|images/redir-misc/rum-time-redir-log|images/redir-misc/error-uncaught-redir-log|addrs/map-reqans-log|morda/access-log|morda/blockstat-baobab-log|morda/blockstat-log|morda/morda-baobab-redir|search/proto-profile-log|unisearch/verticals/spectre|reef/prod/blockstat_logs|metarealty/b2c/prod_app_host_metarealty|reef/prod/redir-log|uslugi-na-poiske/apphost/logs|saas/logs/stable/searchproxy-access|saas/logs/stable_intrasearch/searchproxy-access|saas/logs/stable/searchproxy-reqans|saas/logs/stable_intrasearch/searchproxy-reqans|suggest/suggest-response-log|turbo/blockstat-log|redir/uslugi-redir-log|search-video/redir-misc/error-client-redir-log|search-video/redir-misc/rum-cls-redir-log|search-video/redir-misc/rum-delta-redir-log|search-video/redir-misc/rum-navigation-redir-log|search-video/redir-misc/rum-time-redir-log|search-video/redir-misc/error-uncaught-redir-log|redir/path-redir/error-client-redir-log|redir/path-redir/error-uncaught-redir-log|redir/path-redir/rum-cls-redir-log|redir/path-redir/rum-time-redir-log|redir/path-redir/rum-navigation-redir-log|yazeka/blockstat-log|yazeka/redir-log|redir/path-redir/rum-delta-redir-log",sensor="ReadBytesPerSec"})
```

### hm_lb_in_bytes

```text
series_sum({project="kikimr",service="pqtabletAggregatedCounters",cluster="lbk|lbkx",host="cluster",partition="-",ConsumerPath="user-sessions/rt-money/prod/pub-consumer",TopicPath="rt_money/prod/to-stateless-observers|bsexport/bs-chevent-verdict-log|yabs-rt/bs-pseq-event_lite-log|yabs-rt/bs-pseq-hit_rt-log|yabs-rt/bs-pseq-ads_object_model_event-log|bsexport/bs-action-checked-verdict-log|xurma/prod/bs-chtracking-grouped-verdict-log|xurma/bs-dsp-checked-grouped-verdict-log|yabs-sb/bs-mobile-postclick-log|yabs-rt/bs-pseq-tracking-log|rythmmaster/prod/rythm-ads-action-log|metrika/visit-v2-ads-log|yabs-sb/bs-ally-services-billed-checked-log|xurma/prod/bs-chtracking-log|bsexport/bs-undochtracking-log|yabs-sb/balance/prod/acted_events",sensor="ReadBytesPerSec"})
```

### us_out_bytes

```text
series_sum({project="kikimr",service="pqtabletAggregatedCounters",cluster="lbk|lbkx",host="cluster",TopicPath="user-sessions/rtyt/access-log/common/errors|user-sessions/rtyt/access-log/common/sessions|user-sessions/rtyt/access-log/images/sessions|user-sessions/rtyt/access-log/video/sessions|user-sessions/rtyt/search-blockstat-log/errors|user-sessions/rtyt/search-blockstat-log/sessions|user-sessions/rtyt/search-proto-reqans-log-rt/errors|user-sessions/rtyt/search-proto-reqans-log-rt/prefetches|user-sessions/rtyt/search-proto-reqans-log-rt/sessions|user-sessions/rtyt/common-redir-log/common/errors|user-sessions/rtyt/common-redir-log/common/sessions|user-sessions/rtyt/common-redir-log/geo/sessions|user-sessions/rtyt/common-redir-log/portal/sessions|user-sessions/rtyt/common-redir-log/tv_online/sessions|user-sessions/rtyt/web-middle-reqans-log/errors|user-sessions/rtyt/web-middle-reqans-log/sessions|user-sessions/rtyt/search-redir-perf-log/errors|user-sessions/rtyt/search-redir-perf-log/sessions|user-sessions/rtyt/search-redir-log/errors|user-sessions/rtyt/search-redir-log/sessions|user-sessions/rtyt/search-redir-tech-log/errors|user-sessions/rtyt/search-redir-tech-log/sessions|user-sessions/rtyt/antirobot|user-sessions/rtyt/spy-log/baobab_events|user-sessions/rtyt/spy-log/browser_antifraud_info|user-sessions/rtyt/spy-log/bundle_stat|user-sessions/rtyt/spy-log/cookie_mining|user-sessions/rtyt/spy-log/errors|user-sessions/rtyt/spy-log/sessions|user-sessions/rtyt/bs-watch-log/errors|user-sessions/rtyt/bs-watch-log/sessions|user-sessions/rtyt/images-redir-log/errors|user-sessions/rtyt/images-redir-log/sessions|user-sessions/rtyt/access-log/images/errors|user-sessions/rtyt/images-blockstat-log/errors|user-sessions/rtyt/images-blockstat-log/sessions|user-sessions/rtyt/images-redir-perf-log/errors|user-sessions/rtyt/images-redir-perf-log/sessions|user-sessions/rtyt/images-proto-reqans-log/errors|user-sessions/rtyt/images-proto-reqans-log/sessions|user-sessions/rtyt/images-redir-tech-log/errors|user-sessions/rtyt/images-redir-tech-log/sessions|user-sessions/rtyt/access-log/video/errors|user-sessions/rtyt/video-blockstat-log/errors|user-sessions/rtyt/video-blockstat-log/sessions|user-sessions/rtyt/video-redir-perf-log/errors|user-sessions/rtyt/video-redir-perf-log/sessions|user-sessions/rtyt/video-proto-reqans-log/errors|user-sessions/rtyt/video-proto-reqans-log/sessions|user-sessions/rtyt/video-proto-reqans-log/smartdevice_video|user-sessions/rtyt/video-redir-log/errors|user-sessions/rtyt/video-redir-log/sessions|user-sessions/rtyt/video-redir-tech-log/errors|user-sessions/rtyt/video-redir-tech-log/sessions|user-sessions/rtyt/video-redir-tech-log/smartdevice_video|user-sessions/rtyt/cbir-proto-reqans-log/errors|user-sessions/rtyt/cbir-proto-reqans-log/sessions|user-sessions/rtyt/collections-redir-log/errors|user-sessions/rtyt/collections-redir-log/sessions|user-sessions/rtyt/direct-proto-reqans-log/errors|user-sessions/rtyt/direct-proto-reqans-log/sessions|user-sessions/rtyt/images-error-client-redir/errors|user-sessions/rtyt/images-error-client-redir/sessions|user-sessions/rtyt/images-rum-cls-redir/errors|user-sessions/rtyt/images-rum-cls-redir/sessions|user-sessions/rtyt/images-rum-delta-redir/errors|user-sessions/rtyt/images-rum-delta-redir/sessions|user-sessions/rtyt/images-rum-navigation-redir/errors|user-sessions/rtyt/images-rum-navigation-redir/sessions|user-sessions/rtyt/images-rum-time-redir/errors|user-sessions/rtyt/images-rum-time-redir/sessions|user-sessions/rtyt/images-uncaught-redir/errors|user-sessions/rtyt/images-uncaught-redir/sessions|user-sessions/rtyt/map-reqans-log/errors|user-sessions/rtyt/map-reqans-log/sessions|user-sessions/rtyt/morda-access-log/errors|user-sessions/rtyt/morda-access-log/sessions|user-sessions/rtyt/morda-blockstat-log/errors|user-sessions/rtyt/morda-blockstat-log/sessions|user-sessions/rtyt/proto-profile-log/errors|user-sessions/rtyt/proto-profile-log/sessions|user-sessions/rtyt/reef-access-log/errors|user-sessions/rtyt/reef-access-log/sessions|user-sessions/rtyt/reef-blockstat-log/errors|user-sessions/rtyt/reef-blockstat-log/sessions|user-sessions/rtyt/reef-redir-log/errors|user-sessions/rtyt/reef-redir-log/sessions|user-sessions/rtyt/saas-access/errors|user-sessions/rtyt/saas-access/sessions|user-sessions/rtyt/saas-access-intrasearch/errors|user-sessions/rtyt/saas-access-intrasearch/sessions|user-sessions/rtyt/saas-reqans/errors|user-sessions/rtyt/saas-reqans/sessions|user-sessions/rtyt/saas-reqans-intrasearch/errors|user-sessions/rtyt/saas-reqans-intrasearch/sessions|user-sessions/rtyt/suggest-response-log/errors|user-sessions/rtyt/suggest-response-log/sessions|user-sessions/rtyt/turbo-blockstat-log/errors|user-sessions/rtyt/turbo-blockstat-log/sessions|user-sessions/rtyt/uslugi-redir-log/errors|user-sessions/rtyt/uslugi-redir-log/sessions|user-sessions/rtyt/video-error-client-redir/errors|user-sessions/rtyt/video-error-client-redir/sessions|user-sessions/rtyt/video-rum-cls-redir/errors|user-sessions/rtyt/video-rum-cls-redir/sessions|user-sessions/rtyt/video-rum-delta-redir/errors|user-sessions/rtyt/video-rum-delta-redir/sessions|user-sessions/rtyt/video-rum-navigation-redir/errors|user-sessions/rtyt/video-rum-navigation-redir/sessions|user-sessions/rtyt/video-rum-time-redir/errors|user-sessions/rtyt/video-rum-time-redir/sessions|user-sessions/rtyt/video-ucaught-redir/errors|user-sessions/rtyt/video-ucaught-redir/sessions|user-sessions/rtyt/search-error-client-redir-log/errors|user-sessions/rtyt/search-error-client-redir-log/sessions|user-sessions/rtyt/search-rum-time-redir-log/errors|user-sessions/rtyt/search-rum-time-redir-log/sessions|user-sessions/rtyt/yazeka-blockstat-log/errors|user-sessions/rtyt/yazeka-blockstat-log/sessions|user-sessions/rtyt/yazeka-redir-log/errors|user-sessions/rtyt/yazeka-redir-log/sessions|user-sessions/rtyt/reef-reach-goal|user-sessions/rtyt/reef-request-clicks|user-sessions/rtyt/yclid-clicks|user-sessions/rtyt/ysclid-clicks|user-sessions/rtyt/spy-log/late",sensor="WriteBytesPerSec"})
```

### hm_out_bytes

```text
series_sum({project="kikimr",service="pqtabletAggregatedCounters",cluster="lbk|lbkx",host="cluster",TopicPath="yabs-rt/bs-event-log|yabs-rt/bs-pseq-event-log|yabs-rt/bs-pseq-event_bad-log|yabs-rt/bs-pseq-event_debug-log|user-sessions/rt-money/prod/bs-rt-join-undochevent-log|user-sessions/rt-money/prod/rt-join-acted-event-log|user-sessions/rt-money/prod/rt-join-allocation-log|rt_money/prod/narrow-hit-rt/batch|rt_money/prod/narrow-hit-rt/rtb-lite|rt_money/prod/narrow-hit-rt/vendor-click-context-log|yabs-sb/bs-billable-event-log|rt_money/prod/bs-pseq-chevent-log|yabs-sb/bs-partner-billable-event-log|xurma/bs-ssp-checked-log|yabs-sb/bs-action-checked-log|yabs-sb/bs-action-log|rt_money/prod/master-report-pi-stat-input/dsp-checked|user-sessions/rt-money/prod/rt-join-partner-billable-event-log|xurma/bs-dsp-checked-log|rt_money/prod/moneydwh-conversions-input/chtracking|rt_money/prod/moneydwh-conversions-input/postclick|rt_money/prod/moneydwh-conversions-input/visit|rt_money/prod/bs-pseq-chevent-buffered-log|xurma/prod/bs-chtracking-log|rt_money/prod/event-to-antifraud|rt_money/prod/moneydwh-pseq-staging-chevent|rt_money/prod/moneydwh-pseq-staging-dsp|bsexport/bs-undochevent-log|rt_money/prod/bs-pseq-undochevent-log|zenpromo/billed-checked-log|rt_money/prod/hit-product-metrics-input/chevent|rt_money/prod/hit-product-metrics-input/hit|rt_money/prod/hit-product-metrics-log|rt_money/prod/to-stateless-observers|rt_money/prod/narrow-hit-rt/hit-urls|bsexport/bs-undochtracking-log|bsint/bs-undodsp-log|user-sessions/rt-money/prod/pseq-hit-master-errors",sensor="WriteBytesPerSec"})
```
