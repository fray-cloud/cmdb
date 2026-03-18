# Phase 1: Foundation + IPAM Service

> 플랫폼 공통 인프라, 인증/인가, CQRS/ES 기반 구조, IPAM Core Domain 구현
> 관련 Issue: https://github.com/fray-cloud/cmdb/issues/1

---

## 1. 프로젝트 초기화

- [ ] 모노레포 구조 설정 (서비스별 디렉토리)
  ```
  /services/ipam/
  /services/auth/
  /services/tenant/
  /services/event/
  /services/webhook/
  /frontend/
  /infrastructure/nginx/
  /infrastructure/docker/
  /shared/  (공통 라이브러리)
  ```
- [ ] Python 프로젝트 초기화 — pyproject.toml, Poetry/uv 설정
- [ ] Next.js 프론트엔드 프로젝트 초기화
- [ ] 공통 린트/포맷 설정 (ruff, black, eslint, prettier)
- [ ] Git hooks 설정 (pre-commit)
- [ ] CI 파이프라인 기초 설정 (GitHub Actions — lint, test)

## 2. 인프라 세팅 (Docker Compose)

> 의존성: 1. 프로젝트 초기화

- [ ] Docker Compose 기본 구성 파일 작성
- [ ] PostgreSQL 컨테이너 설정 (서비스별 DB 분리)
- [ ] Kafka + Zookeeper (또는 KRaft) 컨테이너 설정
- [ ] Redis 컨테이너 설정
- [ ] Nginx 리버스 프록시 컨테이너 + 기본 설정
- [ ] 서비스별 Dockerfile 작성 (FastAPI 기반)
- [ ] Frontend Dockerfile 작성 (Next.js)
- [ ] docker-compose.dev.yml (개발용 핫리로드, 볼륨 마운트)
- [ ] 환경변수 관리 (.env.example, .env.dev)

## 3. 공통 라이브러리 (shared/)

> 의존성: 1. 프로젝트 초기화

### 3.1 CQRS 프레임워크
- [ ] Command 베이스 클래스 정의 (Command, CommandHandler)
- [ ] Query 베이스 클래스 정의 (Query, QueryHandler)
- [ ] Command Bus 구현 (Command → Handler 디스패칭)
- [ ] Query Bus 구현 (Query → Handler 디스패칭)

### 3.2 Event Sourcing 프레임워크
- [ ] Domain Event 베이스 클래스 정의 (event_id, aggregate_id, timestamp, version, payload)
- [ ] Aggregate Root 베이스 클래스 구현 (apply_event, load_from_history, uncommitted_events)
- [ ] Event Store 인터페이스 정의 (append, load_stream, load_snapshot)
- [ ] Event Store PostgreSQL 구현 (events 테이블, snapshots 테이블)
- [ ] Event Store DB 마이그레이션 (Alembic)
- [ ] Snapshot 전략 구현 (N 이벤트마다 스냅샷 생성)

### 3.3 Kafka 메시징
- [ ] Kafka Producer 래퍼 (Domain Event → Kafka Topic 발행)
- [ ] Kafka Consumer 래퍼 (Topic 구독 → Event Handler 디스패칭)
- [ ] 이벤트 직렬화/역직렬화 (JSON Schema, Avro 등 결정)
- [ ] Dead Letter Queue 처리
- [ ] Consumer Group 관리

### 3.4 공통 도메인 빌딩블록
- [ ] Entity 베이스 클래스 (id, created_at, updated_at)
- [ ] Value Object 베이스 클래스 (불변, 동등성 비교)
- [ ] Repository 인터페이스 베이스 클래스
- [ ] Domain Service 베이스 클래스
- [ ] Domain Exception 계층 구조

### 3.5 Custom Fields & Tags 공통 모듈
- [ ] CustomField 모델 정의 (name, type, required, default, choices, validation)
- [ ] CustomField 값 저장 전략 (JSONB 컬럼)
- [ ] CustomField 유효성 검증 로직
- [ ] Tag 모델 정의 (name, slug, color)
- [ ] Tag 할당 모델 (다대다 관계)
- [ ] CustomField/Tag 필터링 유틸리티

