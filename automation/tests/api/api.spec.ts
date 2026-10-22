import { test, expect, type APIRequestContext } from '@playwright/test';

const ADMIN_EMAIL = process.env.TEST_ADMIN_EMAIL || 'admin@testflow.local';
const ADMIN_PASSWORD = process.env.TEST_ADMIN_PASSWORD || 'Admin123!';
const QA_EMAIL = process.env.TEST_QA_EMAIL || 'qa@testflow.local';
const QA_PASSWORD = process.env.TEST_QA_PASSWORD || 'QaPass123!';
const VIEWER_EMAIL = process.env.TEST_VIEWER_EMAIL || 'viewer@testflow.local';
const VIEWER_PASSWORD = process.env.TEST_VIEWER_PASSWORD || 'View123!';

type LoginResult = {
  access_token: string;
  token_type: string;
  user: { id: number; email: string; role: string };
};

async function login(
  request: APIRequestContext,
  email: string,
  password: string,
): Promise<LoginResult> {
  const response = await request.post('/api/auth/login', {
    data: { email, password },
  });
  expect(response.status(), 'login should succeed').toBe(200);
  const body = (await response.json()) as LoginResult;
  expect(body.access_token).toBeTruthy();
  expect(body.token_type.toLowerCase()).toBe('bearer');
  return body;
}

function bearer(token: string) {
  return { Authorization: `Bearer ${token}` };
}

function uniqueSuffix() {
  return `${Date.now()}${Math.floor(Math.random() * 10000)}`.slice(-12);
}

