"use client"

import { useEffect, useState } from "react"
import { ArrowRight, Check, ChevronRight, Copy, Search, Share2 } from "lucide-react"
import { getApiStatus, getTradeName, type TradeNameResponse } from "@/lib/api"

const fallback: TradeNameResponse = {
  trade_name: "Amoxicillin 500mg",
  manufacturer: "Nexus Therapeutics",
  drug_class: "Aminopenicillin",
  active_ingredients: [{ pubchem_cid: "3365", chembl_id: "CHEMBL1082", display_name: "Amoxicillin" }],
  alternatives: [{ trade_name: "Moxatag", manufacturer: "Alvogen" }, { trade_name: "Amoxil", manufacturer: "GSK" }],
}

function Logo() {
  return <div className="flex items-center gap-3"><span className="relative flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground"><span className="absolute h-5 w-px bg-primary-foreground/80" /><span className="absolute h-px w-5 bg-primary-foreground/80" /><span className="relative size-2 rounded-full bg-primary-foreground" /></span><span className="text-lg font-semibold tracking-tight">Drug <span className="text-primary">Nexus</span></span></div>
}

function Identifier({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  return <div className="group flex items-center justify-between gap-4 border-b py-4 last:border-0"><div><p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">{label}</p><p className="mt-1 font-mono text-sm text-foreground">{value}</p></div><button aria-label={`Copy ${label}`} className="rounded-md p-2 text-muted-foreground opacity-0 transition group-hover:opacity-100 hover:bg-muted hover:text-foreground" onClick={() => { navigator.clipboard?.writeText(value); setCopied(true); window.setTimeout(() => setCopied(false), 1400) }}>{copied ? <Check className="size-4 text-accent-foreground" /> : <Copy className="size-4" />}</button></div>
}

export default function Dashboard() {
  const [query, setQuery] = useState("")
  const [result, setResult] = useState<TradeNameResponse>(fallback)
  const [searching, setSearching] = useState(false)
  const [apiOnline, setApiOnline] = useState(false)
  const [searched, setSearched] = useState(false)

  useEffect(() => { getApiStatus().then((status) => setApiOnline(status.status !== "offline")) }, [])
  useEffect(() => {
    if (!query.trim()) { setResult(fallback); setSearched(false); return }
    const controller = new AbortController()
    const timer = window.setTimeout(async () => {
      setSearching(true); setSearched(true)
      try { setResult(await getTradeName(query.trim(), controller.signal)) } catch { setResult(fallback) } finally { setSearching(false) }
    }, 350)
    return () => { controller.abort(); window.clearTimeout(timer) }
  }, [query])

  return <main className="min-h-screen bg-background">
    <header className="border-b bg-background/95"><div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8"><Logo /><nav className="hidden items-center gap-8 text-sm text-muted-foreground md:flex"><a className="text-foreground" href="#search">Search</a><a href="#explore" className="hover:text-foreground">Drugs</a><a href="#science" className="hover:text-foreground">Active ingredients</a></nav><div className="flex items-center gap-4"><span className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex"><span className={`size-1.5 rounded-full ${apiOnline ? "bg-accent-foreground" : "bg-muted-foreground"}`} />{apiOnline ? "Live data" : "Reference mode"}</span><button className="rounded-lg border px-3 py-2 text-sm font-medium hover:bg-card">About</button></div></div></header>
    <section id="search" className="mx-auto flex max-w-7xl flex-col gap-10 px-5 pb-20 pt-20 sm:px-8 sm:pt-28 lg:flex-row lg:items-end lg:justify-between"><div className="max-w-2xl"><p className="mb-6 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-accent-foreground"><span className="size-2 rounded-full bg-accent-foreground" />Connected drug knowledge</p><h1 className="text-balance text-5xl font-semibold leading-[1.05] tracking-[-0.06em] text-foreground sm:text-7xl">Understand the drug <span className="text-primary">beyond its name.</span></h1><p className="mt-7 max-w-lg text-base leading-7 text-muted-foreground sm:text-lg">Start with a trade name or active ingredient. Follow the connections from product information to the science behind it.</p></div><div className="w-full max-w-xl lg:pb-2"><label className="mb-3 block text-sm font-semibold" htmlFor="drug-search">Search Drug Nexus</label><div className="flex items-center gap-3 rounded-2xl border bg-card px-4 py-2 shadow-[0_14px_40px_rgba(26,51,76,0.08)] focus-within:ring-2 focus-within:ring-ring"><Search className="size-5 text-muted-foreground" /><input id="drug-search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Trade name or active ingredient" className="min-w-0 flex-1 bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground/70" /><kbd className="hidden rounded-md bg-muted px-2 py-1 font-mono text-[10px] text-muted-foreground sm:block">⌘ K</kbd></div><p className="mt-3 text-xs text-muted-foreground">Try “Amoxicillin”, “Augmentin”, or another medicine name.</p></div></section>
    <div className="border-y bg-card"><div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-8 gap-y-3 px-5 py-4 text-sm sm:px-8"><span className="font-medium text-foreground">One drug, connected clearly</span><span className="text-muted-foreground">Trade product <ChevronRight className="mx-1 inline size-3" /> Active ingredient <ChevronRight className="mx-1 inline size-3" /> Scientific context</span></div></div>
    <section id="explore" className="mx-auto max-w-7xl px-5 py-16 sm:px-8"><div className="mb-8 flex items-end justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">{searched ? "Search result" : "A place to begin"}</p><h2 className="mt-2 text-2xl font-semibold tracking-tight">{searching ? "Looking up your medicine…" : result.trade_name}</h2></div><span className="rounded-full bg-accent px-3 py-1.5 text-xs font-semibold text-accent-foreground">{result.drug_class}</span></div><div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]"><article className="rounded-2xl border bg-background p-6 sm:p-8"><div className="flex flex-col gap-8 sm:flex-row sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">Trade product</p><h3 className="mt-3 text-3xl font-semibold tracking-tight">{result.trade_name}</h3><p className="mt-2 text-sm text-muted-foreground">Manufactured by {result.manufacturer}</p></div><div className="flex size-24 shrink-0 items-center justify-center rounded-2xl border bg-card text-center"><div><div className="mx-auto mb-2 size-7 rounded-lg border-2 border-primary" /><p className="font-mono text-[9px] uppercase tracking-widest text-muted-foreground">Product</p></div></div></div><div className="mt-10 border-t pt-6"><p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">Contains</p><div className="mt-4 flex flex-col gap-3">{result.active_ingredients.map((ingredient) => <button key={ingredient.display_name} className="flex items-center justify-between rounded-xl border bg-card px-4 py-4 text-left transition hover:border-primary hover:shadow-sm"><div><p className="font-semibold text-primary">{ingredient.display_name}</p><p className="mt-1 text-xs text-muted-foreground">Active ingredient · PubChem {ingredient.pubchem_cid}</p></div><ArrowRight className="size-4 text-muted-foreground" /></button>)}</div></div></article><aside id="science" className="rounded-2xl bg-primary p-6 text-primary-foreground sm:p-8"><div className="flex items-center justify-between"><p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary-foreground/70">Explore deeper</p><Share2 className="size-4 text-primary-foreground/60" /></div><h3 className="mt-10 text-2xl font-semibold tracking-tight">The name is only the beginning.</h3><p className="mt-3 text-sm leading-6 text-primary-foreground/70">Open an ingredient to follow its chemical identity, pharmacology, scientific identifiers, and structural evidence.</p><div className="mt-10 flex flex-col gap-1 border-t border-primary-foreground/20 pt-2"><Identifier label="PubChem CID" value={result.active_ingredients[0]?.pubchem_cid ?? "—"} /><Identifier label="ChEMBL ID" value={result.active_ingredients[0]?.chembl_id ?? "—"} /><Identifier label="PDB evidence" value="Explore when available" /></div></aside></div></section>
    <section className="border-t bg-card"><div className="mx-auto grid max-w-7xl gap-8 px-5 py-14 sm:px-8 md:grid-cols-3"><div><p className="font-mono text-xs text-accent-foreground">01</p><h3 className="mt-3 font-semibold">Start familiar</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">Search the trade name you already know.</p></div><div><p className="font-mono text-xs text-accent-foreground">02</p><h3 className="mt-3 font-semibold">See what it contains</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">Move from a product to its active ingredients.</p></div><div><p className="font-mono text-xs text-accent-foreground">03</p><h3 className="mt-3 font-semibold">Follow the science</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">Go deeper only when the question calls for it.</p></div></div></section>
    <footer className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-8 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-8"><Logo /><span>Drug knowledge, connected with clarity.</span></footer>
  </main>
}