### 3.6 API 공통 모듈
- [ ] FastAPI 미들웨어 — Tenant 식별 (요청 헤더/도메인 기반)
- [ ] FastAPI 미들웨어 — Correlation ID 생성/전파
- [ ] 페이지네이션 유틸리티 (cursor-based, offset-based)
- [ ] 필터링 유틸리티 (쿼리 파라미터 → 필터 변환)
- [ ] 정렬 유틸리티
- [ ] 에러 응답 표준 포맷 (RFC 7807 Problem Details)
- [ ] OpenAPI 스키마 커스텀 설정

## 4. Tenant Service

> 의존성: 2. 인프라 세팅, 3.4 공통 도메인 빌딩블록

### 4.1 도메인 모델
- [ ] Tenant Aggregate 정의 (id, name, slug, status, settings, db_config)
- [ ] TenantStatus Value Object (active, suspended, deleted)
- [ ] TenantSettings Value Object (custom_domain, logo_url, theme)
- [ ] Domain Events: TenantCreated, TenantSuspended, TenantDeleted

### 4.2 애플리케이션 레이어
- [ ] CreateTenantCommand / Handler — DB 프로비저닝 포함
- [ ] SuspendTenantCommand / Handler
- [ ] UpdateTenantSettingsCommand / Handler
- [ ] GetTenantQuery / Handler

### 4.3 인프라스트럭처
- [ ] Tenant Repository PostgreSQL 구현
- [ ] Tenant DB 프로비저닝 로직 (새 PostgreSQL DB 생성 + Alembic 마이그레이션 실행)
- [ ] Tenant DB 연결 풀 관리 (요청별 Tenant DB 라우팅)
- [ ] Alembic 멀티 DB 마이그레이션 전략

### 4.4 인터페이스
- [ ] Tenant REST API 엔드포인트 (CRUD)
- [ ] Tenant 식별 미들웨어 (요청 → Tenant DB 라우팅)

## 5. Auth Service

> 의존성: 4. Tenant Service

### 5.1 도메인 모델
- [ ] User Aggregate 정의 (id, email, password_hash, tenant_id, status, roles)
- [ ] Role Entity 정의 (name, permissions)
- [ ] Permission Value Object (object_type, actions: view/add/change/delete)
- [ ] Group Entity 정의 (name, roles)
- [ ] APIToken Entity 정의 (key_hash, scopes, expires_at, allowed_ips)
- [ ] Domain Events: UserCreated, RoleAssigned, TokenGenerated

### 5.2 애플리케이션 레이어
- [ ] RegisterUserCommand / Handler
- [ ] LoginCommand / Handler (JWT 발급)
- [ ] RefreshTokenCommand / Handler
- [ ] CreateAPITokenCommand / Handler
- [ ] AssignRoleCommand / Handler
- [ ] CheckPermissionQuery / Handler

### 5.3 인프라스트럭처
- [ ] User Repository PostgreSQL 구현
- [ ] 비밀번호 해싱 (bcrypt/argon2)
- [ ] JWT 토큰 발급/검증 (access + refresh token)
- [ ] SSO — OIDC Provider 연동 (Google, Azure AD)
- [ ] SSO — SAML 2.0 연동 (Azure AD, Okta)
- [ ] MFA — TOTP 구현

### 5.4 인터페이스
- [ ] Auth REST API — 로그인, 회원가입, 토큰 갱신, 로그아웃
- [ ] User REST API — CRUD, 역할 관리
- [ ] Role/Permission REST API — CRUD
- [ ] API Token REST API — 생성, 조회, 삭제
- [ ] SSO 콜백 엔드포인트

## 6. Nginx API Gateway

> 의존성: 2. 인프라 세팅, 5. Auth Service

