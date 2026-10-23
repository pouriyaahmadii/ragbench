# RAGBench Design System

## Overview

A professional AI engineering lab aesthetic: data-dense but readable, clear experiment comparison tables, restrained color usage, no gratuitous animation, no fake charts, no imaginary metrics.

## Color System

### Semantic Color Tokens (HSL)

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--background` | 0 0% 100% | 222.2 84% 4.9% | Page background |
| `--foreground` | 222.2 84% 4.9% | 210 40% 98% | Primary text |
| `--card` | 0 0% 100% | 222.2 84% 4.9% | Card surfaces |
| `--card-foreground` | 222.2 84% 4.9% | 210 40% 98% | Card text |
| `--popover` | 0 0% 100% | 222.2 84% 4.9% | Popover surfaces |
| `--popover-foreground` | 222.2 84% 4.9% | 210 40% 98% | Popover text |
| `--primary` | 221.2 83.2% 53.3% | 217.2 91.2% 59.8% | Primary actions, links |
| `--primary-foreground` | 210 40% 98% | 222.2 47.4% 11.2% | Text on primary |
| `--secondary` | 210 40% 96.1% | 217.2 32.6% 17.5% | Secondary surfaces |
| `--secondary-foreground` | 222.2 47.4% 11.2% | 210 40% 98% | Secondary text |
| `--muted` | 210 40% 96.1% | 217.2 32.6% 17.5% | Muted surfaces |
| `--muted-foreground` | 215.4 16.3% 46.9% | 215 20.2% 65.1% | Muted text |
| `--accent` | 210 40% 96.1% | 217.2 32.6% 17.5% | Accent surfaces |
| `--accent-foreground` | 222.2 47.4% 11.2% | 210 40% 98% | Accent text |
| `--destructive` | 0 84.2% 60.2% | 0 62.8% 30.6% | Destructive actions |
| `--destructive-foreground` | 210 40% 98% | 210 40% 98% | Text on destructive |
| `--border` | 214.3 31.8% 91.4% | 217.2 32.6% 17.5% | Borders, dividers |
| `--input` | 214.3 31.8% 91.4% | 217.2 32.6% 17.5% | Input borders |
| `--ring` | 221.2 83.2% 53.3% | 224.3 76.3% 48% | Focus rings |

### Status Colors

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--status-success` | 142 76% 36% | 142 76% 36% | Success states, completed |
| `--status-warning` | 38 92% 50% | 38 92% 50% | Warning states, in-progress |
| `--status-error` | 0 84% 60% | 0 84% 60% | Error states, failed |
| `--status-info` | 221 83% 53% | 221 83% 53% | Info states, pending |

### Usage Guidelines

- **Primary**: Main CTAs, active navigation, key links
- **Secondary**: Secondary actions, outline buttons
- **Destructive**: Delete, remove, irreversible actions
- **Muted**: Disabled states, placeholder text, secondary labels
- **Status colors**: Badges, toast notifications, inline status indicators only
- **No gradients** on interactive elements
- **No decorative color** - every color has semantic meaning

## Typography

### Font Families

```css
--font-sans: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
```

### Type Scale

| Token | Size | Line Height | Letter Spacing | Usage |
|-------|------|-------------|----------------|-------|
| `display-xl` | 4.5rem | 1.1 | -0.02em | Hero headlines |
| `display-lg` | 3.75rem | 1.1 | -0.02em | Page titles |
| `display-md` | 3rem | 1.2 | -0.01em | Section headers |
| `display-sm` | 2.25rem | 1.2 | -0.01em | Card titles |
| `heading-xl` | 1.875rem | 1.3 | -0.01em | Major sections |
| `heading-lg` | 1.5rem | 1.3 | -0.01em | Subsections |
| `heading-md` | 1.25rem | 1.4 | 0 | Table headers |
| `heading-sm` | 1.125rem | 1.4 | 0 | Card headers |
| `body-lg` | 1.125rem | 1.6 | 0 | Lead paragraphs |
| `body-md` | 1rem | 1.6 | 0 | Body text (default) |
| `body-sm` | 0.875rem | 1.5 | 0 | Secondary text |
| `caption` | 0.75rem | 1.5 | 0 | Metadata, timestamps |

