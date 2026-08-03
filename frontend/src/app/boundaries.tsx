import { Component, type ErrorInfo, type PropsWithChildren, type ReactNode } from "react";
import { Button } from "@/shared/ui/primitives";

interface BoundaryState {
  failed: boolean;
}

export class AppFatalBoundary extends Component<PropsWithChildren, BoundaryState> {
  state: BoundaryState = { failed: false };
  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo): void {
    void error;
    void info;
    /* safe telemetry adapter is wired later */
  }
  render(): ReactNode {
    if (this.state.failed) {
      return (
        <main>
          <h1>애플리케이션을 시작하지 못했습니다</h1>
          <Button
            onClick={() => {
              window.location.reload();
            }}
          >
            다시 불러오기
          </Button>
        </main>
      );
    }
    return this.props.children;
  }
}

export class RemoteErrorBoundary extends Component<PropsWithChildren, BoundaryState> {
  state: BoundaryState = { failed: false };
  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }
  render(): ReactNode {
    if (this.state.failed) {
      return (
        <section aria-label="오류가 발생한 영역">
          <p role="alert">이 영역을 표시하지 못했습니다.</p>
          <Button
            onClick={() => {
              this.setState({ failed: false });
            }}
          >
            영역 다시 시도
          </Button>
        </section>
      );
    }
    return this.props.children;
  }
}
