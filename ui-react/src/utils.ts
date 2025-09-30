export function toSignedString(num: number, numDecimals: number = 0): string {
  const decimal = Math.abs(num).toFixed(numDecimals);
  return ((num > 0)? '+' : '-') + decimal;
}