### Usage Rules

- **Sans-serif** for all UI text
- **Mono** for code, IDs, hashes, timestamps, metrics
- Max line length: 75ch for body text
- Left-aligned by default; numbers right-aligned in tables
- No all-caps for body text (use `heading-sm` with `font-medium` instead)

## Spacing Scale

Base unit: 4px (0.25rem)

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 0.25rem (4px) | Tight gaps, icon padding |
| `space-2` | 0.5rem (8px) | Component internal padding |
| `space-3` | 0.75rem (12px) | Form field gaps |
| `space-4` | 1rem (16px) | Card padding, default gap |
| `space-5` | 1.25rem (20px) | Section gaps |
| `space-6` | 1.5rem (24px) | Major section gaps |
| `space-8` | 2rem (32px) | Page section gaps |
| `space-10` | 2.5rem (40px) | Large layout gaps |
| `space-12` | 3rem (48px) | Hero sections |
| `space-16` | 4rem (64px) | Page-level margins |
| `space-18` | 4.5rem (72px) | Custom |
| `space-20` | 5rem (80px) | Custom |
| `space-88` | 22rem (352px) | Max content width |
| `space-128` | 32rem (512px) | Custom |

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 0.25rem (4px) | Badges, tags, small inputs |
| `radius-md` | 0.375rem (6px) | Buttons, inputs, cards |
| `radius-lg` | 0.5rem (8px) | Modals, drawers, large cards |
| `radius-full` | 9999px | Pills, avatars, progress |

## Shadows (Elevation)

| Token | Value | Usage |
|-------|-------|-------|
| `elevation-1` | 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1) | Cards, dropdowns |
| `elevation-2` | 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1) | Hovered cards, tooltips |
| `elevation-3` | 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1) | Modals, drawers |
| `elevation-4` | 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1) | Toasts, popovers |

## Component Library

### Buttons

**Variants**: `default` | `secondary` | `outline` | `ghost` | `destructive` | `link`
**Sizes**: `sm` | `md` | `lg` | `icon`

```tsx
<Button variant="default" size="md">Primary Action</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Delete</Button>
<Button variant="link">Link</Button>
```

- Default: Primary background, white text
- Secondary: Muted background, foreground text
- Outline: Transparent, border, foreground text
- Ghost: Transparent, no border, foreground text
- Destructive: Error background, white text
- Link: Underlined text, no padding

**States**: hover, active, focus-visible, disabled, loading
**Loading**: Spinner + disabled, preserves width

### Inputs

**Types**: `text` | `password` | `email` | `number` | `search` | `textarea`

```tsx
<Input 
  label="Query"
  placeholder="Enter your question..."
  error={errors.query?.message}
  helperText="Press Enter to search"
/>
```

- Label above input (required)
- Error message below (red, icon + text)
- Helper text below (muted)
- Focus ring: `focus-visible-ring`
- Disabled: muted background, not cursor-not-allowed

### Tables

**Features**: sortable, selectable, sticky header, responsive (horizontal scroll < 768px)

```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead align="right">Score</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>Experiment A</TableCell>
      <TableCell align="right" className="font-mono">0.847</TableCell>
      <TableCell><Badge variant="success">Complete</Badge></TableCell>
    </TableRow>
  </TableBody>
</Table>
```

- Header: `heading-sm`, `font-medium`, `text-muted-foreground`
- Body: `body-md`, `text-foreground`
- Hover row: `bg-muted/50`
- Selected row: `bg-primary/10`, border-left `3px solid primary`
- Striped: `even:bg-muted/30`
- Numbers: `font-mono`, `tabular-nums`

