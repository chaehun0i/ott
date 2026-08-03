import type { ButtonHTMLAttributes, PropsWithChildren, ReactNode } from "react";
import { useId, useRef } from "react";

export function Button(props: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type="button" {...props} />;
}

export function Field({
  error,
  hint,
  label,
  name,
  children,
}: PropsWithChildren<{ error?: string; hint?: string; label: string; name: string }>) {
  const generated = useId();
  const hintId = hint ? `${generated}-hint` : undefined;
  const errorId = error ? `${generated}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div>
      <label htmlFor={name}>{label}</label>
      <div data-field-control={name} data-describedby={describedBy}>
        {children}
      </div>
      {hint ? <p id={hintId}>{hint}</p> : null}
      {error ? (
        <p id={errorId} role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function ErrorSummary({
  errors,
}: {
  errors: ReadonlyArray<{ fieldId: string; message: string }>;
}) {
  const ref = useRef<HTMLDivElement>(null);
  return (
    <div ref={ref} role="alert" tabIndex={-1}>
      <h2>입력 내용을 확인해 주세요</h2>
      <ul>
        {errors.map((error) => (
          <li key={error.fieldId}>
            <a href={`#${error.fieldId}`}>{error.message}</a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Disclosure({ label, children }: PropsWithChildren<{ label: string }>) {
  return (
    <details>
      <summary>{label}</summary>
      <div>{children}</div>
    </details>
  );
}

export function LiveRegion({ children }: { children: ReactNode }) {
  return (
    <div aria-live="polite" aria-atomic="true">
      {children}
    </div>
  );
}

export function RemoteRegion({
  label,
  status,
  children,
}: PropsWithChildren<{ label: string; status: "loading" | "ready" | "error" | "stale" }>) {
  return (
    <section aria-busy={status === "loading"} aria-label={label}>
      {status === "error" ? <p role="alert">영역을 불러오지 못했습니다.</p> : children}
      {status === "stale" ? <p role="status">마지막으로 확인된 정보를 표시합니다.</p> : null}
    </section>
  );
}

export function errorReferenceGraph(names: readonly string[]) {
  return names.map((name, index) => ({
    controlId: `field-${String(index)}-${name}`,
    errorId: `error-${String(index)}-${name}`,
  }));
}
