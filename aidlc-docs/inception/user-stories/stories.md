# OTT 통합 피드 및 AI 추천 서비스 User Stories

## Story Structure

> **Prototype completion note (2026-08-04)**: U01-related acceptance checkboxes represent completion within the approved prototype and automated verification scope. Native NVDA/VoiceOver execution and production legal/expert review are Future Manual QA/production-readiness activities and are not claimed as performed.

- **Breakdown**: Epic-Based Hybrid
- **Hierarchy**: Epic → Small Story
- **Narrative**: `As a / I want / So that`
- **Acceptance Criteria**: 사용자 흐름은 Given / When / Then, 데이터·품질 제약은 체크리스트
- **Scope**: 초기 단일 서버 프로토타입 중심, 상용 전환 조건 별도 표시

## Epic E-01: 통합 콘텐츠 발견

### US-001: 최신 콘텐츠 통합 피드 탐색

**As a** 빠른 탐색 방문자, **I want** 여러 글로벌 OTT의 신작·인기·공개 예정·종료 예정 콘텐츠를 한 화면에서 보고 싶다, **so that** OTT 앱을 각각 열지 않고 볼 작품을 발견할 수 있다.

**Requirements**: FR-001, FR-002, AC-001

**Acceptance Criteria**:

- **Given** 승인된 콘텐츠가 여러 OTT에 존재하고 **when** 사용자가 피드를 열면 **then** 상태별 콘텐츠가 하나의 반응형 피드에 표시된다.
- **Given** 피드가 표시될 때 **then** 각 항목은 제공 OTT와 콘텐츠 상태를 식별할 수 있다.
- [x] 승인되지 않거나 격리된 콘텐츠는 피드에 포함되지 않는다.
- [x] 키보드만으로 피드 항목을 탐색할 수 있다.

### US-002: 피드 필터링과 작품 상세 확인

**As a** 빠른 탐색 방문자, **I want** 장르·연도·OTT·국가·공개 상태로 필터링하고 작품 상세를 보고 싶다, **so that** 내 조건에 맞는 작품과 시청 위치를 확인할 수 있다.

**Requirements**: FR-003, FR-004, FR-005

**Acceptance Criteria**:

- **Given** 사용 가능한 필터가 있고 **when** 사용자가 복수 필터를 적용하면 **then** 모든 선택 조건을 충족하는 작품만 표시된다.
- **Given** 사용자가 작품을 선택하면 **then** 제목, 줄거리, 장르, 상영 시간, 인물, 제공 OTT, 지역, 갱신 시각을 확인할 수 있다.
- **Given** 합법적인 OTT 이동 링크가 있으면 **when** 사용자가 선택할 때 **then** 해당 제공처로 이동한다.
- [x] 지역 또는 OTT 가용성이 확인되지 않은 링크는 활성화하지 않는다.

### US-003: 데이터 최신성과 상태 확인

**As a** 빠른 탐색 방문자, **I want** 콘텐츠 출처와 마지막 갱신 상태를 확인하고 싶다, **so that** 오래되거나 불완전한 정보를 판단할 수 있다.

**Requirements**: FR-006, DR-006, AC-008

**Acceptance Criteria**:

- **Given** 콘텐츠가 표시될 때 **then** 출처와 마지막 성공 갱신 시각을 확인할 수 있다.
- **Given** 공급자 갱신이 목표 주기를 초과하면 **when** 사용자가 콘텐츠를 보면 **then** 오래된 데이터 상태가 명시된다.
- [x] 수집 실패가 기존의 마지막 정상 데이터를 삭제하지 않는다.

## Epic E-02: 검색과 다국어 탐색

### US-004: 제목·인물 및 필터 검색

**As a** 빠른 탐색 방문자, **I want** 제목과 인물로 검색하고 결과를 필터링하고 싶다, **so that** 기억하는 단서만으로 작품을 찾을 수 있다.

**Requirements**: FR-007, FR-003

**Acceptance Criteria**:

