"use client"

import { useEffect, useMemo, useState } from "react"
import { Activity, ArrowUpRight, BarChart3, Bell, Boxes, ChevronRight, CircleHelp, FlaskConical, LayoutDashboard, Menu, PackageSearch, Search, Settings2, ShieldCheck, Sparkles, X } from "lucide-react"
import { getApiStatus, getTradeName, type TradeNameResponse } from "@/lib/api"

const fallback: TradeNameResponse = {
  trade_name: "Amoxicillin 500mg",
  manufacturer: "Nexus Therapeutics",
  drug_class: "Aminopenicillin",
  active_ingredients: [{ pubchem_cid: "3365", chembl_id: "CHEMBL1082", display_name: "Amoxicillin" }],
  alternatives: [{ trade_name: "Moxatag", manufacturer: "Alvogen" }, { trade_name: "Amoxil", manufacturer: "GSK" }],
}

const navItems = [
  { label: "Overview", icon: LayoutDashboard }, { label: "Drug library", icon: FlaskConical },
  { label: "Inventory", icon: Boxes }, { label: "Analytics", icon: BarChart3 },
]

function Metric({ label, value, change, icon: Icon, tone }: { label: string; value: string; change: string; icon: typeof Activity; tone: string }) {
  return <div className="flex min-w-0 flex-1 items-start justify-between rounded-2xl border bg-card p-5 shadow-[0_8px_30px_rgba(16,42,67,0.04)]">
    <div className="flex flex-col gap-3"><span className="text-sm font-medium text-muted-foreground">{label}</span><strong className="text-3xl font-semibold tracking-[-0.04em] text-foreground">{value}</strong><span className="text-xs font-medium text-accent-foreground">{change} this month</span></div>
    <span className={`flex size-10 items-center justify-center rounded-xl ${tone}`}><Icon className="size-5" /></span>
  </div>
}