### Cards

```tsx
<Card>
  <CardHeader>
    <CardTitle>Experiment Results</CardTitle>
    <CardDescription>Latest evaluation run</CardDescription>
  </CardHeader>
  <CardContent>
    <Table>...</Table>
  </CardContent>
  <CardFooter>
    <Button variant="ghost">View Details</Button>
  </CardFooter>
</Card>
```

- Border: `border-border`
- Shadow: `elevation-1`
- Hover: `elevation-2`
- Padding: `space-4` (md), `space-6` (lg)

### Dialogs / Modals

```tsx
<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild><Button>Open</Button></DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Confirm Delete</DialogTitle>
      <DialogDescription>This action cannot be undone.</DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button variant="ghost">Cancel</Button>
      <Button variant="destructive">Delete</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

- Backdrop: `bg-background/80 backdrop-blur-sm`
- Focus trap, escape to close, click backdrop to close
- Max width: `max-w-lg` (default), `max-w-2xl` (large), `max-w-4xl` (full)

### Drawers (Side Panels)

```tsx
<Drawer open={open} onOpenChange={setOpen} side="right" size="lg">
  <DrawerContent>
    <DrawerHeader>
      <DrawerTitle>Citation Evidence</DrawerTitle>
    </DrawerHeader>
    <DrawerBody>...</DrawerBody>
  </DrawerContent>
</Drawer>
```

- Sizes: `sm` (320px), `md` (480px), `lg` (640px), `xl` (800px), `full`
- Animation: slide-in from side
- Same focus trap as Dialog

### Badges

**Variants**: `default` | `secondary` | `success` | `warning` | `error` | `info` | `outline`

```tsx
<Badge variant="success">Completed</Badge>
<Badge variant="warning">Processing</Badge>
<Badge variant="error">Failed</Badge>
<Badge variant="info">Pending</Badge>
<Badge variant="outline">Draft</Badge>
```

- `default`: Primary background
- `outline`: Transparent, border, foreground text
- Size: `body-sm`, `font-medium`, `px-2 py-0.5`, `radius-full`

### Tabs

```tsx
<Tabs defaultValue="overview" onValueChange={setTab}>
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="documents">Documents</TabsTrigger>
    <TabsTrigger value="evaluations">Evaluations</TabsTrigger>
  </TabsList>
  <TabsContent value="overview">...</TabsContent>
  <TabsContent value="documents">...</TabsContent>
</Tabs>
```

- Indicator: animated, `bg-primary`, height 2px
- Trigger: `body-sm`, `font-medium`, `px-3 py-2`
- Keyboard: arrow keys, home/end

### Tooltips

```tsx
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild><Button variant="ghost"><InfoIcon /></Button></TooltipTrigger>
    <TooltipContent side="top" align="center">This metric measures...</TooltipContent>
  </Tooltip>
</TooltipProvider>
```

- Delay: 300ms show, 100ms hide
- Position: auto-flip, `elevation-3`
- Max width: 280px

### Skeletons

```tsx
<Skeleton className="h-4 w-3/4" />
<Skeleton className="h-12 w-full" />
<Skeleton className="h-48 w-full" variant="card" />
```

- Variants: `default` (pulse), `card` (shimmer wave)
- Colors: `bg-muted`, `animate-pulse` or `animate-shimmer`

### Empty States

```tsx
<EmptyState 
  icon={FileTextIcon}
  title="No documents yet"
  description="Upload your first document to get started"
  action={<Button>Upload Document</Button>}
/>
```

- Centered, generous vertical padding
- Icon: 64x64, `text-muted-foreground`
- Title: `heading-md`
- Description: `body-md`, `text-muted-foreground`

### Alerts

```tsx
<Alert variant="info" title="Indexing in progress">
  Your documents are being processed. This may take a few minutes.