- **Given** 사용자가 제목 또는 인물을 입력하고 **when** 검색하면 **then** 일치하는 승인 콘텐츠가 관련도 순으로 표시된다.
- **Given** 검색 결과가 있을 때 **when** 필터를 적용하면 **then** 검색어와 필터를 모두 충족하는 결과만 남는다.
- [x] 격리 콘텐츠는 검색 색인과 결과에 포함되지 않는다.

### US-005: 한국어 자연어·의미 검색

**As a** 한국어 사용자, **I want** 한국어 문장으로 콘텐츠를 검색하고 싶다, **so that** 정확한 제목을 몰라도 원하는 분위기와 조건의 작품을 찾을 수 있다.

**Requirements**: FR-008, FR-009, FR-035

**Acceptance Criteria**:

- **Given** 한국어 자연어 질의가 입력되고 **when** 검색하면 **then** 시스템은 장르·분위기·시간·동반자·OTT 조건을 구조화하여 결과에 적용한다.
- **Given** 번역 제목과 원제가 존재할 때 **then** 두 표현 모두 검색할 수 있다.
- [x] 구조화된 조건은 사용자에게 확인 가능한 형태로 표시된다.

### US-006: 영어 자연어·의미 검색

**As a** 영어 사용자, **I want** 영어 문장과 원제로 콘텐츠를 검색하고 싶다, **so that** 영어 사용 환경에서도 동일한 탐색 가치를 얻을 수 있다.

**Requirements**: FR-008, FR-009, FR-035

**Acceptance Criteria**:

- **Given** 영어 자연어 질의가 입력되고 **when** 검색하면 **then** 조건이 구조화되어 승인 콘텐츠에 적용된다.
- **Given** 한국어 번역만 있는 필드가 있을 때 **then** 정의된 언어 대체 규칙이 적용된다.
- [x] 한국어와 영어 질의의 구조화 결과는 동일 스키마를 사용한다.

### US-007: 다국어·접근 가능한 공통 UI

**As a** 방문자, **I want** 한국어와 영어로 접근 가능한 UI를 사용하고 싶다, **so that** 언어 또는 보조기술 사용 여부와 관계없이 콘텐츠를 탐색할 수 있다.

**Requirements**: FR-033, FR-034, NFR 7.4

**Acceptance Criteria**:

- **Given** 사용자가 언어를 변경하면 **then** 공통 UI, 상태, 오류, 동의 문구가 선택 언어로 표시된다.
- **Given** 번역 메타데이터가 없으면 **then** 원제 또는 정의된 대체 언어가 표시되고 누락 상태를 숨기지 않는다.
- [x] 모든 핵심 기능은 키보드로 사용할 수 있다.
- [x] 이미지 대체 텍스트, 포커스 표시, 색 대비, 스크린 리더 레이블을 제공한다.

## Epic E-03: 자연어 및 대화형 AI 추천

### US-008: 한국어 상황 기반 추천 요청

**As a** 가벼운 탐색 회원, **I want** `퇴근 후 가볍게 볼 1시간 이내 코미디`처럼 한국어로 상황을 설명하고 싶다, **so that** 복잡한 필터를 직접 조작하지 않고 적합한 작품을 추천받을 수 있다.

**Requirements**: FR-009, FR-010, FR-036, AC-002

**Acceptance Criteria**:

- **Given** 한국어 추천 문장이 입력되고 **when** AI 계층이 해석하면 **then** 기분·장르·시간·동반자·OTT·제외 조건이 구조화된다.
- **Given** 구조화가 완료되면 **then** Recommendation Engine만 후보 적격성과 최종 순위를 결정한다.
- [x] AI 계층은 하드 조건을 임의로 제거하거나 최종 순위를 확정하지 않는다.

### US-009: 영어 상황 기반 추천 요청

**As a** 영어 사용자, **I want** 영어로 시청 상황과 조건을 설명하고 싶다, **so that** 한국어 사용자와 동등한 추천 기능을 사용할 수 있다.

