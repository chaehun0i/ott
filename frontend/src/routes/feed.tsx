import { Link, useSearchParams } from "react-router-dom";
import { prefetchRoute } from "./prefetch";

interface FeedItem {
  id: string;
  title: string;
  genre: string;
  minutes: number;
  provider: string;
}
const feedItems: readonly FeedItem[] = [
  { id: "c1", title: "퇴근길 웃음", genre: "코미디", minutes: 48, provider: "Netflix" },
  { id: "c2", title: "별빛 식당", genre: "드라마", minutes: 55, provider: "TVING" },
];

export function FeedPage() {
  const [params, setParams] = useSearchParams();
  const genre = params.get("genre") ?? "all";
  const sort = params.get("sort") ?? "latest";
  const page = Math.max(1, Number(params.get("page") ?? 1));
  const freshness = params.get("state") ?? "fresh";
  const update = (next: Record<string, string>) => {
    const merged = new URLSearchParams(params);
    Object.entries(next).forEach(([key, value]) => {
      if (value) merged.set(key, value);
      else merged.delete(key);
    });
    setParams(merged);
  };
  const items = feedItems
    .filter((item) => genre === "all" || item.genre === genre)
    .slice()
    .sort((a, b) => (sort === "short" ? a.minutes - b.minutes : a.id.localeCompare(b.id)));
  return (
    <section>
      <h1>OTT 최신 콘텐츠 통합 피드</h1>
      <p role="status">
        {freshness === "stale"
          ? "마지막 정상 데이터입니다. 새로 고치는 중입니다."
          : freshness === "degraded"
            ? "일부 OTT 정보를 불러오지 못했습니다."
            : "방금 업데이트됨"}
      </p>
      <fieldset>
        <legend>피드 조건</legend>
        <label>
          장르{" "}
          <select
            value={genre}
            onChange={(event) => {
              update({ genre: event.target.value === "all" ? "" : event.target.value, page: "1" });
            }}
          >
            <option value="all">전체</option>
            <option value="코미디">코미디</option>
          </select>
        </label>
        <label>
          정렬{" "}
          <select
            value={sort}
            onChange={(event) => {
              update({ sort: event.target.value });
            }}
          >
            <option value="latest">최신순</option>
            <option value="short">짧은 순</option>
          </select>
        </label>
      </fieldset>
      <ul className="card-grid">
        {items.map((item) => (
          <li key={item.id}>
            <article>
              <picture>
                <source srcSet="/poster.svg" type="image/svg+xml" />
                <img
                  className="poster"
                  src="/poster.svg"
                  alt={`${item.title} 포스터`}
                  loading="lazy"
                  width="400"
                  height="600"
                />
              </picture>
              <h2>
                <Link
                  to={`/content/${item.id}`}
                  onPointerEnter={() => {
                    prefetchRoute(`/content/${item.id}`);
                  }}
                >
                  {item.title}
                </Link>
              </h2>
              <p>
                {item.provider} · {item.genre} · {item.minutes}분
              </p>
            </article>
          </li>
        ))}
      </ul>
      <nav aria-label="페이지">
        <button
          type="button"
          disabled={page === 1}
          onClick={() => {
            update({ page: String(page - 1) });
          }}
        >
          이전
        </button>
        <span>{page} 페이지</span>
        <button
          type="button"
          onClick={() => {
            update({ page: String(page + 1) });
          }}
        >
          다음
        </button>
      </nav>
    </section>
  );
}

export function NotFoundPage() {
  return (
    <section>
      <h1>페이지를 찾을 수 없습니다</h1>
      <Link to="/feed">피드로 이동</Link>
    </section>
  );
}
