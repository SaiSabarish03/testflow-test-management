const { chromium } = require('@playwright/test');

async function runValidation() {
  console.log('Starting end-to-end browser validation...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  const consoleMsgs = [];
  const pageErrors = [];

  page.on('console', msg => {
    const text = msg.text();
    consoleMsgs.push({ type: msg.type(), text });
    if (msg.type() === 'error' || msg.type() === 'warning') {
      console.log(`[BROWSER CONSOLE ${msg.type().toUpperCase()}]: ${text}`);
    }
  });

  page.on('pageerror', err => {
    pageErrors.push(err.message);
    console.log(`[BROWSER PAGE ERROR]: ${err.message}`);
  });

  page.on('response', response => {
    const status = response.status();
    const url = response.url();
    if (status >= 400) {
      console.log(`[API ERROR] ${url} returned status ${status}`);
      response.text().then(text => {
        console.log(`[API ERROR DETAIL] ${text}`);
      }).catch(() => {});
    }
  });

  try {
    // 1. Login
    console.log('1. Navigating to login page...');
    await page.goto('http://localhost:5173/login');
    await page.waitForLoadState('networkidle');

    console.log('Logging in as QA Engineer...');
    await page.fill('input[aria-label="Email"]', 'qa@testflow.local');
    await page.fill('input[aria-label="Password"]', 'QaPass123!');
    await page.click('button[type="submit"]');

    console.log('Waiting for Dashboard...');
    await page.waitForURL('**/dashboard');
    console.log('Logged in successfully!');

    // 2. Open project
    console.log('2. Navigating to projects page...');
    await page.goto('http://localhost:5173/projects');
    await page.waitForLoadState('networkidle');
    
    console.log('Opening project details...');
    await page.click('text="TestFlow Web"');
    await page.waitForURL('**/projects/1*');
    console.log('Opened project details page.');

    // 3. Open Test Runs tab
    console.log('3. Switching to Test Runs tab...');
    await page.click('div[role="tab"]:has-text("Test Runs")');
    console.log('Switched to Test Runs tab.');

    // 4. Create a run
    console.log('4. Clicking New Run...');
    const newRunBtn = page.getByRole('button', { name: 'Create Test Run' });
    await expectToBeVisible(newRunBtn, 'Create Test Run button');
    await newRunBtn.click();

    await page.waitForURL('**/projects/1/runs/new');
    console.log('Opened Create Test Run page.');

    // 5. Fill details & Verify READY test cases
    console.log('5. Filling run metadata...');
    await page.fill('input[aria-label="Run name"]', 'E2E Automation Validation Run');
    await page.fill('input[aria-label="Environment"]', 'Staging');

    console.log('Waiting for test case selection table to load...');
    await page.locator('.ant-table-row').first().waitFor({ state: 'visible', timeout: 5000 });

    console.log('Checking test case selection list...');
    // Verify that all test cases listed have status READY
    const statusTags = page.locator('span.ant-tag:has-text("Ready")');
    const statusCount = await statusTags.count();
    console.log(`Found ${statusCount} READY test cases in the selection list.`);
    
    const draftTags = page.locator('span.ant-tag:has-text("Draft")');
    const draftCount = await draftTags.count();
    const deprecatedTags = page.locator('span.ant-tag:has-text("Deprecated")');
    const deprecatedCount = await deprecatedTags.count();
    console.log(`Draft count: ${draftCount}, Deprecated count: ${deprecatedCount}`);
    if (draftCount > 0 || deprecatedCount > 0) {
      throw new Error('DRAFT or DEPRECATED test cases were visible in the select run page!');
    }

    // 6. Select test cases & Create run
    console.log('6. Selecting first test case and creating run...');
    // Click the checkbox for the first test case in the table
    const checkboxes = page.locator('.ant-table-cell input[type="checkbox"]');
    await checkboxes.nth(1).click(); // nth(0) is the select-all header checkbox, nth(1) is the first row's checkbox
    
    const createBtn = page.getByRole('button', { name: 'Create Test Run' });
    console.log('Clicking Create Run button...');
    await createBtn.click();

    // 7. Verify navigation and breadcrumbs
    console.log('7. Verifying navigation to Run Detail page...');
    await page.waitForURL('**/runs/*');
    console.log('Successfully navigated to Run Detail page!');

    // Wait for data load
    await page.waitForLoadState('networkidle');

    console.log('Verifying Breadcrumbs...');
    const projectBreadcrumb = page.locator('a:has-text("TestFlow Web")');
    await expectToBeVisible(projectBreadcrumb, 'Project detail breadcrumb');
    const runsBreadcrumb = page.locator('a:has-text("Test Runs")');
    await expectToBeVisible(runsBreadcrumb, 'Test Runs tab breadcrumb');

    // 8. Start Run
    console.log('8. Starting the test run...');
    const startRunBtn = page.getByRole('button', { name: 'Start Run' });
    await expectToBeVisible(startRunBtn, 'Start Run button');
    await startRunBtn.click();
    console.log('Clicked Start Run.');

    // Wait for the button state to update
    await page.waitForTimeout(1000);
    const inProgressTag = page.locator('.ant-tag:has-text("In Progress")');
    await expectToBeVisible(inProgressTag, 'In Progress status tag');

    // 9. Attempt Complete with NOT_RUN results and verify rejection
    console.log('9. Attempting to Complete Run while results are NOT_RUN...');
    const completeRunBtn = page.getByRole('button', { name: 'Complete Run' });
    // The Complete Run button should be disabled when notRunCount > 0
    const isDisabled = await completeRunBtn.isDisabled();
    console.log(`Complete Run button is disabled: ${isDisabled}`);
    if (!isDisabled) {
      throw new Error('Complete Run button should be disabled when there are NOT_RUN test cases.');
    }

    const alertMsg = page.locator('.ant-alert-message');
    const alertText = await alertMsg.textContent();
    console.log(`Alert message shown: "${alertText}"`);
    if (!alertText || !alertText.includes('result(s) still NOT_RUN')) {
      throw new Error('Expected alert explaining results are still NOT_RUN was missing!');
    }

    // 10. Record results (PASS/FAIL/BLOCKED)
    console.log('10. Recording results...');
    const resultRows = page.locator('.ant-table-row');
    const rowCount = await resultRows.count();
    console.log(`Total results to record: ${rowCount}`);

    for (let i = 0; i < rowCount; i++) {
      console.log(`Recording result for row ${i + 1}...`);
      const row = resultRows.nth(i);
      
      // Fill actual result
      const input = row.locator('input[placeholder="Actual result (optional)"]');
      if (await input.isVisible()) {
        await input.fill(`E2E verified step ${i + 1}`);
      }

      // Click Pass button inside the row
      const passBtn = row.getByRole('button', { name: 'Pass' });
      await passBtn.click();
      await page.waitForTimeout(1000); // Wait for API refresh
    }

    console.log('All results recorded.');

    // 11. Verify Summary stats after execution
    console.log('11. Verifying run summary statistics...');
    const totalStat = page.locator('.ant-statistic-title:has-text("Total") + .ant-statistic-content');
    const passedStat = page.locator('.ant-statistic-title:has-text("Passed") + .ant-statistic-content');
    const notRunStat = page.locator('.ant-statistic-title:has-text("Not Run") + .ant-statistic-content');
    
    console.log(`Summary - Total: ${await totalStat.textContent()}, Passed: ${await passedStat.textContent()}, Not Run: ${await notRunStat.textContent()}`);

    // Verify Executor & Timestamp
    console.log('Verifying Executor and Execution Timestamp column details...');
    const firstRowExecutor = await resultRows.first().locator('td').nth(3).textContent();
    const firstRowTimestamp = await resultRows.first().locator('td').nth(4).textContent();
    console.log(`Executor displays: "${firstRowExecutor}"`);
    console.log(`Timestamp displays: "${firstRowTimestamp}"`);
    if (!firstRowExecutor || !firstRowExecutor.includes('QA Engineer')) {
      throw new Error(`Invalid executor display: "${firstRowExecutor}"`);
    }
    if (!firstRowTimestamp || firstRowTimestamp === '—') {
      throw new Error('Missing execution timestamp.');
    }

    // 12. Complete the run
    console.log('12. Completing the run...');
    await expectToBeVisible(completeRunBtn, 'Complete Run button');
    await completeRunBtn.click();
    await page.waitForTimeout(1500);

    const completedTag = page.locator('.ant-tag:has-text("Completed")');
    await expectToBeVisible(completedTag, 'Completed status tag');
    console.log('Run completed successfully!');

    // 13. Confirm no state action buttons remain
    console.log('13. Checking that no transition buttons remain...');
    const startCount = await page.getByRole('button', { name: 'Start Run' }).count();
    const completeCount = await page.getByRole('button', { name: 'Complete Run' }).count();
    const abortCount = await page.getByRole('button', { name: 'Abort Run' }).count();
    console.log(`Transition buttons count after complete -> Start: ${startCount}, Complete: ${completeCount}, Abort: ${abortCount}`);
    if (startCount > 0 || completeCount > 0 || abortCount > 0) {
      throw new Error('State action buttons should be hidden for COMPLETED runs.');
    }

    // 14. Separate validation: Test Abort Run flow
    console.log('14. Testing Abort Run flow separately...');
    await page.goto('http://localhost:5173/projects/1');
    await page.waitForLoadState('networkidle');
    await page.click('div[role="tab"]:has-text("Test Runs")');
    
    await page.getByRole('button', { name: 'Create Test Run' }).click();
    await page.waitForURL('**/projects/1/runs/new');
    
    await page.fill('input[aria-label="Run name"]', 'E2E Abort Run Test');
    await page.fill('input[aria-label="Environment"]', 'Dev');
    
    await page.locator('.ant-table-row').first().waitFor({ state: 'visible', timeout: 5000 });
    await page.locator('.ant-table-cell input[type="checkbox"]').nth(1).click();
    
    await page.getByRole('button', { name: 'Create Test Run' }).click();
    await page.waitForURL('**/runs/*');
    
    // Start run
    await page.getByRole('button', { name: 'Start Run' }).click();
    await page.waitForTimeout(1000);
    
    // Abort run
    console.log('Clicking Abort Run button...');
    await page.getByRole('button', { name: 'Abort Run' }).click();
    
    // Click confirmation popconfirm "Abort" button
    const popconfirmAbortBtn = page.locator('.ant-popover-buttons button:has-text("Abort")');
    await popconfirmAbortBtn.click();
    await page.waitForTimeout(1500);

    const abortedTag = page.locator('.ant-tag:has-text("Aborted")');
    await expectToBeVisible(abortedTag, 'Aborted status tag');
    console.log('Run aborted successfully!');

    // Verify transition buttons are hidden for Abort
    const startCountAbort = await page.getByRole('button', { name: 'Start Run' }).count();
    const completeCountAbort = await page.getByRole('button', { name: 'Complete Run' }).count();
    const abortCountAbort = await page.getByRole('button', { name: 'Abort Run' }).count();
    console.log(`Transition buttons count after abort -> Start: ${startCountAbort}, Complete: ${completeCountAbort}, Abort: ${abortCountAbort}`);
    if (startCountAbort > 0 || completeCountAbort > 0 || abortCountAbort > 0) {
      throw new Error('State action buttons should be hidden for ABORTED runs.');
    }

    console.log('All end-to-end flows validated successfully!');
  } catch (error) {
    console.error('Validation failed with error:', error);
    process.exitCode = 1;
  } finally {
    await browser.close();
    
    console.log('\n--- BROWSER CONSOLE LOG SUMMARY ---');
    console.log(`Total messages collected: ${consoleMsgs.length}`);
    const warnings = consoleMsgs.filter(m => m.type === 'warning');
    const errors = consoleMsgs.filter(m => m.type === 'error');
    console.log(`Warnings count: ${warnings.length}`);
    console.log(`Errors count: ${errors.length}`);
    
    if (errors.length > 0) {
      console.log('Error logs details:');
      errors.forEach((e, idx) => console.log(`  ${idx+1}: ${e.text}`));
    }
    
    if (pageErrors.length > 0) {
      console.log('Unhandled Page Errors:');
      pageErrors.forEach((e, idx) => console.log(`  ${idx+1}: ${e}`));
    }
  }
}

async function expectToBeVisible(locator, name) {
  try {
    await locator.waitFor({ state: 'visible', timeout: 5000 });
  } catch (error) {
    throw new Error(`Expected element "${name}" to be visible, but it was not found within 5s.`);
  }
}

runValidation();