**Requirements**: FR-009, FR-035, FR-036

**Acceptance Criteria**:

- **Given** 영어 추천 문장이 입력되면 **when** AI 계층이 해석할 때 **then** 한국어와 동일한 추천 의도 스키마를 생성한다.
- **Given** 같은 의미의 한국어·영어 질의가 있으면 **then** 하드 조건의 의미가 언어에 따라 달라지지 않는다.
- [x] 언어별 평가 세트로 의도 추출 회귀를 검증한다.

### US-010: 하드 조건을 지키는 개인화 순위

**As a** 적극적 추천 사용자, **I want** 이용 가능한 OTT·지역·상영 시간 같은 필수 조건을 지키면서 내 취향에 맞는 순위를 받고 싶다, **so that** 실제로 볼 수 있는 추천만 검토할 수 있다.

**Requirements**: FR-011, FR-013, FR-017, FR-037, AC-011, AC-012

**Acceptance Criteria**:

- **Given** 구조화된 추천 조건과 승인 카탈로그가 있고 **when** Recommendation Engine이 추천하면 **then** 하드 조건 충족 후보만 개인화·다양성 점수로 정렬된다.
- **Given** AI 출력에 부적격 후보가 포함되어도 **when** 최종 검증이 실행되면 **then** 해당 후보는 노출되지 않는다.
- [x] 최종 콘텐츠 ID는 모두 승인 카탈로그에 존재한다.
- [x] 동일 입력과 동일 버전의 정책에서는 정의된 허용 범위 안에서 재현 가능한 결과를 제공한다.
- **PBT Candidate**: 승인 카탈로그 소속, 하드 조건 충족, 점수 범위, 중복 제한 불변 조건

### US-011: 메타데이터 근거 기반 추천 이유와 요약

**As a** 추천 사용자, **I want** 작품 요약과 내 조건에 연결된 짧은 추천 이유를 보고 싶다, **so that** 추천을 선택할 근거를 빠르게 이해할 수 있다.

**Requirements**: FR-014, FR-015, FR-016, FR-038, FR-040, AC-003, AC-013

**Acceptance Criteria**:

- **Given** 검증된 추천 후보와 허용된 메타데이터가 있고 **when** AI 계층이 문구를 생성하면 **then** 각 핵심 주장은 콘텐츠 ID와 근거 필드에 연결된다.
- **Given** 근거가 부족하거나 검증이 실패하면 **when** 응답을 조립할 때 **then** 해당 문구는 차단되거나 승인된 템플릿으로 대체된다.
- [x] 스포일러를 최소화하고 AI 생성 문구임을 식별할 수 있다.
- [x] AI가 생성한 새 작품·제공처·줄거리 사실을 카탈로그에 추가하지 않는다.
- **PBT Candidate**: 모든 근거 참조가 동일 콘텐츠의 승인 메타데이터를 가리키는 불변 조건

### US-012: 대화형 추천 조정과 초기화

**As a** 적극적 추천 사용자, **I want** `조금 더 밝은 작품` 또는 `다른 장르`처럼 후속 요청으로 추천을 조정하고 싶다, **so that** 처음부터 다시 입력하지 않고 결과를 개선할 수 있다.

**Requirements**: FR-019, FR-020, FR-021, AC-004

**Acceptance Criteria**:

- **Given** 기존 추천 세션이 있고 **when** 사용자가 일부 조건을 변경하면 **then** 유지·추가·제거된 조건이 구분되어 새 추천에 적용된다.
- **Given** 사용자가 초기화를 선택하면 **then** 이전 세션 조건은 새 추천에 영향을 주지 않는다.
- [x] 후속 요청도 US-010과 US-011의 적격성·근거 검증을 동일하게 통과한다.
- **PBT Candidate**: 변경하지 않은 조건 보존, 초기화 후 이전 상태 비영향 불변 조건

### US-013: 모호하거나 충돌하는 추천 조건 조정

