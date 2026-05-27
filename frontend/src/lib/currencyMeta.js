// Display metadata for the currencies we support. The backend only stores codes,
// so the frontend supplies human-friendly names and flags for a polished UI.
const META = {
  EUR: { name: "Euro", flag: "🇪🇺" },
  USD: { name: "US Dollar", flag: "🇺🇸" },
  GBP: { name: "British Pound", flag: "🇬🇧" },
  JPY: { name: "Japanese Yen", flag: "🇯🇵" },
  CHF: { name: "Swiss Franc", flag: "🇨🇭" },
  AUD: { name: "Australian Dollar", flag: "🇦🇺" },
  CAD: { name: "Canadian Dollar", flag: "🇨🇦" },
};

export function currencyMeta(code) {
  return META[code] || { name: code, flag: "💱" };
}