export default function Dashboard() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [searching, setSearching] = useState(false)
  const [result, setResult] = useState<TradeNameResponse>(fallback)
  const [apiOnline, setApiOnline] = useState(true)
  const [notice, setNotice] = useState("")

  useEffect(() => { getApiStatus().then((status) => setApiOnline(status.status !== "offline")) }, [])
  useEffect(() => {
    if (!query.trim()) { setResult(fallback); return }
    const controller = new AbortController()
    const timer = window.setTimeout(async () => {
      setSearching(true)
      try { setResult(await getTradeName(query.trim(), controller.signal)); setNotice("") }
      catch { setNotice("No exact match found. Showing the workspace sample.") }
      finally { setSearching(false) }
    }, 350)
    return () => { controller.abort(); window.clearTimeout(timer) }
  }, [query])

  const chart = useMemo(() => [42, 58, 46, 66, 53, 72, 62, 78, 67, 84, 74, 92], [])
  return <div className="flex min-h-screen bg-background">
    <aside className={`fixed inset-y-0 left-0 z-20 flex w-64 flex-col border-r bg-card px-5 py-6 transition-transform lg:static lg:translate-x-0 ${menuOpen ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="flex items-center justify-between"><div className="flex items-center gap-3"><span className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground"><FlaskConical className="size-5" /></span><div><p className="text-base font-bold tracking-tight">Drug<span className="text-primary">Nexus</span></p><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Clinical intelligence</p></div></div><button className="lg:hidden" onClick={() => setMenuOpen(false)} aria-label="Close navigation"><X className="size-5" /></button></div>
      <nav className="mt-12 flex flex-col gap-2" aria-label="Main navigation">{navItems.map(({ label, icon: Icon }, index) => <button key={label} className={`flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition ${index === 0 ? "bg-secondary text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}><Icon className="size-[18px]" />{label}{index === 0 && <span className="ml-auto size-2 rounded-full bg-primary" />}</button>)}</nav>
      <div className="mt-auto flex flex-col gap-2"><button className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium text-muted-foreground hover:bg-muted"><Settings2 className="size-[18px]" />Settings</button><div className="mt-3 flex items-center gap-3 border-t pt-5"><span className="flex size-9 items-center justify-center rounded-full bg-accent text-sm font-bold text-accent-foreground">AM</span><div className="min-w-0"><p className="truncate text-sm font-semibold">Amina M.</p><p className="truncate text-xs text-muted-foreground">Clinical operations</p></div><ChevronRight className="ml-auto size-4 text-muted-foreground" /></div></div>
    </aside>
    {menuOpen && <button className="fixed inset-0 z-10 bg-foreground/20 lg:hidden" onClick={() => setMenuOpen(false)} aria-label="Close menu overlay" />}
    <main className="min-w-0 flex-1">
      <header className="flex h-20 items-center justify-between border-b bg-card px-5 sm:px-8"><div className="flex items-center gap-3"><button className="lg:hidden" onClick={() => setMenuOpen(true)} aria-label="Open navigation"><Menu className="size-5" /></button><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Workspace / Overview</p><h1 className="mt-1 text-xl font-semibold tracking-tight">Good morning, Amina</h1></div></div><div className="flex items-center gap-3"><button className="relative rounded-xl p-2 text-muted-foreground hover:bg-muted" aria-label="Notifications"><Bell className="size-5" /><span className="absolute right-1.5 top-1.5 size-1.5 rounded-full bg-primary" /></button><span className={`hidden items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold sm:flex ${apiOnline ? "bg-accent text-accent-foreground" : "bg-muted text-muted-foreground"}`}><span className={`size-1.5 rounded-full ${apiOnline ? "bg-accent-foreground" : "bg-muted-foreground"}`} />{apiOnline ? "API connected" : "Demo mode"}</span></div></header>
      <div className="mx-auto flex max-w-[1500px] flex-col gap-8 p-5 sm:p-8">
        <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><p className="text-sm text-muted-foreground">Thursday, 28 August 2026</p><h2 className="mt-2 max-w-xl text-balance text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">Make every medicine decision with clarity.</h2></div><button className="flex w-fit items-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-[0_8px_20px_rgba(23,105,170,0.18)] hover:opacity-90"><PackageSearch className="size-4" />Explore library<ArrowUpRight className="size-4" /></button></section>
        <section className="flex flex-col gap-4 md:flex-row"><Metric label="Tracked medicines" value="2,418" change="12.4%" icon={FlaskConical} tone="bg-secondary text-primary" /><Metric label="Active ingredients" value="684" change="8.2%" icon={Sparkles} tone="bg-accent text-accent-foreground" /><Metric label="Therapeutic classes" value="42" change="4.8%" icon={ShieldCheck} tone="bg-[#e9eef7] text-[#34558a]" /></section>
        <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]"><div className="rounded-2xl border bg-card p-5 sm:p-6"><div className="flex items-start justify-between"><div><h3 className="font-semibold">Medicine catalog growth</h3><p className="mt-1 text-sm text-muted-foreground">New records added across the network</p></div><button className="rounded-lg border px-3 py-2 text-xs font-semibold text-muted-foreground">Last 12 months</button></div><div className="mt-8 flex h-52 items-end gap-2 sm:gap-4">{chart.map((height, i) => <div key={i} className="flex flex-1 flex-col items-center gap-3"><div className="w-full rounded-t-lg bg-secondary transition hover:bg-primary" style={{ height: `${height}%` }} /><span className="text-[10px] text-muted-foreground">{["Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug"][i]}</span></div>)}</div></div>
          <div className="rounded-2xl border bg-foreground p-6 text-primary-foreground"><div className="flex items-start justify-between"><div><span className="flex size-10 items-center justify-center rounded-xl bg-primary/30"><Search className="size-5" /></span><h3 className="mt-5 text-xl font-semibold tracking-tight">Find a medicine</h3><p className="mt-2 max-w-xs text-sm leading-6 text-primary-foreground/65">Search by trade name to see ingredients, alternatives, and clinical context.</p></div><CircleHelp className="size-5 text-primary-foreground/50" /></div><label className="mt-7 flex items-center gap-3 rounded-xl bg-primary-foreground/10 px-4 py-3 ring-1 ring-primary-foreground/15"><Search className="size-4 text-primary-foreground/60" /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Try Amoxicillin..." className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-primary-foreground/45" aria-label="Search medicines" /></label>{notice && <p className="mt-3 text-xs text-[#bfe9df]">{notice}</p>}<div className="mt-6 border-t border-primary-foreground/15 pt-5"><div className="flex items-center justify-between text-xs text-primary-foreground/55"><span>{searching ? "Looking up..." : "Featured result"}</span><span className="rounded-full bg-primary-foreground/10 px-2 py-1">{result.drug_class}</span></div><div className="mt-3 flex items-center justify-between"><div><p className="font-semibold">{result.trade_name}</p><p className="mt-1 text-xs text-primary-foreground/55">{result.manufacturer}</p></div><ArrowUpRight className="size-4 text-primary-foreground/60" /></div></div></div></section>
        <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]"><div className="overflow-hidden rounded-2xl border bg-card"><div className="flex items-center justify-between p-5 sm:p-6"><div><h3 className="font-semibold">Recently added medicines</h3><p className="mt-1 text-sm text-muted-foreground">Latest records in your library</p></div><button className="text-sm font-semibold text-primary">View all</button></div><div className="overflow-x-auto"><table className="w-full min-w-[600px] text-left text-sm"><thead className="border-y bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground"><tr><th className="px-5 py-3 font-semibold sm:px-6">Medicine</th><th className="px-5 py-3 font-semibold">Class</th><th className="px-5 py-3 font-semibold">Ingredients</th><th className="px-5 py-3 font-semibold">Status</th></tr></thead><tbody>{[{name:"Zepbound 10mg",maker:"Eli Lilly",kind:"Metabolic",count:"2"},{name:"Lenvima 4mg",maker:"Eisai",kind:"Oncology",count:"1"},{name:"Entresto 49/51mg",maker:"Novartis",kind:"Cardiovascular",count:"2"}].map((drug) => <tr key={drug.name} className="border-b last:border-0"><td className="px-5 py-4 sm:px-6"><p className="font-semibold">{drug.name}</p><p className="mt-1 text-xs text-muted-foreground">{drug.maker}</p></td><td className="px-5 py-4 text-muted-foreground">{drug.kind}</td><td className="px-5 py-4 text-muted-foreground">{drug.count} active</td><td className="px-5 py-4"><span className="rounded-full bg-accent px-2.5 py-1 text-xs font-semibold text-accent-foreground">Verified</span></td></tr>)}</tbody></table></div></div><div className="rounded-2xl border bg-card p-5 sm:p-6"><div className="flex items-center justify-between"><div><h3 className="font-semibold">Network activity</h3><p className="mt-1 text-sm text-muted-foreground">What&apos;s happening today</p></div><Activity className="size-5 text-primary" /></div><div className="mt-6 flex flex-col gap-5">{[{text:"New ingredient profile verified",time:"12 min ago",dot:"bg-accent-foreground"},{text:"Drug alternative relationship added",time:"48 min ago",dot:"bg-primary"},{text:"Catalog sync completed",time:"2 hrs ago",dot:"bg-[#34558a]"}].map((item) => <div key={item.text} className="flex gap-3"><span className={`mt-1.5 size-2 shrink-0 rounded-full ${item.dot}`} /><div><p className="text-sm font-medium">{item.text}</p><p className="mt-1 text-xs text-muted-foreground">{item.time}</p></div></div>)}</div></div></section>
      </div>
    </main>
  </div>
}