**As a** 추천 사용자, **I want** 모호하거나 서로 충돌하는 조건을 확인하고 조정하고 싶다, **so that** 시스템이 임의로 중요한 조건을 버리지 않게 할 수 있다.

**Requirements**: FR-010

**Acceptance Criteria**:

- **Given** `30분 이내 장편 영화`처럼 충돌하는 조건이 있고 **when** 해석되면 **then** 충돌 항목이 표시된다.
- **Given** 해석 신뢰도가 기준보다 낮으면 **then** 사용자는 추천 전에 구조화 조건을 수정할 수 있다.
- [x] 사용자 확인 전에는 모호한 값을 하드 조건으로 확정하지 않는다.

## Epic E-04: 계정과 개인화

### US-014: 이메일·소셜 로그인과 계정 접근

**As a** 가벼운 탐색 회원, **I want** 이메일 또는 지원되는 소셜 계정으로 로그인하고 싶다, **so that** 기기와 세션을 넘어 내 설정과 활동을 사용할 수 있다.

**Requirements**: FR-023, NFR 7.3

**Acceptance Criteria**:

- **Given** 유효한 인증 수단이 있고 **when** 로그인하면 **then** 회원 기능에 접근할 수 있다.
- **Given** 인증이 만료되거나 폐기되면 **then** 보호된 기능은 재인증을 요구한다.
- [x] 서버가 회원과 운영자 권한을 구분해 검증한다.
- [x] 자격 증명과 비밀정보는 안전한 저장·주입 정책을 따른다.

### US-015: 선호 장르와 구독 OTT 설정

**As a** 가벼운 탐색 회원, **I want** 선호 장르와 구독 OTT를 설정하고 싶다, **so that** 첫 사용부터 관련성 높은 추천을 받을 수 있다.

**Requirements**: FR-011, FR-024

**Acceptance Criteria**:

- **Given** 회원이 선호와 구독 OTT를 저장하면 **then** 다음 추천과 개인화 피드에 반영된다.
- **Given** 선호를 변경하면 **then** 이후 추천은 새 설정을 사용하고 이전 설정을 하드 조건으로 유지하지 않는다.
- [x] 콜드 스타트에서는 명시적 선호와 인기·신작 신호를 결합한다.

### US-016: 찜·평가·시청 이력 관리

**As a** 회원, **I want** 작품을 저장하고 평가하며 시청 이력을 관리하고 싶다, **so that** 시청 후보를 보관하고 추천 품질을 개선할 수 있다.

**Requirements**: FR-024

**Acceptance Criteria**:

- **Given** 회원이 작품을 저장·평가·시청 처리하면 **then** 각 상태가 계정에 반영된다.
- **Given** 회원이 기록을 수정하거나 삭제하면 **then** 개인화 입력도 최신 상태를 사용한다.
- [x] 동일 작품의 반복 저장은 중복 레코드를 만들지 않는다.
- **PBT Candidate**: 저장 멱등성, 평가 범위, 상태 전이 일관성

### US-017: 행동 피드백 기반 추천 피드 개선

**As a** 회원, **I want** 클릭·저장·다시 추천·추천 무시·OTT 이동 반응이 이후 추천에 반영되길 원한다, **so that** 사용할수록 내 취향에 맞는 피드를 받을 수 있다.

**Requirements**: FR-012, FR-025, DR-007, AC-005

**Acceptance Criteria**:

- **Given** 사용자가 개인화에 동의했고 **when** 관련 행동을 수행하면 **then** 정규화된 이벤트가 이후 추천 특성에 반영된다.
- **Given** 동의를 철회하면 **then** 새로운 행동은 개인화 학습에 사용되지 않는다.
- [x] 이벤트에는 불필요한 직접 식별정보를 포함하지 않는다.
- [x] 추천 버전과 피드 순서 변화가 평가 가능한 지표로 기록된다.

### US-018: 개인화 데이터 동의·조회·내보내기·삭제

