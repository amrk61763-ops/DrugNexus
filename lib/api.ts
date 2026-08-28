export type TradeName = {
  trade_name: string
  manufacturer: string
}

export type IngredientSummary = {
  pubchem_cid: string
  chembl_id: string
  display_name: string
}

export type TradeNameResponse = {
  trade_name: string
  manufacturer: string
  drug_class: string
  active_ingredients: IngredientSummary[]
  alternatives: TradeName[]
}

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? ""

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, { signal, next: { revalidate: 60 } })
  if (!response.ok) throw new Error(`API request failed (${response.status})`)
  return response.json() as Promise<T>
}

export async function getTradeName(name: string, signal?: AbortSignal) {
  return request<TradeNameResponse>(`/trade-names/${encodeURIComponent(name)}`, signal)
}

export async function getApiStatus() {
  try { return await request<{ status: string; docs: string }>("/") }
  catch { return { status: "offline", docs: "/docs" } }
}
