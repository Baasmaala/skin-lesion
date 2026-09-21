import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { translations } from "./translations.js";

const LANG_KEY = "rareflect-lang";
const LanguageContext = createContext(null);

function getInitialLang() {
  try {
    const stored = localStorage.getItem(LANG_KEY);
    if (stored === "en" || stored === "ar") return stored;
  } catch {
    // localStorage unavailable, fall through to default
  }
  return "en";
}

function readPath(obj, path) {
  return path.split(".").reduce((acc, key) => (acc == null ? acc : acc[key]), obj);
}

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(getInitialLang);
  const dir = lang === "ar" ? "rtl" : "ltr";

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
    try {
      localStorage.setItem(LANG_KEY, lang);
    } catch {
      // localStorage unavailable, language just won't persist across visits
    }
  }, [lang, dir]);

  const value = useMemo(() => {
    const t = (path) => {
      const value = readPath(translations[lang], path) ?? readPath(translations.en, path);
      return value ?? path;
    };
    // Backend class names (e.g. "Melanoma") are plain English strings, not
    // translation keys, so they need a lookup by value rather than by path.
    // Falls back to the original name for anything not in the table
    // (English mode, or a blocked-result message that isn't a class name).
    const tName = (name) => translations.ar.classNames?.[name] && lang === "ar"
      ? translations.ar.classNames[name]
      : name;
    return { lang, setLang, dir, t, tName };
  }, [lang, dir]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within a LanguageProvider");
  return ctx;
}
