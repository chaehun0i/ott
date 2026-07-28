# Known Limitations

- 현재 완성 범위는 U07 Platform and Delivery입니다. 실제 OTT 공급자 수집, 통합 피드, 개인화 추천, AI 요약·추천 이유, 대화형 조정 UI는 U01~U06 구현 후 제공됩니다.
- 이 호스트의 Docker daemon 오류로 이미지 build와 컨테이너 기동은 실행하지 않았습니다. PostgreSQL 통합 테스트는 Docker 대신 로컬 PostgreSQL 17.10에서 skip 없이 통과했습니다. CI에서도 `TEST_DATABASE_URL` 기반 별도 필수 gate를 유지합니다.
- 로컬 검증은 Python 3.12.13에서 수행했습니다. Dockerfile base image의 registry digest는 remote 배포 시 조직이 승인한 digest로 교체해야 합니다.
- worker는 후속 비즈니스 단위가 handler를 등록할 composition slot을 제공합니다. U07 단독 상태에서는 처리할 business job type이 없습니다.
- 분기 복원 workflow는 실제 격리 인프라와 승인된 archive secret이 제공되기 전까지 증적·입력 gate 역할만 합니다.
