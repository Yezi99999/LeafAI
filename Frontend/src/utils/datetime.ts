// 后端接口返回的时间为无时区的 UTC 字符串。统一补 'Z' 使 JS 按 UTC 解析，再换算成本地时区展示。
// 若字符串本身已带时区标记（Z 或 ±HH:MM），则原样使用。
export function toLocalDateTime(iso: string): string {
  const normalized = /([zZ]|[+-]\d{2}:?\d{2})$/.test(iso) ? iso : `${iso}Z`
  const d = new Date(normalized)
  return isNaN(d.getTime()) ? iso : d.toLocaleString()
}

// 简短时间：M-d HH:mm（本地时区）
export function toLocalShort(iso: string): string {
  const normalized = /([zZ]|[+-]\d{2}:?\d{2})$/.test(iso) ? iso : `${iso}Z`
  const d = new Date(normalized)
  if (isNaN(d.getTime())) return ''
  return `${d.getMonth() + 1}-${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}