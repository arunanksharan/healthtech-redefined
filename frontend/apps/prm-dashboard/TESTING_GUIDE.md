# Testing & Quality Assurance Guide

Complete testing infrastructure and best practices for the PRM Dashboard.

## Table of Contents

- [Testing Strategy](#testing-strategy)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Running Tests](#running-tests)
- [Coverage Reports](#coverage-reports)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)

## Testing Strategy

The PRM Dashboard uses a comprehensive multi-layer testing approach:

1. **Unit Tests**: Test individual components and functions in isolation
2. **Integration Tests**: Test API clients and data flow
3. **End-to-End Tests**: Test complete user workflows
4. **Visual Regression**: Test UI consistency (future)
5. **Performance Tests**: Test load times and bundle size

### Coverage Goals

- **Overall**: 70% minimum
- **Critical Paths**: 90%+ (AI agents, API clients, auth)
- **UI Components**: 60%+
- **Utility Functions**: 80%+

## Unit Testing

### Setup

We use **Jest** and **React Testing Library** for unit tests.

**Configuration**: `jest.config.js`
**Setup**: `jest.setup.js`

### Running Unit Tests

```bash
# Run all unit tests
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- AppointmentAgent.test.ts
```

### Example: Testing AI Agents

**File**: `lib/ai/agents/__tests__/AppointmentAgent.test.ts`

```typescript
describe('AppointmentAgent', () => {
  it('should identify booking intent', () => {
    const agent = new AppointmentAgent();
    expect(agent.canHandle('book appointment')).toBe(true);
  });

  it('should have correct capabilities', () => {
    const agent = new AppointmentAgent();
    const caps = agent.getCapabilities();
    expect(caps.name).toBe('AppointmentAgent');
    expect(caps.capabilities.length).toBeGreaterThan(0);
  });
});
```

### Example: Testing API Clients

**File**: `lib/api/__tests__/appointments.test.ts`

```typescript
describe('Appointments API', () => {
  it('should fetch all appointments', async () => {
    const mockData = { data: [...], total: 10 };
    (apiClient.get as jest.Mock).mockResolvedValue({ data: mockData });

    const [data, error] = await appointmentsAPI.getAll();

    expect(data).toEqual(mockData);
    expect(error).toBeNull();
  });

  it('should handle errors', async () => {
    (apiClient.get as jest.Mock).mockRejectedValue(new Error('Network error'));

    const [data, error] = await appointmentsAPI.getAll();

    expect(data).toBeNull();
    expect(error).toBeTruthy();
  });
});
```

### Writing New Unit Tests

1. Create `__tests__` folder next to the file you're testing
2. Name test files: `ComponentName.test.ts` or `functionName.test.ts`
3. Use descriptive test names
4. Follow Arrange-Act-Assert pattern
5. Mock external dependencies

## Integration Testing

Integration tests verify that multiple components work together correctly.

### API Client Testing

Test the complete flow: API client → network → response handling

```typescript
describe('Patient API Integration', () => {
  it('should create and retrieve patient', async () => {
    // Create patient
    const [created, createError] = await patientsAPI.create({
      name: 'Test Patient',
      date_of_birth: '1990-01-01',
      gender: 'male',
    });

    expect(createError).toBeNull();
    expect(created).toHaveProperty('id');

    // Retrieve patient
    const [retrieved, getError] = await patientsAPI.getById(created!.id);

    expect(getError).toBeNull();
    expect(retrieved).toEqual(created);
  });
});
```

## End-to-End Testing

### Setup

We use **Playwright** for E2E tests.

**Configuration**: `playwright.config.ts`
**Tests**: `e2e/` directory

### Running E2E Tests

```bash
# Install Playwright browsers (first time)
npx playwright install

# Run all E2E tests
npm run test:e2e

# Run in headed mode (see browser)
npm run test:e2e -- --headed

# Run specific test file
npm run test:e2e -- appointments.spec.ts

# Debug mode
npm run test:e2e -- --debug

# Run on specific browser
npm run test:e2e -- --project=chromium
```

### Example: Appointments E2E Test

**File**: `e2e/appointments.spec.ts`

```typescript
test('should display appointments calendar', async ({ page }) => {
  await page.goto('/appointments');
  await page.waitForLoadState('networkidle');

  await expect(page.getByRole('heading', { name: /appointments/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /week/i })).toBeVisible();
});

test('should book new appointment', async ({ page }) => {
  await page.goto('/appointments');

  // Click "New Appointment"
  await page.getByRole('button', { name: /new appointment/i }).click();

  // Fill form
  await page.getByLabel('Patient').fill('John Doe');
  await page.getByLabel('Date').fill('2024-12-01');
  await page.getByLabel('Time').fill('10:00');

  // Submit
  await page.getByRole('button', { name: /book/i }).click();

  // Verify success
  await expect(page.getByText(/appointment booked/i)).toBeVisible();
});
```

### Example: AI Chat E2E Test

**File**: `e2e/ai-chat.spec.ts`

```typescript
test('should send message and receive response', async ({ page }) => {
  await page.goto('/');

  const chatInput = page.getByPlaceholder(/ask ai/i);
  await chatInput.fill('Show me appointments');
  await chatInput.press('Enter');

  // Wait for response
  await page.waitForSelector('[data-testid="ai-message"]', { timeout: 10000 });

  const response = page.locator('[data-testid="ai-message"]').last();
  await expect(response).toBeVisible();
});
```

### Writing New E2E Tests

1. Create test files in `e2e/` directory
2. Use descriptive test names
3. Wait for network idle before assertions
4. Use data-testid attributes for reliable selectors
5. Test happy paths AND error cases

## Error Handling

### Error Boundaries

We use React Error Boundaries to catch and display errors gracefully.

**Global Error Boundary**: `app/layout.tsx`
**Section Error Boundary**: `components/error-boundary.tsx`

```typescript
import { ErrorBoundary } from '@/components/error-boundary';

function MyPage() {
  return (
    <ErrorBoundary>
      <MyComponent />
    </ErrorBoundary>
  );
}
```

### Form Validation

All forms use Zod schemas for validation.

**Schemas**: `lib/validation/schemas.ts`
**Hook**: `lib/hooks/useFormValidation.ts`

```typescript
import { useFormValidation } from '@/lib/hooks/useFormValidation';
import { createAppointmentSchema } from '@/lib/validation/schemas';

function AppointmentForm() {
  const { errors, handleSubmit } = useFormValidation({
    schema: createAppointmentSchema,
    onSubmit: async (data) => {
      // Submit data
    },
  });

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      {errors.patient_id && <span>{errors.patient_id}</span>}
    </form>
  );
}
```

## Loading States

Use skeleton components for better UX during data loading.

**Components**: `components/ui/skeleton.tsx`

```typescript
import { DashboardSkeleton, ListSkeleton } from '@/components/ui/skeleton';

function MyPage() {
  const { data, isLoading } = useQuery(...);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return <div>{/* Actual content */}</div>;
}
```

## Coverage Reports

### Generating Coverage Reports

```bash
# Generate coverage report
npm test -- --coverage

# Open coverage report in browser
open coverage/lcov-report/index.html
```

### Coverage Metrics

- **Statements**: Lines of code executed
- **Branches**: If/else paths taken
- **Functions**: Functions called
- **Lines**: Individual lines executed

### Improving Coverage

1. Identify uncovered files in report
2. Write tests for critical paths first
3. Focus on business logic
4. Don't aim for 100% - aim for quality

## Best Practices

### Unit Tests

✅ **DO**:
- Test one thing per test
- Use descriptive test names
- Mock external dependencies
- Test edge cases
- Keep tests fast

❌ **DON'T**:
- Test implementation details
- Create brittle tests
- Share state between tests
- Test third-party code

### Integration Tests

✅ **DO**:
- Test realistic scenarios
- Use actual API responses (mocked)
- Test error handling
- Verify data flow

❌ **DON'T**:
- Make actual API calls
- Depend on external services
- Skip error cases

### E2E Tests

✅ **DO**:
- Test critical user flows
- Use data-testid for selectors
- Wait for elements properly
- Test on multiple browsers
- Screenshot on failure

❌ **DON'T**:
- Test every possible scenario
- Use CSS selectors (they change)
- Make tests too slow
- Ignore flaky tests

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm test -- --coverage

      - name: Run E2E tests
        run: npx playwright install --with-deps && npm run test:e2e

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
```

### Pre-commit Hooks

Use Husky to run tests before commits:

```bash
# Install husky
npm install --save-dev husky

# Create pre-commit hook
npx husky add .husky/pre-commit "npm test -- --findRelatedTests"
```

## Test Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:debug": "playwright test --debug",
    "test:all": "npm test && npm run test:e2e"
  }
}
```

## Debugging Tests

### Jest Debugging

```bash
# Use node debugger
node --inspect-brk node_modules/.bin/jest --runInBand

# Or use VS Code launch configuration
```

**VS Code `launch.json`**:

```json
{
  "type": "node",
  "request": "launch",
  "name": "Jest Debug",
  "program": "${workspaceFolder}/node_modules/.bin/jest",
  "args": ["--runInBand"],
  "console": "integratedTerminal",
  "internalConsoleOptions": "neverOpen"
}
```

### Playwright Debugging

```bash
# Debug mode - step through tests
npm run test:e2e -- --debug

# UI mode - interactive test runner
npm run test:e2e -- --ui

# Headed mode - see browser
npm run test:e2e -- --headed
```

## Performance Testing

### Bundle Size Analysis

```bash
# Analyze bundle size
ANALYZE=true npm run build
```

Add to `package.json`:

```json
{
  "scripts": {
    "analyze": "ANALYZE=true next build"
  }
}
```

### Lighthouse CI

```bash
# Run Lighthouse
npx lighthouse http://localhost:3000 --view

# CI integration
npm install --save-dev @lhci/cli
```

## Accessibility Testing

### Axe Core

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('should have no accessibility violations', async () => {
  const { container } = render(<MyComponent />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## Continuous Improvement

1. **Review Coverage Weekly**: Identify gaps
2. **Add Tests for Bugs**: Write test first, then fix
3. **Refactor Tests**: Keep them maintainable
4. **Update Test Data**: Keep realistic
5. **Monitor Flaky Tests**: Fix or remove

---

**Questions or Issues?**
- Review test examples in `__tests__` directories
- Check Playwright documentation: https://playwright.dev
- Check Jest documentation: https://jestjs.io
