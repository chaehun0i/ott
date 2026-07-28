# U03 Catalog and Discovery NFR Requirements Clarification Questions

Q5와 Q6의 답변 사이에 cache 존재 여부에 관한 충돌이 발견되었습니다.

## Contradiction 1: Application Cache와 무효화·TTL 정책

Q5에서 C를 선택하여 별도 application cache를 사용하지 않기로 했지만, Q6에서 A를 선택하여 CatalogVersion event 기반 cache 무효화와 feed 5분·detail 15분 TTL을 적용하기로 했습니다. Cache가 없다면 무효화와 TTL의 적용 대상도 존재하지 않습니다.

## Question 1
초기 U03 cache 정책을 최종적으로 어떻게 확정합니까?

A) Q5를 A로 변경한다. Process-local bounded cache를 사용하고 Q6의 event 무효화, feed 5분·detail 15분 TTL을 적용한다.

B) Q5의 C를 유지한다. Application cache를 사용하지 않고 Q6은 N/A로 변경하며 PostgreSQL query와 projection만 사용한다.

C) Application cache는 사용하지 않되 reverse proxy HTTP cache에 Q6의 TTL과 CatalogVersion purge를 적용한다.

X) Other (please describe after [Answer]: tag below)

[Answer]: B
