# -*- coding: utf-8 -*-
"""قالب صفحة الدواء - نفس تصميم index.html (Tailwind + monochrome + dark mode).
الأماكن اللي بتتبدل: {{TITLE}} {{DESC}} {{CANON}} {{ROBOTS}} {{JSONLD}} {{BODY}}
ملاحظة: كل مسارات الصور absolute (/assets/...) لأن الصفحة بتتفتح على /drug/ID/slug."""

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=GT-MQP3XHTN"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','GT-MQP3XHTN');</script>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="color-scheme" content="light dark" />
  <title>{{TITLE}}</title>
  <meta name="description" content="{{DESC}}" />
  <meta name="robots" content="{{ROBOTS}}" />
  <link rel="canonical" href="{{CANON}}" />
  <meta name="theme-color" content="#FAFAF9" media="(prefers-color-scheme: light)" />
  <meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="ViaDrug" />
  <meta property="og:title" content="{{TITLE}}" />
  <meta property="og:description" content="{{DESC}}" />
  <meta property="og:url" content="{{CANON}}" />
  <meta property="og:image" content="https://viadrug.app/assets/hero-molecule.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <script type="application/ld+json">{{JSONLD}}</script>
  <link rel="icon" href="/assets/logo.png">
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = { darkMode: 'class', theme: { extend: {
      colors: { ink:'#0A0A0A', paper:'#FAFAF9', mute:'#71717A', faint:'#A1A1AA', hair:'#E4E4E7', coal:'#000000', snow:'#FAFAFA', dhair:'#1C1C1E' },
      fontFamily: { sans:['"Inter"','system-ui','sans-serif'], mono:['"IBM Plex Mono"','ui-monospace','monospace'] },
      letterSpacing: { tightest:'-0.045em' } } } }
    function swapLogo(d){document.querySelectorAll('img[data-logo]').forEach(function(i){i.src=d?'/assets/logo-white.png':'/assets/logo.png';});}
    (function(){
      const mq=window.matchMedia('(prefers-color-scheme: dark)');
      const apply=(d)=>{document.documentElement.classList.toggle('dark',d);document.documentElement.style.colorScheme=d?'dark':'light';};
      const saved=localStorage.getItem('viadrug-theme');
      const dark=saved?saved==='dark':mq.matches; apply(dark);
      document.addEventListener('DOMContentLoaded',()=>swapLogo(dark));
    })();
    function toggleTheme(){const r=document.documentElement;const d=r.classList.toggle('dark');r.style.colorScheme=d?'dark':'light';localStorage.setItem('viadrug-theme',d?'dark':'light');swapLogo(d);}
  </script>
  <style>
    ::selection{background:#0A0A0A;color:#FAFAFA}.dark ::selection{background:#FAFAFA;color:#0A0A0A}
    .thin-scroll::-webkit-scrollbar{width:5px;height:5px}.thin-scroll::-webkit-scrollbar-thumb{background:#D4D4D8;border-radius:3px}
    .dark .thin-scroll::-webkit-scrollbar-thumb{background:#2C2C30}.thin-scroll{scrollbar-width:thin}
    .ddi-head{background:#F4F4F5}.dark .ddi-head{background:#1C1C1E}
    details>summary{list-style:none;cursor:pointer}details>summary::-webkit-details-marker{display:none}
    details[open] .chev{transform:rotate(180deg)}
    .fade-up{animation:fadeUp .7s cubic-bezier(.2,.8,.2,1) both}@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
  </style>
</head>
<body class="font-sans bg-paper text-ink dark:bg-coal dark:text-snow antialiased transition-colors duration-300">

  <header class="sticky top-0 z-50 bg-paper/85 dark:bg-coal/85 backdrop-blur-xl border-b border-hair dark:border-dhair">
    <nav class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <a href="/" class="flex items-center gap-1">
        <span class="w-6 h-6 grid place-items-center"><img src="/assets/logo.png" data-logo alt="ViaDrug logo" class="w-5 h-5"></span>
        <span class="text-[15px] font-bold tracking-tight">ViaDrug</span>
      </a>
      <div class="flex items-center gap-3">
        <button type="button" onclick="toggleTheme()" aria-label="Toggle dark mode" class="w-9 h-9 grid place-items-center rounded-full border border-hair dark:border-dhair hover:border-ink dark:hover:border-snow transition-colors">
          <svg class="w-4 h-4 dark:hidden" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          <svg class="w-4 h-4 hidden dark:block" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        </button>
        <a href="/#search" class="inline-flex items-center text-[13px] font-semibold text-paper dark:text-coal bg-ink dark:bg-snow px-5 py-2 rounded-full hover:opacity-75 transition-opacity">Search another drug</a>
      </div>
    </nav>
  </header>

  <main class="max-w-7xl mx-auto px-6 py-12 sm:py-16 fade-up">
{{BODY}}
  </main>

  <footer class="py-14 border-t border-hair dark:border-dhair">
    <div class="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5">
      <div>
        <a href="/" class="inline-flex items-center gap-2.5"><span class="w-5 h-5 grid place-items-center"><img src="/assets/logo.png" data-logo alt="ViaDrug logo" class="w-5 h-5"></span><span class="text-[15px] font-bold tracking-tight">ViaDrug</span></a>
        <p class="mt-2 text-sm text-mute dark:text-[#9C9CA3]">One drug. Every layer of evidence, connected.</p>
        <p lang="ar" dir="rtl" class="mt-2 text-sm text-mute dark:text-[#9C9CA3] max-w-md">ViaDrug مرجع علمي للأدوية في السوق المصري: ابحث بالاسم التجاري لتعرف المادة الفعّالة والبدائل والتداخلات الدوائية.</p>
      </div>
      <p class="text-[13px] font-mono text-mute dark:text-[#9C9CA3]">© 2026 ViaDrug · Amr Khaled Abdelkader. All rights reserved.</p>
    </div>
    <div class="max-w-7xl mx-auto px-6 mt-8 pt-6 border-t border-hair dark:border-dhair">
      <nav aria-label="Legal" class="flex flex-wrap gap-x-5 gap-y-1.5 text-[12px] text-mute dark:text-[#9C9CA3]">
        <a href="/terms/" class="hover:text-ink dark:hover:text-snow transition-colors">Terms &amp; Conditions</a>
        <a href="/privacy/" class="hover:text-ink dark:hover:text-snow transition-colors">Privacy</a>
        <a href="/disclaimer/" class="hover:text-ink dark:hover:text-snow transition-colors">Medical Disclaimer</a>
        <a href="/advertising-policy/" class="hover:text-ink dark:hover:text-snow transition-colors">Advertising Policy</a>
        <a href="/data-sources/" class="hover:text-ink dark:hover:text-snow transition-colors">Data Sources</a>
      </nav>
      <p class="mt-4 text-[12px] leading-relaxed text-faint dark:text-[#8E8E96] max-w-3xl">ViaDrug is an educational and scientific reference, not medical advice. Always consult a doctor or pharmacist before using or changing any medicine.</p>
    </div>
  </footer>
</body>
</html>
"""
