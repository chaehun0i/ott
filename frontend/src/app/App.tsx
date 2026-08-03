import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "@/styles/tokens.css";
import { AppShell } from "./AppShell";
import { AppFatalBoundary, RemoteErrorBoundary } from "./boundaries";
import { LocaleProvider } from "./locale";
import { FeedPage, NotFoundPage } from "@/routes/feed";

const SearchPage = lazy(() => import("@/routes/route-search"));
const DetailPage = lazy(() => import("@/routes/route-detail"));
const RecommendationPage = lazy(() => import("@/routes/route-recommendation"));
const AccountPage = lazy(() => import("@/routes/route-account"));
const AdminPage = lazy(() => import("@/routes/route-admin"));
const NotificationsPage = lazy(() => import("@/routes/route-notifications"));
const LoginPage = lazy(() => import("@/routes/route-login"));

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppFatalBoundary>
          <LocaleProvider>
            <Suspense fallback={<p role="status">화면을 불러오는 중입니다.</p>}>
              <Routes>
                <Route element={<AppShell />}>
                  <Route index element={<Navigate replace to="/feed" />} />
                  <Route
                    path="feed"
                    element={
                      <RemoteErrorBoundary>
                        <FeedPage />
                      </RemoteErrorBoundary>
                    }
                  />
                  <Route
                    path="content/:contentId"
                    element={
                      <RemoteErrorBoundary>
                        <DetailPage />
                      </RemoteErrorBoundary>
                    }
                  />
                  <Route
                    path="search"
                    element={
                      <RemoteErrorBoundary>
                        <SearchPage />
                      </RemoteErrorBoundary>
                    }
                  />
                  <Route path="notifications" element={<NotificationsPage />} />
                  <Route path="login" element={<LoginPage />} />
                  <Route
                    path="recommend"
                    element={
                      <RemoteErrorBoundary>
                        <RecommendationPage />
                      </RemoteErrorBoundary>
                    }
                  />
                  <Route
                    path="account"
                    element={
                      <RemoteErrorBoundary>
                        <AccountPage />
                      </RemoteErrorBoundary>
                    }
                  />
                  <Route
                    path="admin/*"
                    element={
                      <RemoteErrorBoundary>
                        <AdminPage />
                      </RemoteErrorBoundary>
                    }
                  />
                  <Route path="*" element={<NotFoundPage />} />
                </Route>
              </Routes>
            </Suspense>
          </LocaleProvider>
        </AppFatalBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
