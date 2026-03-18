# CMDB Platform — TODO

> PRD Issue: https://github.com/fray-cloud/cmdb/issues/1

| Phase | 파일 | 범위 | 의존성 |
|-------|------|------|--------|
| **Phase 1** | [phase-1-foundation-ipam.md](./phase-1-foundation-ipam.md) | 프로젝트 초기화, 인프라, 공통 라이브러리(CQRS/ES), Auth, Tenant, Nginx, Event, Webhook, IPAM, Frontend 기반 | - |
| **Phase 2** | [phase-2-dcim.md](./phase-2-dcim.md) | 사이트, 랙, 디바이스, 컴포넌트, 케이블링, 전원 + IPAM 연동 | Phase 1 |
| **Phase 3** | [phase-3-circuits-virtualization.md](./phase-3-circuits-virtualization.md) | 회선, 프로바이더, L2VPN, 클러스터, VM + Cross-service 연동 | Phase 2 |
| **Phase 4** | [phase-4-tenancy-contacts-extras.md](./phase-4-tenancy-contacts-extras.md) | 논리적 Tenant, 연락처, 승인 워크플로우, Config Template | Phase 3 |
| **Phase 5** | [phase-5-plugins-advanced.md](./phase-5-plugins-advanced.md) | 플러그인 시스템, 커스텀 스크립트, 관측성, K8s 배포, 보안 강화 | Phase 4 |