**As a** 회원, **I want** 개인화 데이터 사용을 통제하고 내 데이터를 조회·내보내기·삭제하고 싶다, **so that** 서비스 사용 중에도 개인정보 통제권을 유지할 수 있다.

**Requirements**: FR-022, FR-026, FR-027, AC-007, NFR 7.4

**Acceptance Criteria**:

- **Given** 회원이 설정을 열면 **then** 수집 목적, 보존 기간, AI·외부 공급자 전송 범위와 현재 동의 상태를 확인할 수 있다.
- **Given** 내보내기 또는 삭제를 요청하면 **then** 인증과 권한 검증 후 처리 상태를 확인할 수 있다.
- [x] 비회원 행동은 명시적 동의 없이 회원 프로필에 결합되지 않는다.
- [x] 삭제·철회 결과가 추천과 AI 입력에 반영된다.

### US-019: 관심 콘텐츠 알림 관리

**As a** 회원, **I want** 관심 작품의 공개·예정 알림을 설정하고 채널을 관리하고 싶다, **so that** 보고 싶은 콘텐츠를 놓치지 않을 수 있다.

**Requirements**: FR-028, FR-029

**Acceptance Criteria**:

- **Given** 회원이 관심 작품 알림을 켜고 **when** 검증된 공개 이벤트가 발생하면 **then** 선택한 채널로 알림을 받는다.
- **Given** 알림 유형이나 채널을 끄면 **then** 이후 해당 알림은 전송되지 않는다.
- [x] 오래되거나 격리된 메타데이터는 알림을 발생시키지 않는다.

## Epic E-05: 콘텐츠 운영과 Metadata 검증

### US-020: 메타데이터 수집·정규화·검증·격리

**As a** 콘텐츠 운영자, **I want** 공급자 데이터를 상태별 Pipeline으로 검증하고 실패 레코드를 격리하고 싶다, **so that** 신뢰할 수 있는 데이터만 피드와 추천에 사용되게 할 수 있다.

**Requirements**: DR-001~DR-006, DR-009~DR-012, FR-039, FR-041, AC-014

**Acceptance Criteria**:

- **Given** 공급자 데이터가 수집되면 **when** Pipeline이 실행될 때 **then** 원본·정규화·승인·격리 상태가 추적된다.
- **Given** 스키마, 출처, 라이선스, 최신성, 식별자, 지역·OTT 검증 중 하나가 실패하면 **then** 레코드는 원인 코드와 함께 격리된다.
- [ ] 격리 레코드는 피드·검색·추천 색인에 진입하지 않는다.
- [ ] 재처리는 공급자 요청 제한과 제한된 재시도 정책을 따른다.
- **PBT Candidate**: 정규화 멱등성, 중복 병합 요소 보존, 격리 비유출 불변 조건

### US-021: 작품 정보와 노출 상태 운영

**As a** 콘텐츠 운영자, **I want** 작품 정보와 노출 여부를 수정하고 변경 이력을 확인하고 싶다, **so that** 자동 수집 오류를 교정하면서 책임 있는 운영을 할 수 있다.

**Requirements**: FR-030, FR-031, FR-032

**Acceptance Criteria**:

- **Given** 운영자 권한이 있고 **when** 작품 정보나 노출 상태를 수정하면 **then** 변경 전후 값, 변경자, 시각이 기록된다.
- **Given** 자동 수집 값과 운영자 수정 값이 충돌하면 **then** 정의된 우선순위가 적용되고 운영자에게 상태가 표시된다.
- [x] 일반 회원은 운영 기능을 호출할 수 없다.

### US-022: 추천 결과 Metadata 검증과 안전한 대체

**As a** 적극적 추천 사용자, **I want** 검증된 작품과 근거만 추천 결과에 나타나길 원한다, **so that** 존재하지 않거나 조건에 맞지 않는 추천을 신뢰 문제 없이 피할 수 있다.

**Requirements**: FR-038~FR-041, DR-013, DR-014, AC-011~AC-014

**Acceptance Criteria**:

