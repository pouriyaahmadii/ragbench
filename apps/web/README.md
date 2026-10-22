# Apps/Web — Frontend Application

This directory contains the Next.js 14 (App Router) frontend application.

## Structure

```
apps/web/
├── app/                    # Next.js App Router pages and layouts
│   ├── (auth)/            # Auth route group (future)
│   ├── (dashboard)/       # Main dashboard route group
│   ├── api/               # API route proxies (if needed)
│   ├── globals.css        # Global styles + Tailwind imports
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/
│   └── ui/                # shadcn/ui pattern components (Button, Card, Table, etc.)
├── features/              # Feature-based modules (domain-driven)
│   ├── documents/         # Document library, upload, detail
│   ├── chat/              # Chat/QA interface, citations
│   ├── evaluations/       # Dataset list, run evaluation, results
│   └── experiments/       # Experiment list, comparison, detail
├── hooks/                 # Shared React hooks (useApi, useDebounce, etc.)
├── lib/                   # Utilities, API client, config, types
│   ├── api/               # Generated TypeScript API client (from OpenAPI)
│   ├── utils.ts           # Common utilities (cn, formatters)
│   └── validations.ts     # Zod schemas for forms
├── public/                # Static assets (favicon, placeholder images)
├── tests/
│   └── e2e/               # Playwright end-to-end tests
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── eslint.config.js
└── playwright.config.ts
```

## Key Conventions

- **Feature-based organization:** Each feature is self-contained with its own components, hooks, and types
- **Generated API client:** Types and client generated from FastAPI OpenAPI spec via `openapi-typescript`
- **shadcn/ui pattern:** Copy-paste components in `components/ui/` — no external component library dependency
- **Server Components by default:** Use Client Components (`'use client'`) only when needed (interactivity, hooks)
- **TanStack Query:** Server state management for API calls (caching, invalidation, optimistic updates)

## Development

```bash
# From apps/web/
npm install
npm run dev          # Development server with hot reload
npm run build        # Production build
npm run lint         # ESLint + Prettier
npm run typecheck    # tsc --noEmit
npm run test         # Vitest unit tests
npm run test:e2e     # Playwright E2E tests
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL (e.g., `http://127.0.0.1:8000`) |

See `.env.example` in repository root for all variables.