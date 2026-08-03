export type PendingAction = "save" | "rate" | "subscribe";

export interface PendingIntent {
  action: PendingAction;
  consumed: boolean;
  contentRef: string;
  returnPath: string;
}

export type LoginEvent = "begin" | "fail" | "succeed" | "retry";

export interface LoginModel {
  authenticated: boolean;
  executionCount: number;
  intent?: PendingIntent;
}

export function validReturnPath(path: string): boolean {
  return path.startsWith("/") && !path.startsWith("//") && !path.includes("\\");
}

export function createPendingIntent(
  action: PendingAction,
  contentRef: string,
  returnPath: string,
): PendingIntent {
  if (!contentRef || !validReturnPath(returnPath)) throw new Error("Invalid pending intent");
  return { action, consumed: false, contentRef, returnPath };
}

export function transitionLogin(model: LoginModel, event: LoginEvent): LoginModel {
  if (event === "fail") return { ...model, authenticated: false };
  if (event === "begin" || event === "retry") return model;
  if (!model.intent || model.intent.consumed) return { ...model, authenticated: true };
  return {
    authenticated: true,
    executionCount: model.executionCount + 1,
    intent: { ...model.intent, consumed: true },
  };
}

export class SingleFlightAuthentication {
  #active: Promise<boolean> | undefined;
  run(authenticate: () => Promise<boolean>): Promise<boolean> {
    this.#active ??= authenticate().finally(() => {
      this.#active = undefined;
    });
    return this.#active;
  }
}