- **Given** AI와 Recommendation Engine 결과가 준비되고 **when** Metadata Validation Pipeline이 실행되면 **then** 콘텐츠 ID, 승인 상태, 지역·OTT 가용성, 하드 조건, 근거 참조가 검증된다.
- **Given** 항목 검증이 실패하면 **then** 해당 항목이나 문구는 노출되지 않고 검증된 템플릿 또는 규칙 기반 결과로 대체된다.
- [ ] 검증 실패가 전체 추천 응답 실패로 불필요하게 확대되지 않는다.
- [ ] 검증되지 않은 생성 문구를 그대로 노출하는 우회 경로가 없다.
- **PBT Candidate**: 승인 카탈로그 폐쇄성, 하드 조건 보존, 근거 참조 유효성, 격리 비유출

### US-023: 추천 결정과 검증 추적

**As a** 콘텐츠 운영자, **I want** 추천과 검증 Pipeline의 버전과 결과를 추적하고 싶다, **so that** 잘못된 추천을 재현하고 원인을 조사할 수 있다.

**Requirements**: FR-042, DR-008, DR-014

**Acceptance Criteria**:

- **Given** 추천 요청이 완료되면 **then** 의도 해석, 후보 집합, 필터, 점수·순위 정책, 메타데이터, 검증 규칙 버전과 대체 경로 여부가 연결된다.
- **Given** 운영자가 허용된 추적 ID로 조회하면 **then** 실패 단계와 원인 코드를 확인할 수 있다.
- [x] 개인정보와 모델 내부 추론 내용은 추적 로그에 기록하지 않는다.
- [x] 추적 로그 접근은 운영자 권한으로 제한된다.

## Epic E-06: 품질, 복원력 및 운영 준비

### US-024: 외부 서비스 장애 시 저하 운용

**As a** 회원, **I want** 콘텐츠 공급자나 AI 서비스에 장애가 있어도 기본 피드와 추천을 계속 사용하고 싶다, **so that** 일시적 외부 장애 때문에 전체 서비스가 중단되지 않는다.

**Requirements**: FR-018, NFR 8.4, AC-006, RESILIENCY-10

**Acceptance Criteria**:

- **Given** 콘텐츠 공급자가 실패하면 **when** 피드를 열 때 **then** 마지막 정상 데이터와 오래된 상태가 표시된다.
- **Given** AI 서비스가 제한 시간 내 응답하지 않으면 **then** 규칙 기반 인기·신작·장르 추천으로 전환된다.
- [ ] 외부 호출에 제한 시간, 제한된 재시도, 지수 백오프를 적용한다.
- [ ] 장애 의존성이 전체 요청 자원을 고갈시키지 않도록 격리한다.

### US-025: 상태 점검·관측·장애 대응

**As a** 콘텐츠 운영자, **I want** 서비스 상태와 주요 품질 저하를 확인하고 경량 장애 절차를 실행하고 싶다, **so that** 문제를 빠르게 감지하고 복구할 수 있다.

**Requirements**: NFR 7.7, NFR 8.5, RESILIENCY-05, RESILIENCY-06, RESILIENCY-07, RESILIENCY-15

**Acceptance Criteria**:

- **Given** 서비스가 실행 중이면 **then** 얕은 상태 점검과 데이터베이스·외부 API·AI 의존성을 확인하는 깊은 상태 점검을 제공한다.
- **Given** 오류율, 지연, 백업 실패, 외부 API 한도, 데이터 최신성 저하가 기준을 넘으면 **then** 운영 알림이 생성된다.
- [x] 구조화 로그, 요청 상관관계 ID, 지연·오류·처리량 지표를 제공한다.
- [x] 장애 대응은 탐지, 영향 확인, 완화, 복구, 공지, 사후 분석을 포함한다.

### US-026: 백업·복원과 복구 검증

**As a** 콘텐츠 운영자, **I want** 사용자·개인화·운영 데이터를 백업하고 복원 검증을 수행하고 싶다, **so that** 단일 서버 장애 후 수 시간 이내에 서비스를 복구할 수 있다.

