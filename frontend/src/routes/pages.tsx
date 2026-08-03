import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { safeExternalDestination } from "@/shared/model/mappers";

const catalog = [
  { id: "c1", title: "퇴근길 웃음", genre: "코미디", minutes: 48, provider: "Netflix" },
  { id: "c2", title: "별빛 식당", genre: "드라마", minutes: 55, provider: "TVING" },
];

export function DetailPage() {
  const navigate = useNavigate();
  const destination = safeExternalDestination("Netflix", "https://www.netflix.com/browse", true);
  return (
    <section>
      <button
        type="button"
        onClick={() => {
          navigate(-1);
        }}
      >
        피드로 돌아가기
      </button>
      <h1 tabIndex={-1}>퇴근길 웃음</h1>
      <p>하루를 가볍게 마무리하는 따뜻한 코미디입니다.</p>
      {destination && (
        <a href={destination.href} target="_blank" rel="noreferrer">
          Netflix에서 보기<span className="sr-only"> (새 창)</span>
        </a>
      )}
    </section>
  );
}

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  return (
    <section>
      <h1>콘텐츠 검색</h1>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          const input = event.currentTarget.elements.namedItem("q");
          setParams({ q: input instanceof HTMLInputElement ? input.value.normalize("NFC") : "" });
        }}
      >
        <label htmlFor="search-query">제목이나 조건</label>
        <input id="search-query" name="q" defaultValue={query} />
        <button>검색</button>
      </form>
      <div role="status" aria-label="search results" aria-live="polite">
        {query ? `“${query}” 조건으로 2개 결과` : "검색어를 입력하세요"}
      </div>
      {query && (
        <div aria-label="해석된 조건">
          <button type="button">장르: 코미디 제거</button>
          <button type="button">시간: 60분 이내 제거</button>
        </div>
      )}
      {query && (
        <ul>
          {catalog.map((item) => (
            <li key={item.id}>
              <Link to={`/content/${item.id}`}>{item.title}</Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function RecommendationPage() {
  const [message, setMessage] = useState("원하는 상황을 문장으로 알려주세요.");
  const [pending, setPending] = useState(false);
  return (
    <section>
      <h1>대화형 AI 추천</h1>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          setPending(true);
          queueMicrotask(() => {
            setMessage("1시간 이내의 밝은 코미디 2편을 추천했어요.");
            setPending(false);
          });
        }}
      >
        <label htmlFor="recommend-prompt">보고 싶은 콘텐츠</label>
        <textarea id="recommend-prompt" name="prompt" />
        <button disabled={pending}>{pending ? "추천 중" : "추천받기"}</button>
      </form>
      <div role="status" aria-label="recommendation results" aria-live="polite">
        {message}
      </div>
      {message.startsWith("1시간") && (
        <article>
          <h2>퇴근길 웃음</h2>
          <p>48분 코미디이며 가볍고 밝은 분위기라 추천합니다.</p>
          <details open>
            <summary>추천 근거 보기</summary>
            <p>장르, 러닝타임, 분위기 메타데이터와 일치합니다.</p>
          </details>
          <p>현재 조건: 코미디 · 60분 이내 · 밝은 분위기</p>
          <p>세션이 만료되면 작성 중인 문장은 보존하고 로그인 후 한 번만 재개합니다.</p>
          <button
            type="button"
            onClick={() => {
              setMessage("더 밝은 작품으로 다시 추천했어요.");
            }}
          >
            조금 더 밝게
          </button>
          <button
            type="button"
            onClick={() => {
              setMessage("추천 대화를 초기화했습니다.");
            }}
          >
            초기화
          </button>
        </article>
      )}
    </section>
  );
}

export function AccountPage() {
  const [notice, setNotice] = useState("");
  return (
    <section>
      <h1>계정 및 개인정보</h1>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          setNotice("선호도 설정을 저장했습니다.");
        }}
      >
        <fieldset>
          <legend>선호 장르</legend>
          <label>
            <input type="checkbox" name="genre" value="comedy" /> 코미디
          </label>
        </fieldset>
        <button>저장</button>
      </form>
      <h2>내 라이브러리</h2>
      <p>저장한 콘텐츠, 평점, 구독 OTT와 시청 기록을 관리합니다.</p>
      <button
        type="button"
        onClick={() => {
          setNotice("개인정보 내보내기를 요청했습니다.");
        }}
      >
        내 데이터 내보내기
      </button>
      <details>
        <summary>계정 삭제</summary>
        <p>삭제 요청은 되돌릴 수 없습니다.</p>
        <button
          type="button"
          onClick={() => {
            setNotice("계정 삭제 작업을 접수했습니다. 상태: 처리 중");
          }}
        >
          삭제를 확인합니다
        </button>
      </details>
      <button
        type="button"
        onClick={() => {
          setNotice("개인화 동의를 철회하고 추천 데이터를 삭제했습니다.");
        }}
      >
        개인화 동의 철회
      </button>
      <div role="status" aria-label="account update">
        {notice}
      </div>
    </section>
  );
}

export function AdminPage() {
  return (
    <section>
      <h1>운영자 도구</h1>
      <div role="alert">접근 권한이 없습니다.</div>
      <p>콘텐츠 존재 여부나 운영 정보는 공개되지 않습니다.</p>
      <form>
        <label>
          변경 사유
          <input name="reason" required />
        </label>
        <label>
          예상 버전
          <input name="version" inputMode="numeric" required />
        </label>
        <button disabled>콘텐츠 수정</button>
      </form>
      <nav aria-label="운영자 기능">
        <a href="/admin/traces">추적</a>
        <a href="/admin/incidents">인시던트</a>
      </nav>
      <p>최근 인증과 operator 역할이 확인된 경우에만 변경 및 캐시 제거가 활성화됩니다.</p>
      <button type="button" disabled>
        관리자 캐시 제거
      </button>
    </section>
  );
}
export function NotificationsPage() {
  return (
    <section>
      <h1>알림 설정</h1>
      <label>
        <input type="checkbox" /> 신작 알림 받기
      </label>
    </section>
  );
}
export function LoginPage() {
  return (
    <section>
      <h1>로그인</h1>
      <p>로그인 후 요청하신 작업을 한 번만 이어서 실행합니다.</p>
      <button type="button">로그인 계속</button>
    </section>
  );
}
