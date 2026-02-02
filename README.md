# Firm Offer Copilot

AI-powered generator for maritime firm offers.
Specializes in Ukrainian grain exports to Mediterranean markets.

## Quick Start

### 1. Install Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Run Claude Code
```bash
cd C:\Projects\FrtOffersCopilot
claude
```

### 3. Give Task
```
> Read TASK.md and start building the MVP
```

## Project Structure

```
FrtOffersCopilot/
├── TASK.md              # Main task for Claude Code
├── README.md            # This file
├── docs/                # Documentation
│   ├── MASTER_LIBRARY.md
│   ├── CARGO_DATABASE.md
│   └── SYSTEM_ARCHITECTURE.md
├── examples/            # Example firm offers (add yours here)
├── backend/             # Python FastAPI (will be created)
└── frontend/            # React app (will be created)
```

## What Claude Code Will Build

1. **Backend (Python FastAPI)**
   - Clause selection logic
   - Firm offer text generation
   - API endpoint

2. **Frontend (React)**
   - Form for parameters
   - Output display
   - Copy to clipboard

## MVP Features

- Select load/discharge ports
- Select cargo type
- Enter quantity, freight, laycan
- Generate firm offer with correct clauses
- Copy result

## Adding Examples

Put your real firm offers in `/examples/` folder.
This helps Claude Code understand the exact format you need.

## Next Steps After MVP

1. PDF generation
2. Charterer database
3. Telegram bot
4. Counter workflow