**Requirements**: NFR 8.2, NFR 8.5, RESILIENCY-02, RESILIENCY-11, RESILIENCY-12, RESILIENCY-13

**Acceptance Criteria**:

- **Given** 영속 데이터가 있고 **when** 백업 일정이 실행되면 **then** 암호화된 백업이 생성되고 30일 보존 정책이 적용된다.
- **Given** 복원 검증을 실행하면 **then** 데이터 무결성과 핵심 사용자 흐름을 확인한다.
- [ ] 백업 실패가 알림으로 연결된다.
- [ ] RTO/RPO 수 시간 목표와 단계별 복구·복귀 실행서를 제공한다.

### US-027: 안전한 계정·개인정보·접근성 운영

**As a** 회원, **I want** 내 계정과 개인정보가 안전하게 처리되고 핵심 기능에 접근할 수 있길 원한다, **so that** 개인화 서비스를 신뢰하고 사용할 수 있다.

**Requirements**: NFR 7.3, NFR 7.4, FR-026, AC-007

**Acceptance Criteria**:

- **Given** 개인정보가 저장·전송될 때 **then** 정의된 암호화와 최소 권한 정책이 적용된다.
- **Given** 사용자 입력과 인증 요청이 처리되면 **then** 서버 측 권한 검증, 입력 검증, 요청 제한과 감사 기록이 적용된다.
- [x] 비밀정보가 소스 코드나 컨테이너 이미지에 포함되지 않는다.
- [x] 핵심 회원 흐름은 키보드와 보조기술로 완료할 수 있다.
- [x] 상용 전환 전 개인정보·접근성 법무 및 전문가 검토가 완료되어야 한다.

### US-028: 재현 가능한 배포와 버전 롤백

**As a** 콘텐츠 운영자, **I want** 검증된 컨테이너 이미지를 직접 배포하고 실패 시 이전 버전으로 되돌리고 싶다, **so that** 프로토타입 변경 위험을 통제할 수 있다.

**Requirements**: NFR 7.6, NFR 8.3, AC-010, RESILIENCY-03, RESILIENCY-04

**Acceptance Criteria**:

- **Given** 변경이 저장소에 반영되면 **when** GitHub Actions가 실행될 때 **then** 빌드·테스트 후 버전이 고정된 이미지를 GHCR에 게시한다.
- **Given** 직접 배포가 실패하면 **when** 운영자가 롤백을 실행할 때 **then** 이전 이미지와 배포 설정으로 복구된다.
- [ ] Git 커밋, 릴리스 태그, 이미지 버전, 배포 결과를 변경 이력으로 연결한다.
- [ ] 데이터베이스 변경은 이전 애플리케이션과의 호환 또는 별도 복구 절차를 가진다.
- [ ] 상용 전환 전 Multi-AZ, 자동 확장, 배포 전략과 복원력 테스트 방식을 재평가한다.

## Persona-to-Story Map

| Persona | Stories |
|---|---|
| P-01 빠른 탐색 방문자 | US-001~US-007 |
| P-02 가벼운 탐색 회원 | US-008~US-019, US-024, US-027 |
| P-03 적극적 추천 사용자 | US-005, US-006, US-008~US-013, US-016~US-018, US-022~US-024, US-027 |
| P-04 콘텐츠 운영자 | US-020~US-028 |

## Requirements Traceability

