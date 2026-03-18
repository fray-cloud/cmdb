# Phase 4: Tenancy + Contact Service + Extras

> 논리적 고객 관리, 연락처, 설정 템플릿, 승인 워크플로우
> 관련 Issue: https://github.com/fray-cloud/cmdb/issues/1
> 의존성: Phase 3 완료

---

## 1. Tenancy Service (CMDB 내부 논리적 고객/조직)

> ⚠️ 플랫폼 SaaS 멀티테넌시(Phase 1 Tenant Service)와 별개

### 1.1 도메인 모델
- [ ] Tenant Aggregate Root (name, slug, group_id, description)
- [ ] TenantGroup Entity (name, slug, parent_id — 계층 구조)
- [ ] Domain Events: TenantCreated, TenantUpdated, TenantDeleted
- [ ] 단위 테스트

### 1.2 애플리케이션 & 인프라
- [ ] Tenant CRUD Command/Query Handlers
- [ ] TenantGroup CRUD Command/Query Handlers
- [ ] Event Store + Read Model + Alembic 마이그레이션
- [ ] Kafka 연동 — TenantAssigned 이벤트 발행 → 각 서비스에서 리소스에 Tenant 메타데이터 부착
- [ ] Tenant별 리소스 사용량 리포트 Query (Read Model 집계)

### 1.3 인터페이스
- [ ] Tenant REST API — CRUD
- [ ] TenantGroup REST API — CRUD
- [ ] Tenant 리소스 리포트 API
- [ ] GraphQL API
- [ ] Nginx 라우팅 추가 (/api/v1/tenancy/*)

## 2. Contact Service

### 2.1 도메인 모델
- [ ] Contact Aggregate Root (name, title, phone, email, address, group_id)
- [ ] ContactGroup Entity (name, slug, parent_id)
- [ ] ContactRole Entity (name, slug)
- [ ] ContactAssignment Entity (object_type, object_id, contact_id, role_id)
- [ ] Domain Events: ContactCreated, ContactAssigned
- [ ] 단위 테스트

### 2.2 애플리케이션 & 인프라
- [ ] Contact CRUD Command/Query Handlers
- [ ] ContactGroup, ContactRole CRUD Command/Query Handlers
- [ ] AssignContactCommand / Handler (Cross-service: 다양한 객체에 연락처 할당)
- [ ] Event Store + Read Model + Alembic 마이그레이션
- [ ] Kafka 연동 — ContactAssigned 이벤트 발행/수신

### 2.3 인터페이스
- [ ] Contact REST API — CRUD + 할당
- [ ] ContactGroup, ContactRole REST API — CRUD
- [ ] GraphQL API
- [ ] Nginx 라우팅 추가 (/api/v1/contacts/*)

## 3. 승인 워크플로우 (Notification Service 확장)

> 의존성: Phase 1 Auth Service

- [ ] ChangeRequest Aggregate (requester, object_type, command_payload, status, approvers)
- [ ] ChangeRequestStatus Value Object (pending, approved, rejected, auto_approved)
- [ ] ApprovalRule Entity (object_type, required_approvers, auto_approve_conditions)
- [ ] CreateChangeRequestCommand / Handler — Command를 대기 상태로 보관
- [ ] ApproveChangeRequestCommand / Handler — 승인 시 원래 Command 실행 → Event 발행
- [ ] RejectChangeRequestCommand / Handler
- [ ] 다단계 승인 로직 (모든 승인자 승인 필요 / N명 이상 승인)
- [ ] 자동 승인 규칙 평가 (역할/객체 타입 조건)
- [ ] 승인 대기 큐 Query
- [ ] ChangeRequest REST API — 생성, 조회, 승인, 반려
- [ ] ApprovalRule REST API — CRUD
- [ ] Kafka 연동 — 승인 완료 시 Domain Event 발행

## 4. Configuration Template

- [ ] ConfigTemplate Aggregate (name, template_content, data_source)
- [ ] Jinja2 렌더링 엔진 연동
- [ ] DCIM Read Model 데이터를 변수로 주입
- [ ] 디바이스별 설정 생성 API (device_id → 렌더링된 설정 반환)
- [ ] ConfigTemplate REST API — CRUD + 렌더링

## 5. Frontend

> 의존성: 1~4 인터페이스

- [ ] Tenant 목록/상세/생성/수정 뷰
- [ ] TenantGroup 계층 트리 뷰
- [ ] Contact 목록/상세/생성/수정 뷰
- [ ] Contact 할당 UI (객체 상세 페이지에서 연락처 추가)
- [ ] 승인 워크플로우 UI — 승인 대기 큐, 승인/반려 버튼
- [ ] ChangeRequest 목록/상세 뷰
- [ ] Configuration Template 편집기 + 미리보기
- [ ] Tenancy/Contacts 대시보드 위젯

## 6. 통합 테스트

- [ ] Tenant 할당 → 각 서비스 리소스에 Tenant 메타데이터 부착 E2E
- [ ] Contact 할당 → 다양한 객체 타입에 연락처 할당 E2E
- [ ] 승인 워크플로우 E2E — ChangeRequest 생성 → 승인 → Command 실행 → Event 발행
- [ ] Configuration Template 렌더링 E2E
