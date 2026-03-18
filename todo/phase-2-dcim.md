# Phase 2: DCIM Service

> 사이트, 랙, 디바이스, 컴포넌트, 케이블링, 전원 관리 + IPAM 연동
> 관련 Issue: https://github.com/fray-cloud/cmdb/issues/1
> 의존성: Phase 1 완료

---

## 1. DCIM 도메인 모델

### 1.1 Site Aggregate
- [ ] Region Value Object Tree (재귀적 중첩 계층)
- [ ] SiteGroup Entity
- [ ] Site Aggregate Root (name, status, region, group, physical_address, gps_coordinates, tenant_id)
- [ ] PhysicalAddress Value Object (address, city, country, postal_code)
- [ ] GPSCoordinates Value Object (latitude, longitude)
- [ ] Location Entity (계층형 — building, floor, room)
- [ ] Domain Events: SiteCreated, SiteUpdated, SiteDecommissioned
- [ ] 단위 테스트

### 1.2 Rack Aggregate
- [ ] Rack Aggregate Root (name, site_id, location_id, u_height, status, role, tenant_id)
- [ ] RackUnit Value Object (U 위치)
- [ ] 장비 배치 Invariant (U 겹침 방지)
- [ ] 랙 예약 Entity (units, user, description)
- [ ] Domain Events: RackCreated, DeviceMounted, DeviceUnmounted
- [ ] 단위 테스트

### 1.3 Device Aggregate
- [ ] Manufacturer Entity (name, slug)
- [ ] DeviceType Aggregate (manufacturer, model, u_height, component_templates)
- [ ] Device Aggregate Root (name, device_type, site_id, rack_id, position, status, role, serial, asset_tag, platform, tenant_id)
- [ ] DeviceStatus Value Object (Active, Planned, Staged, Failed, Decommissioning, Inventory)
- [ ] SerialNumber Value Object
- [ ] AssetTag Value Object
- [ ] Platform Entity (name, slug, manufacturer)
- [ ] DeviceRole Entity (name, slug, color)
- [ ] Domain Events: DeviceCreated, DeviceStatusChanged, DeviceDecommissioned
- [ ] 단위 테스트

### 1.4 디바이스 컴포넌트 (Device 하위 Entity)
- [ ] Interface Entity (name, type, speed, mac_address, mtu, mode, tagged_vlans, untagged_vlan)
- [ ] InterfaceType Value Object (1GE, 10GE, 25GE, 40GE, 100GE, SFP 등)
- [ ] MACAddress Value Object
- [ ] ConsolePort Entity, ConsoleServerPort Entity
- [ ] PowerPort Entity, PowerOutlet Entity
- [ ] FrontPort Entity, RearPort Entity (패치 패널 패스스루)
- [ ] ModuleBay Entity (모듈 슬롯)
- [ ] DeviceBay Entity (블레이드 섀시)
- [ ] InventoryItem Entity (name, manufacturer, part_id, serial, asset_tag)
- [ ] 단위 테스트

### 1.5 Cable Aggregate
- [ ] Cable Aggregate Root (type, color, length, label, status)
- [ ] CableTermination Value Object (termination_type, termination_id, side: A/Z)
- [ ] Cable Tracing Domain Service (연결 경로 그래프 탐색 알고리즘)
- [ ] 다중 종단 케이블 (브레이크아웃) 로직
- [ ] Wireless Link Entity
- [ ] Domain Events: CableConnected, CableDisconnected
- [ ] 단위 테스트

### 1.6 Power Aggregate
- [ ] PowerPanel Aggregate Root (name, site_id, location_id)
- [ ] PowerFeed Entity (panel_id, name, status, type, supply, phase, voltage, amperage)
- [ ] 전원 포트 → 아울렛 연결 로직
- [ ] 단위 테스트

## 2. DCIM 애플리케이션 레이어 (CQRS)

> 의존성: 1. DCIM 도메인 모델

