# CLAUDE.ko.md

이 파일은 CLAUDE.md의 한국어 번역본으로, 사람이 읽기 위한 용도입니다.
Claude Code는 이 파일이 아닌 CLAUDE.md를 참조합니다.

## 빌드 & 개발 명령어

```bash
# 의존성
uv sync                    # 워크스페이스 전체 의존성 설치

# 테스트
uv run pytest              # 전체 테스트 실행
make test                  # 위와 동일
uv run pytest services/ipam/tests/test_domain/test_prefix.py::TestPrefixCreate::test_method  # 단일 테스트

# 린트 & 포맷
uv run ruff check .        # 린트
make lint                  # 린트 (프론트엔드 포함)
uv run ruff format .       # 포맷
make format                # 위와 동일

# Docker 개발 환경
make dev-up                # 개발 컨테이너 시작
make dev-down              # 개발 컨테이너 중지
make dev-logs              # 개발 컨테이너 로그 확인
make dev-build             # 개발 이미지 빌드

# 프론트엔드
cd frontend && pnpm install && pnpm dev   # 개발 서버
cd frontend && pnpm lint                  # 프론트엔드 린트
```

## 아키텍처 개요

**uv 모노레포 워크스페이스**: `services/*` 와 `shared` 패키지로 구성.

각 서비스는 **DDD + CQRS + Event Sourcing** 패턴을 따름:

```
services/<name>/src/<name>/
  domain/          # Aggregate, Entity, Value Object, Domain Event, Repository 인터페이스
  application/     # Command, Query, Handler, DTO
  infrastructure/  # DB 모델, Repository 구현체, 설정
  interface/       # FastAPI 라우터, 스키마, 메인 앱
```

**공유 라이브러리** (`shared/src/shared/`) 제공 모듈:
- `domain/` — 기반 클래스: Entity, ValueObject, AggregateRoot, Repository, DomainService, CustomField, Tag
- `cqrs/` — Command/Query 버스, Command/Query 기반 클래스
- `event/` — Event Store, DomainEvent, AggregateRoot(ES), Snapshot 지원
- `api/` — 페이지네이션, 필터링, 정렬, 에러 핸들링, OpenAPI 유틸, 미들웨어
- `messaging/` — Kafka Producer/Consumer, 직렬화
- `db/` — Tenant DB 매니저 (멀티테넌시)

**기술 스택**: Python 3.13, FastAPI, PostgreSQL, Kafka, Redis, Next.js (프론트엔드)

## 설계 & 구현 가이드라인

### DDD 패턴
- **Entity**: ID 기반 도메인 객체, 생명주기를 가짐
- **Value Object**: 불변, 값에 의한 동등성
- **Aggregate**: 일관성 경계, AggregateRoot를 통해서만 접근, Repository로만 조회
- **Repository**: 도메인 레이어에 인터페이스, 인프라 레이어에 구현체
- **Domain Event**: 도메인에서 발생한 사건의 기록
- **Domain Service**: 단일 Aggregate에 속하지 않는 로직

### CQRS + Event Sourcing 흐름
```
Command → CommandHandler → Aggregate (apply()로 상태 변경) → DomainEvent
  → Event Store (추가) + Kafka (발행)

Query → QueryHandler → Read Model (비정규화된 프로젝션)
```

### 멀티테넌시
- `shared.db.tenant_db_manager`를 통한 테넌트 수준 데이터베이스 격리
- 각 테넌트는 별도 스키마 또는 데이터베이스를 가짐

### 서비스 간 통신
- 서비스 간 통신은 **오직** Kafka 비동기 이벤트만 사용
- 동기 서비스 간 호출 금지

### 클린 아키텍처 레이어
- **Domain**은 아무것도 의존하지 않음
- **Application**은 Domain에 의존
- **Infrastructure**는 Domain + Application에 의존
- **Interface**는 Application에 의존 (Domain 내부에 직접 의존하지 않음)

## 코드 스타일

- **Ruff** 설정: `line-length = 120`, `target-version = "py313"`, `quote-style = "double"`
- 린트 규칙: E, F, I, N (N802 제외), W, UP, B, A, SIM
- **Pre-commit 훅** 설정됨: `ruff --fix` + `ruff format`
- 커밋 전 `uv run ruff check . && uv run ruff format .` 실행

## 프로젝트 관리

- **GitHub 저장소**: `fray-cloud/cmdb`
- **이슈 트래킹**: GitHub Issues, 마일스톤 `P1` (Phase 1)
- **PRD**: Issue #1
- **워크플로우**: 섹션별 커밋 → push → 이슈 태스크 체크박스 체크

## 사용 가능한 스킬

| 스킬 | 트리거 | 용도 |
|------|--------|------|
| `/grill-me` | "grill me", 설계 스트레스 테스트 | 공유된 이해에 도달할 때까지 계획에 대해 집요하게 질문 |
| `/design-an-interface` | API 설계, 인터페이스 탐색 | 다양한 인터페이스 설계안을 병렬로 생성 |
| `/prd-to-plan` | PRD 분해, 단계 계획 | PRD를 tracer-bullet 구현 계획으로 변환 |
| `/prd-to-issues` | PRD를 이슈로 변환 | PRD를 GitHub 이슈로 분해 |
| `/triage-issue` | 버그 보고, 이슈 조사 | 코드베이스 탐색 + TDD 수정 계획으로 버그 분류 |
| `/ubiquitous-language` | 도메인 용어 정의, 용어집 | 대화에서 DDD 유비쿼터스 언어 추출 |
| `/request-refactor-plan` | 리팩터링 계획, RFC | 작은 커밋 단위의 리팩터링 계획을 GitHub 이슈로 생성 |
| `/write-a-skill` | 새 스킬 생성 | 올바른 구조의 에이전트 스킬 생성 |
| `/tdd` | TDD, red-green-refactor | 테스트 주도 개발 루프 |