- [ ] 서비스별 upstream 정의 (auth, tenant, ipam 등)
- [ ] URL prefix 기반 라우팅 규칙 (/api/v1/ipam/*, /api/v1/auth/* 등)
- [ ] auth_request 서브리퀘스트로 JWT 검증 (Auth Service 연동)
- [ ] Rate Limiting 설정 (limit_req_zone — Tenant별, IP별)
- [ ] CORS 설정 (allowed origins, methods, headers)
- [ ] SSL/TLS 설정 (개발: self-signed, 프로덕션: Let's Encrypt)
- [ ] Access log / Error log 포맷 설정
- [ ] Upstream health check 설정
- [ ] 정적 파일 서빙 (Next.js 빌드 결과물)

## 7. Event Service

> 의존성: 3.2 Event Sourcing 프레임워크, 3.3 Kafka 메시징

### 7.1 도메인
- [ ] EventStream Aggregate (stream_id, aggregate_type, version)
- [ ] Snapshot 관리 로직

### 7.2 인프라
- [ ] Event Store PostgreSQL 스키마 (events, snapshots 테이블) — 마이그레이션
- [ ] Kafka Consumer — 모든 서비스의 Domain Event 수신 → Event Store 저장
- [ ] Change Log 생성 (Event → 변경 이력 변환)
- [ ] Change Log 조회 API

### 7.3 인터페이스
- [ ] Change Log REST API (객체별 변경 이력 조회, 필터링)
- [ ] Event Replay API (특정 Aggregate의 이벤트 스트림 조회)

## 8. IPAM Service — 도메인 모델

> 의존성: 3. 공통 라이브러리

### 8.1 Prefix Aggregate
- [ ] Prefix Aggregate Root 구현 (prefix, vrf_id, status, role, tenant_id, description)
- [ ] PrefixNetwork Value Object (IPv4/IPv6 네트워크 주소 — python ipaddress 활용)
- [ ] PrefixStatus Value Object (Active, Reserved, Deprecated, Container)
- [ ] 계층형 Prefix 도메인 로직 (상위/하위 서브넷 관계 Invariant)
- [ ] Prefix 활용률 계산 Domain Service
- [ ] 사용 가능한 하위 Prefix 탐색 Domain Service
- [ ] Domain Events: PrefixCreated, PrefixUpdated, PrefixDeleted, PrefixStatusChanged
- [ ] 단위 테스트: Prefix Aggregate 비즈니스 룰

### 8.2 IPAddress Aggregate
- [ ] IPAddress Aggregate Root 구현 (address, vrf_id, status, dns_name, tenant_id)
- [ ] IPAddressValue Value Object (IPv4/IPv6 주소)
- [ ] IPAddressStatus Value Object (Active, Reserved, Deprecated, DHCP, SLAAC)
- [ ] IP 중복 검사 Domain Service (VRF Scope 내)
- [ ] 사용 가능한 IP 자동 탐색 Domain Service
- [ ] Domain Events: IPAddressCreated, IPAddressAssigned, IPAddressReleased, IPAddressStatusChanged
- [ ] 단위 테스트: IPAddress Aggregate 비즈니스 룰

### 8.3 IPRange Aggregate
- [ ] IPRange Aggregate Root 구현 (start_address, end_address, vrf_id, status)
- [ ] IPRangeBound Value Object
- [ ] 범위 내 할당 상태 추적 로직
- [ ] 단위 테스트

### 8.4 VRF Aggregate
- [ ] VRF Aggregate Root 구현 (name, rd, tenant_id, description)
- [ ] RouteDistinguisher Value Object
- [ ] RouteTarget Entity (name, type: import/export)
- [ ] VRF 간 IP 중복 허용 Invariant
- [ ] Domain Events: VRFCreated, VRFUpdated, VRFDeleted
- [ ] 단위 테스트

### 8.5 VLAN Aggregate
- [ ] VLAN Aggregate Root 구현 (vid, name, group_id, status, role, tenant_id)
- [ ] VLANId Value Object (1-4094 범위 검증)
- [ ] VLANGroup Entity (name, scope)
- [ ] VLAN-to-Prefix 연결 로직
- [ ] Domain Events: VLANCreated, VLANUpdated, VLANDeleted
- [ ] 단위 테스트

### 8.6 RIR Aggregate / ASN
- [ ] RIR Entity (name, slug, description)
- [ ] Aggregate (RIR 할당) Aggregate Root 구현 (prefix, rir_id, tenant_id)
- [ ] ASN Entity (asn, rir_id, tenant_id, description)
- [ ] ASN Value Object (16-bit/32-bit 범위 검증)
- [ ] 단위 테스트

### 8.7 FHRP Group Aggregate
- [ ] FHRPGroup Aggregate Root (protocol: VRRP/HSRP/CARP/GLBP, group_id, auth_type)
- [ ] 가상 IP 할당 로직
- [ ] 단위 테스트

### 8.8 Service Entity
- [ ] Service Entity (name, protocol, ports, device_id/vm_id)
- [ ] ServiceProtocol Value Object (TCP, UDP, SCTP)
- [ ] 단위 테스트

## 9. IPAM Service — 애플리케이션 레이어 (CQRS)

> 의존성: 8. IPAM 도메인 모델

### 9.1 Command Handlers (Write Side)
- [ ] CreatePrefixCommand / Handler
- [ ] UpdatePrefixCommand / Handler
- [ ] DeletePrefixCommand / Handler
- [ ] ChangePrefixStatusCommand / Handler
- [ ] CreateIPAddressCommand / Handler
- [ ] AssignIPAddressCommand / Handler
- [ ] ReleaseIPAddressCommand / Handler
- [ ] CreateVRFCommand / Handler, UpdateVRFCommand / Handler, DeleteVRFCommand / Handler
- [ ] CreateVLANCommand / Handler, UpdateVLANCommand / Handler, DeleteVLANCommand / Handler
- [ ] CreateIPRangeCommand / Handler, UpdateIPRangeCommand / Handler
- [ ] CreateRIRAggregateCommand / Handler
- [ ] CreateASNCommand / Handler
- [ ] CreateFHRPGroupCommand / Handler
- [ ] BulkCreateCommand / Handler (범용 벌크 처리)

### 9.2 Query Handlers (Read Side)
- [ ] ListPrefixesQuery / Handler (필터링, 페이지네이션)
- [ ] GetPrefixDetailQuery / Handler (계층 구조 포함)
- [ ] GetPrefixUtilizationQuery / Handler
- [ ] GetAvailablePrefixesQuery / Handler
- [ ] ListIPAddressesQuery / Handler
- [ ] GetIPAddressDetailQuery / Handler
- [ ] GetAvailableIPsQuery / Handler
- [ ] ListVRFsQuery / Handler, GetVRFDetailQuery / Handler
- [ ] ListVLANsQuery / Handler, GetVLANDetailQuery / Handler
- [ ] ListIPRangesQuery / Handler
- [ ] ListASNsQuery / Handler
- [ ] GlobalSearchQuery / Handler (IPAM 범위 내 전문 검색)

### 9.3 Application Services
- [ ] IPAM Application Service (Command/Query Bus 오케스트레이션)
- [ ] Custom Fields 연동 (Command에 custom_fields 포함, Read Model에 반영)
- [ ] Tags 연동 (Command에 tags 포함, Read Model에 반영)

## 10. IPAM Service — 인프라스트럭처

> 의존성: 9. 애플리케이션 레이어

### 10.1 Persistence (Write Side)
- [ ] Prefix Event Store 구현 (이벤트 append, 스냅샷)
- [ ] IPAddress Event Store 구현
- [ ] VRF Event Store 구현
- [ ] VLAN Event Store 구현
- [ ] IPRange, RIR Aggregate, ASN, FHRP Event Store 구현
- [ ] Alembic 마이그레이션 — IPAM events/snapshots 테이블

### 10.2 Read Model (Query Side)
- [ ] Prefix Read Model 테이블 설계 + 마이그레이션
- [ ] IPAddress Read Model 테이블 설계 + 마이그레이션
- [ ] VRF, VLAN, IPRange Read Model 테이블 설계 + 마이그레이션
- [ ] Event Handler → Read Model 프로젝션 구현 (Event → Read Model 업데이트)
- [ ] Redis 캐시 레이어 (자주 조회되는 Prefix/IP 활용률)

### 10.3 Kafka 연동
- [ ] IPAM Domain Event → Kafka Topic 발행 (ipam.events)
- [ ] Cross-service Event 수신 Consumer (DCIM DeviceCreated 등 — Phase 2 준비)

## 11. IPAM Service — 인터페이스

> 의존성: 10. 인프라스트럭처

### 11.1 REST API
- [ ] Prefix API — CRUD + 활용률 + 가용 Prefix 조회
- [ ] IPAddress API — CRUD + 할당/해제 + 가용 IP 조회
- [ ] VRF API — CRUD + Route Target 관리
- [ ] VLAN API — CRUD + VLAN Group 관리
- [ ] IPRange API — CRUD + 활용률
- [ ] RIR Aggregate API — CRUD
- [ ] ASN API — CRUD
- [ ] FHRP Group API — CRUD
- [ ] Service API — CRUD
- [ ] Bulk API — 벌크 생성/수정/삭제
- [ ] OpenAPI 문서 자동 생성 확인

### 11.2 GraphQL API
- [ ] Prefix Query/Type 정의
- [ ] IPAddress Query/Type 정의
- [ ] VRF, VLAN, IPRange Query/Type 정의
- [ ] 중첩 쿼리 (Prefix → IPAddresses, VRF → Prefixes 등)
- [ ] GraphQL Playground 설정

## 12. Webhook Service

> 의존성: 3.3 Kafka 메시징

- [ ] Webhook Aggregate 정의 (url, secret, event_types, status)
- [ ] Webhook 등록/수정/삭제 API
- [ ] Kafka Consumer — Domain Event 수신 → 조건 매칭 → HTTP POST 발송
- [ ] 이벤트 규칙 엔진 (event_type 필터, 조건부 트리거)
- [ ] 재시도 로직 (exponential backoff)
- [ ] Dead Letter Queue 처리
- [ ] Webhook 발송 로그 조회 API

## 13. 검색 및 필터링

> 의존성: 10.2 Read Model

- [ ] IPAM Read Model 기반 상세 필터 구현 (status, vrf, tenant, role, tag 등)
- [ ] Saved Filters 모델 및 API (사용자별 필터 프리셋 저장)
- [ ] 글로벌 검색 — IPAM 범위 내 전문 검색 (PostgreSQL full-text search)

## 14. 저널링

> 의존성: 3.4 공통 도메인 빌딩블록

- [ ] Journal Entry 모델 (object_type, object_id, entry_type, comment, user_id, created_at)
- [ ] Journal Entry API — 생성, 조회 (객체별)
- [ ] entry_type: info, success, warning, danger

## 15. 데이터 가져오기/내보내기

> 의존성: 11. IPAM 인터페이스

- [ ] CSV Import — CSV 파싱 → Command 배치 변환 → 실행
- [ ] CSV/JSON/YAML Export — Read Model 조회 → 포맷 변환
- [ ] Jinja2 Export 템플릿 엔진 — 커스텀 템플릿 등록/렌더링
- [ ] Bulk Edit API — 다중 객체 일괄 수정 Command

## 16. Frontend 기반 (Next.js)

> 의존성: 6. Nginx, 11. IPAM REST API

### 16.1 프로젝트 구조
- [ ] Next.js App Router 구조 설정
- [ ] UI 컴포넌트 라이브러리 선정 및 설정 (shadcn/ui, Tailwind CSS 등)
- [ ] API 클라이언트 설정 (axios/fetch 래퍼, 인증 토큰 자동 첨부)
- [ ] 인증 상태 관리 (JWT 저장, 자동 갱신)
- [ ] 다크 모드 / 라이트 모드 토글

### 16.2 인증 UI
- [ ] 로그인 페이지
- [ ] 회원가입 페이지
- [ ] SSO 로그인 버튼 (Google, Azure AD)
- [ ] 비밀번호 재설정

### 16.3 IPAM UI
- [ ] Prefix 목록 뷰 (테이블, 필터, 페이지네이션)
- [ ] Prefix 상세 뷰 (계층 구조 시각화, 활용률, 관련 IP)
- [ ] Prefix 생성/수정 폼
- [ ] IP Address 목록/상세/생성/수정 뷰
- [ ] VRF 목록/상세/생성/수정 뷰
- [ ] VLAN 목록/상세/생성/수정 뷰
- [ ] IPRange, ASN, FHRP 뷰
- [ ] 글로벌 검색 UI
- [ ] 변경 이력 타임라인 뷰
- [ ] 저널 엔트리 UI (노트 추가/조회)

### 16.4 대시보드
- [ ] IPAM 대시보드 (Prefix/IP 활용률 요약, 최근 변경)
- [ ] 위젯 기반 레이아웃

## 17. 통합 테스트

> 의존성: 모든 서비스

- [ ] IPAM E2E 테스트 — Prefix 생성 → Event Store 기록 → Read Model 반영 → API 조회
- [ ] Auth E2E 테스트 — 회원가입 → 로그인 → JWT → API 호출 → 권한 검증
- [ ] Tenant 격리 테스트 — Tenant A 데이터가 Tenant B에서 조회 불가
- [ ] Kafka 이벤트 흐름 테스트 — Domain Event → Kafka → Event Store 저장
- [ ] Webhook 발송 테스트 — Event → Webhook 매칭 → HTTP POST 검증
