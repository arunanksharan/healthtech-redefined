import { test, expect } from '@playwright/test';

test.describe('Appointments Management', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to appointments page
    await page.goto('/appointments');
  });

  test('should display appointments calendar', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check if calendar header is visible
    await expect(page.getByRole('heading', { name: /appointments/i })).toBeVisible();

    // Check if view mode toggles are present
    await expect(page.getByRole('button', { name: /day/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /week/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /month/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /list/i })).toBeVisible();
  });

  test('should switch between calendar views', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Click on Week view
    await page.getByRole('button', { name: /week/i }).click();
    await expect(page.getByRole('button', { name: /week/i })).toHaveClass(/default/);

    // Click on Month view
    await page.getByRole('button', { name: /month/i }).click();
    await expect(page.getByRole('button', { name: /month/i })).toHaveClass(/default/);

    // Click on List view
    await page.getByRole('button', { name: /list/i }).click();
    await expect(page.getByRole('button', { name: /list/i })).toHaveClass(/default/);
  });

  test('should navigate to next/previous periods', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Get initial date
    const initialDate = await page.locator('[data-testid="current-date"]').textContent();

    // Click next button
    await page.getByRole('button', { name: /next/i }).click();
    const nextDate = await page.locator('[data-testid="current-date"]').textContent();
    expect(nextDate).not.toBe(initialDate);

    // Click previous button
    await page.getByRole('button', { name: /previous/i }).click();
    const prevDate = await page.locator('[data-testid="current-date"]').textContent();
    expect(prevDate).toBe(initialDate);
  });

  test('should filter appointments by status', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Click on status filter
    await page.locator('select[name="status"]').selectOption('confirmed');

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Verify URL updated with filter
    expect(page.url()).toContain('confirmed');
  });

  test('should search appointments', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Type in search box
    await page.getByPlaceholder(/search/i).fill('John Doe');

    // Wait for search to apply
    await page.waitForTimeout(500);

    // Results should update (implementation specific)
    const appointmentCards = page.locator('[data-testid="appointment-card"]');
    await expect(appointmentCards.first()).toBeVisible();
  });

  test('should show appointment details on click', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Switch to list view for easier testing
    await page.getByRole('button', { name: /list/i }).click();

    // Click on first appointment
    const firstAppointment = page.locator('[data-testid="appointment-card"]').first();
    if (await firstAppointment.isVisible()) {
      await firstAppointment.click();

      // Verify details are shown (modal or expanded view)
      await expect(page.locator('[data-testid="appointment-details"]')).toBeVisible();
    }
  });
});

test.describe('Appointment Actions', () => {
  test('should open new appointment dialog', async ({ page }) => {
    await page.goto('/appointments');
    await page.waitForLoadState('networkidle');

    // Click "New Appointment" button
    await page.getByRole('button', { name: /new appointment/i }).click();

    // Dialog should open
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('heading', { name: /new appointment/i })).toBeVisible();
  });

  test('should validate appointment form', async ({ page }) => {
    await page.goto('/appointments');
    await page.waitForLoadState('networkidle');

    // Open new appointment dialog
    await page.getByRole('button', { name: /new appointment/i }).click();

    // Try to submit without filling required fields
    await page.getByRole('button', { name: /book|create/i }).click();

    // Error messages should appear
    await expect(page.getByText(/required/i).first()).toBeVisible();
  });
});
