# Phase 3: Circuits + Virtualization Service

> 회선 관리, L2VPN, 클러스터, VM + 타 서비스 연동
> 관련 Issue: https://github.com/fray-cloud/cmdb/issues/1
> 의존성: Phase 2 완료 (DCIM Service)

---

## 1. Circuit Service — 도메인 모델

### 1.1 Provider Aggregate
- [ ] Provider Aggregate Root (name, slug, account, asn, tenant_id)
- [ ] ProviderNetwork Entity (name, provider_id)
- [ ] Domain Events: ProviderCreated, ProviderUpdated
- [ ] 단위 테스트

### 1.2 Circuit Aggregate
- [ ] Circuit Aggregate Root (cid, provider_id, type, status, tenant_id)
- [ ] CircuitID Value Object (프로바이더별 고유 식별자)
- [ ] CircuitType Entity (name, slug)
- [ ] CircuitTermination Entity (side: A/Z, site_id, provider_network_id)
- [ ] Domain Events: CircuitProvisioned, CircuitTerminated, CircuitStatusChanged
- [ ] 단위 테스트

### 1.3 L2VPN Aggregate
- [ ] L2VPN Aggregate Root (name, slug, type: VXLAN/EVPN, tenant_id)
- [ ] L2VPNTermination Entity (assigned_object_type, assigned_object_id)
- [ ] 단위 테스트

## 2. Circuit Service — 애플리케이션 & 인프라

> 의존성: 1. 도메인 모델

- [ ] Provider CRUD Command/Query Handlers
- [ ] Circuit CRUD + Terminate Command/Query Handlers
- [ ] L2VPN CRUD Command/Query Handlers
- [ ] Event Store 구현 + Alembic 마이그레이션
- [ ] Read Model 테이블 + 프로젝션
- [ ] Kafka 연동 — DCIM SiteCreated 수신 (회선 종단 가능 사이트)
- [ ] Kafka 연동 — Circuit 이벤트 발행

## 3. Circuit Service — 인터페이스

> 의존성: 2. 애플리케이션 & 인프라

- [ ] Provider REST API — CRUD
- [ ] Circuit REST API — CRUD + Termination
- [ ] L2VPN REST API — CRUD
- [ ] GraphQL API — Provider, Circuit, L2VPN Query/Type
- [ ] Bulk API
- [ ] Nginx 라우팅 추가 (/api/v1/circuits/*)

## 4. Virtualization Service — 도메인 모델

### 4.1 Cluster Aggregate
- [ ] ClusterType Entity (name, slug)
- [ ] ClusterGroup Entity (name, slug)
- [ ] Cluster Aggregate Root (name, type, group, site_id, status, tenant_id)
- [ ] Domain Events: ClusterCreated, ClusterUpdated
- [ ] 단위 테스트

### 4.2 VirtualMachine Aggregate
- [ ] VirtualMachine Aggregate Root (name, cluster_id, status, vcpus, memory, disk, tenant_id)
- [ ] ResourceSpec Value Object (vcpus, memory_mb, disk_gb)
- [ ] VMInterface Entity (name, mac_address, mtu)
- [ ] 리소스 초과 방지 Invariant (클러스터 리소스 한도)
- [ ] Domain Events: VMCreated, VMStatusChanged, VMDecommissioned
- [ ] 단위 테스트

## 5. Virtualization Service — 애플리케이션 & 인프라

> 의존성: 4. 도메인 모델

- [ ] Cluster CRUD Command/Query Handlers
- [ ] VM CRUD + StatusChange Command/Query Handlers
- [ ] VMInterface CRUD Command/Query Handlers
- [ ] Event Store 구현 + Alembic 마이그레이션
- [ ] Read Model 테이블 + 프로젝션
- [ ] Kafka 연동 — DCIM SiteCreated 수신 (클러스터-사이트 연결)
- [ ] Kafka 연동 — IPAM IPAddressAssigned 수신 → VM 인터페이스 IP 업데이트
- [ ] Kafka 연동 — VMCreated 발행 → IPAM IP 할당 가능 대상 등록

## 6. Virtualization Service — 인터페이스

> 의존성: 5. 애플리케이션 & 인프라

- [ ] Cluster REST API — CRUD
- [ ] VM REST API — CRUD + 상태 변경
- [ ] VMInterface REST API — CRUD
- [ ] GraphQL API — Cluster, VM Query/Type + IPAM 연동 쿼리
- [ ] Bulk API
- [ ] Nginx 라우팅 추가 (/api/v1/virtualization/*)

## 7. Frontend

> 의존성: 3, 6. 인터페이스

- [ ] Provider 목록/상세/생성/수정 뷰
- [ ] Circuit 목록/상세/생성/수정 뷰 + Termination 관리
- [ ] L2VPN 목록/상세 뷰
- [ ] Cluster 목록/상세/생성/수정 뷰
- [ ] VM 목록/상세/생성/수정 뷰 + 인터페이스/IP 관리
- [ ] Circuits/Virtualization 대시보드 위젯

## 8. 통합 테스트

- [ ] Circuit 생성 → Termination → DCIM Site 연결 E2E
- [ ] VM 생성 → Cluster 할당 → IP 할당(IPAM 연동) E2E
- [ ] Cross-service 이벤트 흐름 검증 (Circuit ↔ DCIM, VM ↔ IPAM)
