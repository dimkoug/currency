export function convert(from, to, amount, rates) {
  const fromRate = rates[from];
  const toRate = rates[to];
  if (fromRate == null || toRate == null) return null;
  return (Number(amount) * Number(toRate)) / Number(fromRate);
}