| Requirement Set | Stories |
|---|---|
| FR-001~FR-006 | US-001~US-003 |
| FR-007~FR-010 | US-004~US-006, US-008, US-009, US-013 |
| FR-011~FR-018 | US-010, US-011, US-015, US-017, US-024 |
| FR-019~FR-022 | US-012, US-018 |
| FR-023~FR-027 | US-014~US-018, US-027 |
| FR-028~FR-029 | US-019 |
| FR-030~FR-032 | US-021 |
| FR-033~FR-035 | US-005~US-007, US-009 |
| FR-036~FR-042 | US-008~US-012, US-020, US-022, US-023 |
| DR-001~DR-006 | US-003, US-020 |
| DR-007~DR-008 | US-017, US-018, US-023 |
| DR-009~DR-014 | US-020, US-022, US-023 |
| AC-001~AC-004 | US-001, US-008, US-011, US-012 |
| AC-005~AC-010 | US-003, US-017, US-018, US-024, US-026, US-028 |
| AC-011~AC-014 | US-010, US-011, US-020, US-022 |
| Performance, freshness, AI quality | US-001~US-013, US-020, US-022, US-024 |
| Security, privacy, accessibility | US-007, US-014, US-018, US-021, US-023, US-027 |
| Resiliency and operations | US-024~US-028 |
| Property-Based Testing | US-009~US-012, US-016, US-020, US-022 |

## INVEST Verification

`Yes`는 현재 스토리가 Independent, Negotiable, Valuable, Estimable, Small, Testable 기준을 충족함을 뜻한다. 구현 중 하나의 스토리가 독립적으로 완료될 수 없을 만큼 커지면 해당 Epic 안에서 분리한다.

| Story | I | N | V | E | S | T |
|---|---|---|---|---|---|---|
| US-001 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-002 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-003 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-004 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-005 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-006 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-007 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-008 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-009 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-010 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-011 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-012 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-013 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-014 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-015 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-016 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-017 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-018 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-019 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-020 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-021 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-022 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-023 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-024 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-025 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-026 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-027 | Yes | Yes | Yes | Yes | Yes | Yes |
| US-028 | Yes | Yes | Yes | Yes | Yes | Yes |

## Extension Compliance

### Security Baseline

- **Status**: Disabled
- **Treatment**: 확장 규칙은 건너뛰었다. 인증, 권한, 암호화, 비밀정보, 개인정보, 접근성은 일반 요구사항에 따라 US-014, US-018, US-021, US-023, US-027에 포함했다.

### Resiliency Baseline

| Rules | Status | Story-stage rationale |
|---|---|---|
| RESILIENCY-01~02 | Compliant | 핵심 작업 부하 사용자 영향과 수 시간 복구 목표가 US-024~US-026에 반영되었다. |
| RESILIENCY-03~04 | Compliant | 변경 이력, CI/CD, 직접 배포와 버전 롤백이 US-028에 반영되었다. |
| RESILIENCY-05~07 | Compliant | 관측성, 상태 점검, 경보와 운영 대응이 US-025에 반영되었다. |
| RESILIENCY-08~09 | N/A | 사용자 승인에 따라 초기 단일 서버·저규모 프로토타입에서 제외하고 US-028의 상용 전환 조건으로 기록했다. |
| RESILIENCY-10 | Compliant | 외부 장애 격리와 저하 운용이 US-024에 반영되었다. |
| RESILIENCY-11~13 | Compliant | 백업·복원·실행서·검증이 US-026에 반영되었다. |
| RESILIENCY-14 | N/A | 상세 복원력 테스트 방식은 NFR Design에서 사용자 결정 후 적용한다. |
| RESILIENCY-15 | Compliant | 경량 장애 대응과 사후 분석이 US-025에 반영되었다. |

### Property-Based Testing

| Rules | Status | Story-stage rationale |
|---|---|---|
| PBT-01 | N/A | 공식 속성 식별은 Functional Design에서 수행하며 후보 속성을 관련 Story에 표시했다. |
| PBT-02~08 | N/A | 구현 전 단계이므로 테스트 생성은 적용되지 않는다. 왕복·불변·멱등·상태·격리 후보를 Story에 연결했다. |
| PBT-09 | N/A | 프레임워크 선택은 NFR Requirements에서 수행한다. |
| PBT-10 | N/A | 예제 기반·속성 기반 테스트 병행은 Code Generation과 Build and Test에서 검증한다. |

현재 User Stories 단계에서 적용 가능한 확장 규칙의 차단 Finding은 없다.