</Alert>
<Alert variant="error" title="Upload failed" onDismiss={handleDismiss}>
  The file format is not supported. Please try PDF, TXT, or MD.
</Alert>
```

- Variants: `info` | `success` | `warning` | `error`
- Icon + title + description + optional dismiss
- No auto-dismiss for errors

## Navigation

### Sidebar (Main Navigation)

```tsx
<Sidebar>
  <SidebarHeader>
    <Logo />
  </SidebarHeader>
  <SidebarNav>
    <NavItem href="/dashboard" icon={LayoutDashboardIcon}>Dashboard</NavItem>
    <NavItem href="/documents" icon={FileTextIcon}>Documents</NavItem>
    <NavItem href="/chat" icon={MessageSquareIcon}>Chat</NavItem>
    <NavItem href="/evaluations" icon={BarChartIcon}>Evaluations</NavItem>
    <NavItem href="/experiments" icon={FlaskConicalIcon}>Experiments</NavItem>
    <NavItem href="/settings" icon={SettingsIcon}>Settings</NavItem>
  </SidebarNav>
  <SidebarFooter>
    <UserMenu />
  </SidebarFooter>
</Sidebar>
```

- Collapsible: icon-only (64px) / expanded (256px)
- Active: `bg-primary/10`, border-left `3px solid primary`
- Hover: `bg-muted/50`
- Keyboard: arrow keys, enter to activate

### Top Bar

```tsx
<TopBar>
  <TopBarLeft>
    <SidebarToggle />
    <Breadcrumbs />
  </TopBarLeft>
  <TopBarRight>
    <ThemeToggle />
    <Notifications />
    <UserAvatar />
  </TopBarRight>
</TopBar>
```

- Height: 56px (desktop), 48px (mobile)
- Sticky, `elevation-1`, `bg-background/95 backdrop-blur`

### Breadcrumbs

```tsx
<Breadcrumbs>
  <BreadcrumbItem href="/dashboard">Dashboard</BreadcrumbItem>
  <BreadcrumbItem href="/experiments">Experiments</BreadcrumbItem>
  <BreadcrumbItem current>exp_abc123</BreadcrumbItem>
</Breadcrumbs>
```

- Separator: `/` (muted)
- Current: `font-medium`, not clickable
- Max 3 visible, collapse with ellipsis

## Forms

### Field Layout

```tsx
<FormField 
  label="API Key"
  error={errors.apiKey?.message}
  helperText="Stored securely, never logged"
>
  <Input type="password" {...register('apiKey')} />
</FormField>
```

- Label: `body-sm`, `font-medium`, `mb-1.5`
- Required: asterisk `text-destructive`
- Error: `text-status-error`, `body-sm`, `flex items-center gap-1`
- Helper: `text-muted-foreground`, `body-sm`

### Validation

- Zod schemas for all forms
- Client-side validation on blur + submit
- Server errors mapped to fields
- Toast for non-field errors

## Responsive Breakpoints

| Breakpoint | Width | Usage |
|------------|-------|-------|
| `sm` | 640px | Mobile landscape |
| `md` | 768px | Tablet portrait |
| `lg` | 1024px | Tablet landscape / small desktop |
| `xl` | 1280px | Desktop |
| `2xl` | 1536px | Large desktop |

### Layout Behavior

- **Sidebar**: Collapsed on `< lg`, drawer on mobile
- **Tables**: Horizontal scroll on `< lg`, card layout on `< md`
- **Drawers**: Full screen on `< md`
- **Dialogs**: Full screen on `< sm`
- **Grid**: 1 col `< sm`, 2 col `< lg`, 3 col `< xl`, 4 col `≥ xl`

## Accessibility

### Focus Management

- All interactive elements: visible `focus-visible-ring`
- Focus trap in Dialogs, Drawers, Dropdowns
- Skip to main content link (first tab stop)
- Restore focus on close

### Keyboard Navigation

| Component | Keys |
|-----------|------|
| Buttons | Enter, Space |
| Links | Enter |
| Inputs | Tab, arrows (number), Enter (submit) |
| Select/Combobox | Arrow up/down, Enter, Escape, Type-ahead |
| Tabs | Arrow left/right, Home, End |
| Tables | Arrow keys (cell navigation), Enter (row action) |
| Dialogs/Drawers | Escape (close), Tab (trap) |
| Menus/Dropdowns | Arrow keys, Enter, Escape, Type-ahead |

### ARIA

- `role="button"` for non-button clickables
- `aria-label` for icon-only buttons
- `aria-describedby` for errors/helpers
- `aria-live="polite"` for toasts
- `aria-expanded`/`aria-controls` for disclosure
- `role="status"` for loading states

### Color Contrast

- All text: ≥ 4.5:1 (AA), ≥ 7:1 (AAA for body)
- UI components: ≥ 3:1
- Status colors meet contrast on both themes

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```

