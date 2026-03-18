# Phase 5: Plugin System + 고급 기능

> 플러그인 아키텍처, 커스텀 스크립트, 관측성 고도화
> 관련 Issue: https://github.com/fray-cloud/cmdb/issues/1
> 의존성: Phase 4 완료

---

## 1. Plugin System

### 1.1 아키텍처 설계
- [ ] 플러그인 인터페이스/계약 정의 (진입점, 라이프사이클 훅)
- [ ] 플러그인 등록/해제 메커니즘
- [ ] 플러그인 격리 전략 (서비스별 독립 실행 or 사이드카)
- [ ] 플러그인 설정 스키마 정의

### 1.2 확장 포인트
- [ ] 커스텀 데이터 모델 추가 (플러그인 자체 Aggregate + Event Store)
- [ ] REST API 확장 (플러그인 전용 엔드포인트 등록)
- [ ] GraphQL 확장 (플러그인 Type/Query 등록)
- [ ] UI 확장 — 네비게이션 메뉴 항목 추가
- [ ] UI 확장 — 기존 객체 상세 페이지에 탭/섹션 추가
- [ ] Event 구독 — 플러그인이 Domain Event 수신하여 커스텀 로직 실행

### 1.3 플러그인 관리
- [ ] 플러그인 관리 REST API (설치, 활성화, 비활성화, 삭제)
- [ ] 플러그인 관리 UI
- [ ] 플러그인 마켓플레이스 기초 (메타데이터, 버전 관리)
- [ ] 플러그인 DB 마이그레이션 자동화

## 2. Custom Script

- [ ] Script 실행 엔진 (Python 샌드박스 환경)
- [ ] Script 모델 (name, source_code, description, scheduled)
- [ ] Script 실행 API (동기/비동기 실행)
- [ ] Script 실행 결과 저장 및 조회
- [ ] Script UI — 코드 편집기 + 실행 버튼 + 결과 뷰
- [ ] ORM/API 접근 제한 (읽기 전용 vs 쓰기 가능 스크립트 구분)
- [ ] 외부 데이터 임포트 스크립트 템플릿

## 3. 관측성 (Observability) 고도화

### 3.1 분산 트레이싱
- [ ] OpenTelemetry SDK 연동 (각 서비스)
- [ ] Trace ID 전파 (HTTP 헤더, Kafka 메시지 헤더)
- [ ] Jaeger/Zipkin 수집기 설정 (Docker Compose)
- [ ] 트레이싱 대시보드

### 3.2 중앙 집중 로깅
- [ ] 구조화된 로그 포맷 (JSON) — 각 서비스
- [ ] 로그 수집기 설정 (Fluentd/Fluent Bit → Elasticsearch or Loki)
- [ ] 로그 조회 대시보드 (Kibana or Grafana)

### 3.3 메트릭
- [ ] Prometheus 메트릭 엔드포인트 (각 서비스 /metrics)
- [ ] 커스텀 비즈니스 메트릭 (API 호출 수, 이벤트 처리량, Tenant별 사용량)
- [ ] Grafana 대시보드 — 서비스 헬스, API 지연시간, Kafka lag
- [ ] 알림 규칙 설정 (서비스 다운, 높은 에러율, Kafka consumer lag)

### 3.4 헬스체크
- [ ] 서비스별 /health 엔드포인트 (DB, Kafka, Redis 연결 상태)
- [ ] 서비스 헬스 종합 대시보드
- [ ] Nginx upstream health check와 연동

## 4. Kubernetes 배포

- [ ] Helm Chart 작성 (서비스별)
- [ ] ConfigMap / Secret 관리
- [ ] HPA (Horizontal Pod Autoscaler) 설정
- [ ] PDB (Pod Disruption Budget) 설정
- [ ] Ingress Controller 설정 (Nginx Ingress)
- [ ] Persistent Volume 설정 (PostgreSQL, Kafka)
- [ ] Kafka on K8s (Strimzi 또는 Confluent Operator)
- [ ] DB 마이그레이션 Job (Alembic — init container or Job)
- [ ] CI/CD 파이프라인 — K8s 배포 자동화

## 5. 성능 최적화

- [ ] Read Model 쿼리 최적화 (인덱스, 쿼리 플랜 분석)
- [ ] Event Store Snapshot 주기 튜닝
- [ ] Kafka Consumer 병렬 처리 최적화 (파티션, consumer 수)
- [ ] Redis 캐시 히트율 모니터링 및 튜닝
- [ ] API 응답 시간 프로파일링 및 병목 제거
- [ ] 대량 임포트 배치 사이즈 최적화

## 6. 보안 강화

- [ ] 서비스 간 mTLS 설정
- [ ] API 입력값 검증 강화 (Pydantic strict mode)
- [ ] SQL Injection / XSS 방어 점검
- [ ] Rate Limiting 세밀화 (엔드포인트별)
- [ ] 감사 로그 무결성 검증 (Event Store 체인 해시)
- [ ] 보안 스캔 CI 연동 (Bandit, Trivy)

## 7. 통합 테스트

- [ ] 플러그인 설치 → 커스텀 모델 생성 → API 호출 E2E
- [ ] Custom Script 실행 E2E
- [ ] OpenTelemetry 트레이스 전파 검증 (요청 → 서비스 간 → Kafka → 응답)
- [ ] K8s 배포 스모크 테스트
- [ ] 부하 테스트 (Locust/k6 — API 응답 시간 SLA 검증)
