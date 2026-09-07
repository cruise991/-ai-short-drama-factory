import { useState, useEffect } from 'react';
import en from './en.json';
import zh from './zh.json';

export type Language = 'en' | 'zh';

const dictionaries: Record<Language, any> = { en, zh };

let currentLang: Language = (localStorage.getItem('app_lang') as Language) || 'en';
const listeners = new Set<(lang: Language) => void>();

export function setLanguage(lang: Language) {
  currentLang = lang;
  localStorage.setItem('app_lang', lang);
  listeners.forEach((listener) => listener(lang));
}

export function getLanguage(): Language {
  return currentLang;
}

export function useTranslation() {
  const [lang, setLang] = useState<Language>(currentLang);

  useEffect(() => {
    const handleLangChange = (newLang: Language) => setLang(newLang);
    listeners.add(handleLangChange);
    return () => {
      listeners.delete(handleLangChange);
    };
  }, []);

  const t = (path: string, paramsOrFallback?: Record<string, any> | string, fallback?: string): string => {
    const keys = path.split('.');
    let value = dictionaries[lang];
    for (const key of keys) {
      if (value && typeof value === 'object' && key in value) {
        value = value[key];
      } else {
        return typeof paramsOrFallback === 'string' ? paramsOrFallback : fallback || path;
      }
    }
    let res = typeof value === 'string' ? value : (typeof paramsOrFallback === 'string' ? paramsOrFallback : fallback || path);
    if (paramsOrFallback && typeof paramsOrFallback === 'object') {
      Object.entries(paramsOrFallback).forEach(([k, v]) => {
        res = res.replace(new RegExp(`{{\\s*${k}\\s*}}`, 'g'), String(v));
      });
    }
    return res;
  };

  return { t, lang, setLanguage };
}
