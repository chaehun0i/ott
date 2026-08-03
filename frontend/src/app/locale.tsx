import { createContext, useContext, useMemo, useState, type PropsWithChildren } from "react";
import { resources } from "@/locales/resources";
import type { Locale } from "@/shared/model/presentation";

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  text: (key: "appName" | "nav.feed" | "nav.search" | "nav.recommend" | "nav.account") => string;
}

const LocaleContext = createContext<LocaleContextValue | undefined>(undefined);

export function LocaleProvider({ children }: PropsWithChildren) {
  const [locale, setLocale] = useState<Locale>("ko");
  const value = useMemo<LocaleContextValue>(() => {
    const dictionary = resources[locale];
    const map = {
      appName: dictionary.appName,
      "nav.feed": dictionary.nav.feed,
      "nav.search": dictionary.nav.search,
      "nav.recommend": dictionary.nav.recommend,
      "nav.account": dictionary.nav.account,
    };
    return { locale, setLocale, text: (key) => map[key] };
  }, [locale]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale(): LocaleContextValue {
  const value = useContext(LocaleContext);
  if (!value) throw new Error("LocaleProvider is required");
  return value;
}
