# Gift Card Wallet Development Guide

## Build & Test Commands
- Backend: `cd backend && python -m uvicorn app.main:app --reload`
- Frontend: `cd frontend/wallet_frontend && npm run start`
- Android: `cd frontend/wallet_frontend && npm run android`
- iOS: `cd frontend/wallet_frontend && npm run ios`
- Tests: `cd frontend/wallet_frontend && npm run test`
- Lint: `cd frontend/wallet_frontend && npm run lint`
- Single test: `cd frontend/wallet_frontend && npm test -- -t "test_name"`

## Code Style Guidelines
### Backend (Python)
- **Imports**: Group by stdlib → third-party → local; use specific imports
- **Formatting**: 4-space indentation; snake_case for variables/functions; PascalCase for classes
- **Types**: Use type hints; Pydantic models for validation
- **Error handling**: Structured try/except; detailed logging with context

### Frontend (TypeScript)
- **Imports**: React first, libraries next, local last; use named imports
- **Formatting**: 2-space indentation; semicolons required
- **Types**: Define interfaces for props; explicit typing for functions and variables
- **Components**: Functional with React.FC; props interfaces at top; styles at bottom
- **Naming**: PascalCase for components/types; camelCase for variables/functions
- **Theming**: Use centralized theme constants; avoid hardcoded values