test.describe('API — authentication, projects and test-case workflow', () => {
  test('rejects invalid login credentials with 401', async ({ request }) => {
    const response = await request.post('/api/auth/login', {
      data: { email: ADMIN_EMAIL, password: 'invalid-password-for-test' },
    });

    expect(response.status()).toBe(401);
    expect(response.headers()['www-authenticate']).toBe('Bearer');
    expect((await response.json()).detail).toBeTruthy();
  });

  test('protects current-user endpoint without a bearer token', async ({ request }) => {
    const response = await request.get('/api/auth/me');

    expect(response.status()).toBe(401);
    expect(response.headers()['www-authenticate']).toBe('Bearer');
  });

  test('valid login returns a bearer token and /me returns the same user', async ({ request }) => {
    const auth = await login(request, ADMIN_EMAIL, ADMIN_PASSWORD);
    expect(auth.user.email).toBe(ADMIN_EMAIL);
    expect(auth.user.role).toBe('ADMIN');

    const response = await request.get('/api/auth/me', {
      headers: bearer(auth.access_token),
    });

    expect(response.status()).toBe(200);
    const me = await response.json();
    expect(me.id).toBe(auth.user.id);
    expect(me.email).toBe(ADMIN_EMAIL);
    expect(response.headers()['content-type']).toContain('application/json');
  });

  test('authenticated project list returns the documented collection shape', async ({ request }) => {
    const auth = await login(request, QA_EMAIL, QA_PASSWORD);
    const response = await request.get('/api/projects?page=1&page_size=10', {
      headers: bearer(auth.access_token),
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body.items)).toBe(true);
    expect(body.total).toEqual(expect.any(Number));
    expect(body.page).toBe(1);
    expect(body.page_size).toBe(10);
    expect(response.headers()['content-type']).toContain('application/json');
  });

  test('rejects project creation with an invalid project key', async ({ request }) => {
    const auth = await login(request, ADMIN_EMAIL, ADMIN_PASSWORD);
    const response = await request.post('/api/projects', {
      headers: bearer(auth.access_token),
      data: { name: `Invalid key ${uniqueSuffix()}`, key: 'bad-key!' },
    });

    expect(response.status()).toBe(422);
    const body = await response.json();
    expect(body.detail).toBeTruthy();
  });

  test('rejects duplicate project keys with 409 and leaves the original project intact', async ({ request }) => {
    const auth = await login(request, ADMIN_EMAIL, ADMIN_PASSWORD);
    const headers = bearer(auth.access_token);
    const suffix = uniqueSuffix();
    const key = `DUP${suffix}`.slice(0, 20).toUpperCase();
    let projectId: number | undefined;

    try {
      const first = await request.post('/api/projects', {
        headers,
        data: { name: `Duplicate key original ${suffix}`, key },
      });
      expect(first.status()).toBe(201);
      projectId = (await first.json()).id;

      const duplicate = await request.post('/api/projects', {
        headers,
        data: { name: `Duplicate key second ${suffix}`, key },
      });
      expect(duplicate.status()).toBe(409);
      expect((await duplicate.json()).detail).toMatch(/already exists/i);

      const original = await request.get(`/api/projects/${projectId}`, { headers });
      expect(original.status()).toBe(200);
      expect((await original.json()).name).toBe(`Duplicate key original ${suffix}`);
    } finally {
      if (projectId !== undefined) {
        await request.delete(`/api/projects/${projectId}`, { headers }).catch(() => undefined);
      }
    }
  });

  test('viewer is forbidden from creating a project', async ({ request }) => {
    const auth = await login(request, VIEWER_EMAIL, VIEWER_PASSWORD);
    const response = await request.post('/api/projects', {
      headers: bearer(auth.access_token),
      data: {
        name: `Viewer forbidden ${uniqueSuffix()}`,
        key: `V${uniqueSuffix()}`.slice(0, 20).toUpperCase(),
      },
    });

    expect(response.status()).toBe(403);
  });

  test('creates a project, suite and test case through the API and verifies response contracts', async ({ request }) => {
    const auth = await login(request, ADMIN_EMAIL, ADMIN_PASSWORD);
    const headers = bearer(auth.access_token);
    const suffix = uniqueSuffix();
    let projectId: number | undefined;
    let suiteId: number | undefined;
    let testCaseId: number | undefined;

    try {
      const projectResponse = await request.post('/api/projects', {
        headers,
        data: {
          name: `API Workflow ${suffix}`,
          key: `API${suffix}`.slice(0, 20).toUpperCase(),
          description: 'Created by the Playwright API regression suite',
        },
      });
      expect(projectResponse.status()).toBe(201);
      expect(projectResponse.headers()['content-type']).toContain('application/json');
      const project = await projectResponse.json();
      projectId = project.id;
      expect(project.name).toBe(`API Workflow ${suffix}`);
      expect(project.status).toBe('ACTIVE');

      const suiteResponse = await request.post(`/api/projects/${project.id}/suites`, {
        headers,
        data: { name: `API Suite ${suffix}`, description: 'API workflow validation' },
      });
      expect(suiteResponse.status()).toBe(201);
      const suite = await suiteResponse.json();
      suiteId = suite.id;
      expect(suite.project_id).toBe(project.id);

      const caseResponse = await request.post(`/api/suites/${suite.id}/test-cases`, {
        headers,
        data: {
          title: `API Test Case ${suffix}`,
          expected_result: 'The created record is returned with the expected fields.',
          priority: 'HIGH',
          status: 'READY',
          steps: [{ order: 1, action: 'Submit a valid API request' }],
        },
      });
      expect(caseResponse.status()).toBe(201);
      const testCase = await caseResponse.json();
      testCaseId = testCase.id;
      expect(testCase.suite_id).toBe(suite.id);
      expect(testCase.title).toBe(`API Test Case ${suffix}`);
      expect(testCase.status).toBe('READY');
      expect(testCase.steps).toHaveLength(1);

      const runResponse = await request.post(`/api/projects/${project.id}/runs`, {
        headers,
        data: {
          name: `API Run ${suffix}`,
          environment: 'test',
          test_case_ids: [testCase.id],
        },
      });
      expect(runResponse.status()).toBe(201);
      const run = await runResponse.json();
      expect(run.project_id).toBe(projectId);
      expect(run.status).toBe('NOT_STARTED');

      const startResponse = await request.post(`/api/runs/${run.id}/start`, { headers });
      expect(startResponse.status()).toBe(200);
      expect((await startResponse.json()).status).toBe('IN_PROGRESS');

      const prematureComplete = await request.post(`/api/runs/${run.id}/complete`, { headers });
      expect(prematureComplete.status()).toBe(409);

      const resultsResponse = await request.get(`/api/runs/${run.id}/results`, { headers });
      expect(resultsResponse.status()).toBe(200);
      const resultsBody = await resultsResponse.json();
      expect(resultsBody.items).toHaveLength(1);
      const resultId = resultsBody.items[0].id;

      const recordResponse = await request.put(`/api/runs/${run.id}/results/${resultId}`, {
        headers,
        data: { status: 'PASSED', actual_result: 'API workflow completed successfully.' },
      });
      expect(recordResponse.status()).toBe(200);
      expect((await recordResponse.json()).status).toBe('PASSED');

      const completeResponse = await request.post(`/api/runs/${run.id}/complete`, { headers });
      expect(completeResponse.status()).toBe(200);
      expect((await completeResponse.json()).status).toBe('COMPLETED');

      const summaryResponse = await request.get(`/api/runs/${run.id}/summary`, { headers });
      expect(summaryResponse.status()).toBe(200);
      const summary = await summaryResponse.json();
      expect(summary.total).toBe(1);
      expect(summary.passed).toBe(1);
      expect(summary.not_run).toBe(0);
      expect(summary.pass_rate).toBe(100);

      const persistedResponse = await request.get(`/api/test-cases/${testCase.id}`, { headers });
      expect(persistedResponse.status()).toBe(200);
      expect((await persistedResponse.json()).title).toBe(`API Test Case ${suffix}`);
    } finally {
      if (testCaseId !== undefined) {
        await request.delete(`/api/test-cases/${testCaseId}`, { headers }).catch(() => undefined);
      }
      if (suiteId !== undefined) {
        await request.delete(`/api/suites/${suiteId}`, { headers }).catch(() => undefined);
      }
      if (projectId !== undefined) {
        await request.delete(`/api/projects/${projectId}`, { headers }).catch(() => undefined);
      }
    }
  });
});
