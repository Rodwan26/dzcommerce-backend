import { getRequestConfig } from "next-intl/server";
import { cookies, headers } from "next/headers";

const locales = ["ar", "fr", "en"] as const;
const defaultLocale = "ar";

function matchAcceptLanguage(accept: string | null): string {
  if (!accept) return defaultLocale;
  const preferred = accept.split(",").map((s) => s.split(";")[0].trim().slice(0, 2));
  for (const lang of preferred) {
    if ((locales as readonly string[]).includes(lang)) return lang;
  }
  return defaultLocale;
}

export default getRequestConfig(async () => {
  const cookieStore = await cookies();
  const cookie = cookieStore.get("NEXT_LOCALE")?.value;
  if (cookie && (locales as readonly string[]).includes(cookie)) {
    return {
      locale: cookie,
      messages: (await import(`../messages/${cookie}.json`)).default,
    };
  }

  const headersList = await headers();
  const accept = headersList.get("Accept-Language");
  const locale = matchAcceptLanguage(accept);

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
