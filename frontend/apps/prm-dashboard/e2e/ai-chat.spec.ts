import { test, expect } from '@playwright/test';

test.describe('AI Chat Interface', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display AI chat panel', async ({ page }) => {
    // AI chat panel should be visible on all pages
    await expect(page.locator('[data-testid="ai-chat-panel"]')).toBeVisible();

    // Should have input field
    await expect(page.getByPlaceholder(/ask ai|type a message/i)).toBeVisible();

    // Should have send button
    await expect(page.getByRole('button', { name: /send/i })).toBeVisible();
  });

  test('should accept text input', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask ai|type a message/i);

    // Type a message
    await chatInput.fill('Show me today\'s appointments');

    // Verify input has the text
    await expect(chatInput).toHaveValue('Show me today\'s appointments');
  });

  test('should send message on button click', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask ai|type a message/i);
    const sendButton = page.getByRole('button', { name: /send/i });

    // Type and send message
    await chatInput.fill('Hello AI');
    await sendButton.click();

    // Input should be cleared after sending
    await expect(chatInput).toHaveValue('');

    // Message should appear in chat history
    await expect(page.getByText('Hello AI')).toBeVisible();
  });

  test('should send message on Enter key', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask ai|type a message/i);

    // Type message and press Enter
    await chatInput.fill('Test message');
    await chatInput.press('Enter');

    // Input should be cleared
    await expect(chatInput).toHaveValue('');

    // Message should appear
    await expect(page.getByText('Test message')).toBeVisible();
  });

  test('should show loading state while processing', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask ai|type a message/i);

    // Send a message
    await chatInput.fill('Book an appointment');
    await chatInput.press('Enter');

    // Should show loading indicator
    const loadingIndicator = page.locator('[data-testid="ai-loading"]');
    await expect(loadingIndicator).toBeVisible();
  });

  test('should display AI response', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask ai|type a message/i);

    // Send a message
    await chatInput.fill('What can you help me with?');
    await chatInput.press('Enter');

    // Wait for AI response (with timeout)
    await page.waitForSelector('[data-testid="ai-message"]', { timeout: 10000 });

    // Response should be visible
    const aiResponse = page.locator('[data-testid="ai-message"]').last();
    await expect(aiResponse).toBeVisible();
  });

  test('should show suggested actions', async ({ page }) => {
    // Suggested actions/quick actions should be visible
    const suggestedActions = page.locator('[data-testid="suggested-action"]');

    if (await suggestedActions.count() > 0) {
      await expect(suggestedActions.first()).toBeVisible();

      // Click on a suggestion should populate input
      await suggestedActions.first().click();
      const chatInput = page.getByPlaceholder(/ask ai|type a message/i);
      await expect(chatInput).not.toHaveValue('');
    }
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Simulate error by disconnecting network
    await page.context().setOffline(true);

    const chatInput = page.getByPlaceholder(/ask ai|type a message/i);
    await chatInput.fill('Test during offline');
    await chatInput.press('Enter');

    // Should show error message
    await expect(page.getByText(/error|failed|try again/i)).toBeVisible();

    // Reconnect
    await page.context().setOffline(false);
  });

  test('should display conversation history', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask ai|type a message/i);

    // Send multiple messages
    await chatInput.fill('First message');
    await chatInput.press('Enter');
    await page.waitForTimeout(500);

    await chatInput.fill('Second message');
    await chatInput.press('Enter');
    await page.waitForTimeout(500);

    // Both messages should be in history
    await expect(page.getByText('First message')).toBeVisible();
    await expect(page.getByText('Second message')).toBeVisible();
  });

  test('should clear chat history', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask ai|type a message/i);

    // Send a message
    await chatInput.fill('Test message');
    await chatInput.press('Enter');
    await page.waitForTimeout(500);

    // Find and click clear button
    const clearButton = page.getByRole('button', { name: /clear|reset/i });
    if (await clearButton.isVisible()) {
      await clearButton.click();

      // Confirm clear action if dialog appears
      const confirmButton = page.getByRole('button', { name: /confirm|yes/i });
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
      }

      // Chat should be empty
      await expect(page.getByText('Test message')).not.toBeVisible();
    }
  });
});

test.describe('Command Bar (Cmd+K)', () => {
  test('should open command bar with keyboard shortcut', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Press Cmd+K (or Ctrl+K on Windows/Linux)
    await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');

    // Command bar should open
    await expect(page.locator('[data-testid="command-bar"]')).toBeVisible();
  });

  test('should search and execute commands', async ({ page }) => {
    await page.goto('/');

    // Open command bar
    await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');

    // Type search query
    await page.getByPlaceholder(/search|type a command/i).fill('appointments');

    // Wait for results
    await page.waitForTimeout(300);

    // Results should be visible
    const results = page.locator('[data-testid="command-result"]');
    await expect(results.first()).toBeVisible();
  });

  test('should close command bar on Escape', async ({ page }) => {
    await page.goto('/');

    // Open command bar
    await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');
    await expect(page.locator('[data-testid="command-bar"]')).toBeVisible();

    // Press Escape
    await page.keyboard.press('Escape');

    // Command bar should close
    await expect(page.locator('[data-testid="command-bar"]')).not.toBeVisible();
  });
});
