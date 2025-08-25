export function toSignedString(num: number, numDecimals: number = 0): string {
  let decimal = Math.abs(num).toFixed(numDecimals);
  return ((num > 0)? '+' : '-') + decimal;
}