- Respects `prefers-reduced-motion`
- No auto-playing animations
- Transitions only on user interaction

### Screen Readers

- Semantic HTML: `<nav>`, `<main>`, `<aside>`, `<header>`, `<footer>`
- Headings: h1-h6 hierarchy, no skipping
- Landmarks: banner, navigation, main, contentinfo
- Tables: `<th scope="col">`, `<caption>`

## Dark Mode

- Class-based: `.dark` on `<html>`
- System preference default, user toggle persists
- No flash: inline script in `<head>` reads localStorage
- All colors work in both themes without overrides

## Icons

- **Library**: lucide-react (consistent, 24x24 default)
- **Sizes**: 16px (inline), 20px (buttons), 24px (nav), 32px (empty states)
- **Stroke**: 2px (default), 1.5px (small)
- **CurrentColor** for inheritance

## Implementation Notes

### CSS Variables

All design tokens exposed as CSS custom properties in `:root` and `.dark` for runtime theming.

### Utility Classes

```css
.focus-visible-ring  /* Visible focus */
.text-balance        /* text-wrap: balance */
.animate-in          /* Entrance animation */
```

### Component Architecture

- **shadcn/ui** patterns: Radix UI primitives + Tailwind
- **Composition over configuration**: Slot-based, render props
- **TypeScript**: Strict, discriminated unions for variants
- **No external CSS**: All styles in Tailwind/globals.css

## File Structure

```
apps/web/
├── components/
│   ├── ui/                 # Base components (Button, Input, Table, etc.)
│   ├── layout/             # Sidebar, TopBar, Breadcrumbs, PageLayout
│   ├── navigation/         # NavItem, UserMenu, ThemeToggle
│   ├── feedback/           # Alert, Toast, Skeleton, EmptyState
│   └── data-display/       # Badge, Avatar, Progress, StatCard
├── lib/
│   ├── utils.ts            # clsx, cn, formatters
│   ├── constants.ts        # Routes, enums, config
│   └── validators.ts       # Zod schemas
├── hooks/
│   ├── useTheme.ts         # Theme context
│   ├── useSidebar.ts       # Sidebar state
│   └── useMediaQuery.ts    # Responsive hooks
├── app/
│   ├── layout.tsx          # Root layout, providers
│   ├── globals.css         # Design tokens
│   ├── (dashboard)/        # Route groups
│   ├── (auth)/             # Auth routes
│   └── api/                # API routes (if needed)
└── types/
    └── index.ts            # Shared types
```

## Quality Checklist

- [ ] All tokens defined in CSS variables
- [ ] Components work in both themes
- [ ] Focus visible on all interactives
- [ ] Keyboard accessible
- [ ] Screen reader tested
- [ ] Reduced motion respected
- [ ] Responsive at all breakpoints
- [ ] No hardcoded colors in components
- [ ] TypeScript strict mode passes
- [ ] ESLint + Prettier clean