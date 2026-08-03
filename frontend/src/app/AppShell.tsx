import { useEffect, useRef } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useLocale } from "./locale";
import { prefetchRoute } from "@/routes/prefetch";

export function AppShell() {
  const { locale, setLocale, text } = useLocale();
  const location = useLocation();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const previousPath = useRef(location.pathname);
  useEffect(() => {
    if (previousPath.current !== location.pathname) headingRef.current?.focus();
    previousPath.current = location.pathname;
  }, [location.pathname]);
  return (
    <>
      <a href="#main">본문으로 건너뛰기</a>
      <header>
        <p>{text("appName")}</p>
        <nav aria-label="주요">
          <NavLink to="/feed">{text("nav.feed")}</NavLink>
          <NavLink
            to="/search"
            onPointerEnter={() => {
              prefetchRoute("/search");
            }}
          >
            {text("nav.search")}
          </NavLink>
          <NavLink to="/recommend">{text("nav.recommend")}</NavLink>
          <NavLink to="/account">{text("nav.account")}</NavLink>
        </nav>
        <label>
          언어
          <select
            value={locale}
            onChange={(event) => {
              setLocale(event.target.value as "ko" | "en");
            }}
          >
            <option value="ko">한국어</option>
            <option value="en">English</option>
          </select>
        </label>
      </header>
      <main id="main">
        <h1 ref={headingRef} tabIndex={-1}>
          {text("appName")}
        </h1>
        <p role="status" aria-label="route announcement" className="visually-hidden">
          {location.pathname} 화면
        </p>
        <Outlet />
      </main>
    </>
  );
}