### 2.1 Command Handlers
- [ ] Site CRUD Commands (Create, Update, Delete, Decommission)
- [ ] Location CRUD Commands
- [ ] Rack CRUD Commands + MountDevice / UnmountDevice
- [ ] Device CRUD Commands + ChangeStatus
- [ ] DeviceType CRUD Commands
- [ ] Interface CRUD Commands
- [ ] Cable Connect / Disconnect Commands
- [ ] PowerPanel, PowerFeed CRUD Commands
- [ ] Bulk Commands (벌크 생성/수정/삭제)

### 2.2 Query Handlers
- [ ] Site 목록/상세 Query (Region 계층 포함)
- [ ] Rack 목록/상세 Query (엘리베이션 데이터 포함)
- [ ] Rack 활용률 Query
- [ ] Device 목록/상세 Query (컴포넌트 포함)
- [ ] Interface 목록 Query (디바이스별)
- [ ] Cable Trace Query (연결 경로 조회)
- [ ] 글로벌 검색 Query (DCIM 범위)

## 3. DCIM 인프라스트럭처

> 의존성: 2. 애플리케이션 레이어

### 3.1 Persistence
- [ ] Site, Rack, Device, Cable, Power Event Store 구현
- [ ] Alembic 마이그레이션 — DCIM events/snapshots 테이블

### 3.2 Read Model
- [ ] Site, Location, Rack Read Model 테이블 + 마이그레이션
- [ ] Device, DeviceType, Interface Read Model 테이블 + 마이그레이션
- [ ] Cable Read Model 테이블 + 마이그레이션 (그래프 인접 리스트)
- [ ] Power Read Model 테이블 + 마이그레이션
- [ ] Event → Read Model 프로젝션 구현
- [ ] Redis 캐시 (랙 엘리베이션, 디바이스 상태)

### 3.3 Kafka 연동 — Cross-service 이벤트
- [ ] DCIM → Kafka 이벤트 발행 (dcim.events)
- [ ] IPAM → DCIM 이벤트 수신: IPAddressAssigned → 디바이스 인터페이스 IP 업데이트
- [ ] DCIM → IPAM 이벤트 발행: DeviceCreated → IP 할당 가능 대상 등록
- [ ] DCIM → IPAM 이벤트 발행: DeviceDecommissioned → 관련 IP 해제 트리거

## 4. DCIM 인터페이스

> 의존성: 3. 인프라스트럭처

### 4.1 REST API
- [ ] Region API, Site API, Location API — CRUD
- [ ] Rack API — CRUD + 엘리베이션 + 활용률
- [ ] Device API — CRUD + 상태 변경
- [ ] DeviceType API, Manufacturer API — CRUD
- [ ] Interface API — CRUD + VLAN 할당
- [ ] Cable API — 연결/해제 + Cable Trace
- [ ] PowerPanel, PowerFeed API — CRUD
- [ ] Bulk API
- [ ] OpenAPI 문서 확인

### 4.2 GraphQL API
- [ ] Site, Rack, Device, Cable Query/Type 정의
- [ ] 중첩 쿼리 (Site → Racks → Devices → Interfaces)
- [ ] IPAM 연동 쿼리 (Device → Primary IP, Interface → IP Addresses)

## 5. Nginx 라우팅 추가

> 의존성: 4.1 REST API

- [ ] /api/v1/dcim/* → DCIM Service upstream 라우팅 추가

## 6. Frontend — DCIM UI

> 의존성: 4. DCIM 인터페이스

- [ ] Site 목록/상세/생성/수정 뷰
- [ ] Region 계층 트리 뷰
- [ ] Rack 목록/상세/생성/수정 뷰
- [ ] 랙 엘리베이션 시각화 (전면/후면)
- [ ] Device 목록/상세/생성/수정 뷰
- [ ] 디바이스 컴포넌트 탭 (Interfaces, Console, Power 등)
- [ ] Cable Trace 시각화
- [ ] Power 관리 뷰
- [ ] DCIM 대시보드 위젯 추가

## 7. 통합 테스트

- [ ] Device 생성 → Rack 배치 → Interface 추가 → Cable 연결 E2E
- [ ] DCIM ↔ IPAM 이벤트 연동 테스트 (Device → IP 할당)
- [ ] Cable Trace 경로 탐색 테스트
- [ ] Rack 엘리베이션 U 겹침 방지 테스트
