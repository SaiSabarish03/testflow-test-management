import { useEffect, useState } from 'react';
import { Form, Input, Select, Button, Card, Typography, notification, Space } from 'antd';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useAsync } from '../../hooks/useAsync';
import { getTestCase, createTestCase, updateTestCase } from '../../api/testCases';
import { getSuite } from '../../api/testSuites';
import { PageLoader } from '../../components/common/PageLoader';
import { PageError } from '../../components/common/PageError';
import { AppBreadcrumb } from '../../components/common/AppBreadcrumb';
import { StepEditor, stepsToPayload, payloadToSteps } from '../../components/forms/StepEditor';
import type { StepItem } from '../../components/forms/StepEditor';
import { extractErrorMessage } from '../../api/client';

const { Title } = Typography;
const { Option } = Select;

interface FormValues {
  title: string;
  description?: string;
  preconditions?: string;
  expected_result: string;
  priority: string;
  status: string;
}

export function TestCaseFormPage() {
  const { suiteId, testCaseId } = useParams<{ suiteId?: string; testCaseId?: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [form] = Form.useForm<FormValues>();
  const [steps, setSteps] = useState<StepItem[]>([]);
  const [saving, setSaving] = useState(false);

  const isEdit = Boolean(testCaseId);
  const resolvedSuiteId = suiteId ? Number(suiteId) : undefined;
  const resolvedCaseId = testCaseId ? Number(testCaseId) : undefined;

  const { data: suite } = useAsync(
    () => (resolvedSuiteId ? getSuite(resolvedSuiteId) : Promise.resolve(null)),
    [resolvedSuiteId],
  );

  const { data: existingCase, isLoading, error } = useAsync(
    () => (resolvedCaseId ? getTestCase(resolvedCaseId) : Promise.resolve(null)),
    [resolvedCaseId],
  );

  useEffect(() => {
    if (existingCase) {
      form.setFieldsValue({
        title: existingCase.title,
        description: existingCase.description ?? undefined,
        preconditions: existingCase.preconditions ?? undefined,
        expected_result: existingCase.expected_result,
        priority: existingCase.priority,
        status: existingCase.status,
      });
      setSteps(payloadToSteps(existingCase.steps));
    }
  }, [existingCase, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const payload = { ...values, steps: stepsToPayload(steps) };

      if (isEdit && resolvedCaseId) {
        await updateTestCase(resolvedCaseId, payload);
        notification.success({ message: 'Test case updated' });
        navigate(`/test-cases/${resolvedCaseId}`);
      } else if (resolvedSuiteId) {
        const created = await createTestCase(resolvedSuiteId, payload);
        notification.success({ message: 'Test case created' });
        navigate(`/test-cases/${created.id}`);
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) return <PageLoader />;
  if (error) return <PageError message={error} />;

  const effectiveSuiteId = resolvedSuiteId ?? existingCase?.suite_id;
  const projectId = suite?.project_id ?? searchParams.get('project_id');

  return (
    <div>
      <AppBreadcrumb items={[
        { label: 'Projects', path: '/projects' },
        ...(projectId ? [{ label: 'Project', path: `/projects/${projectId}` }] : []),
        ...(effectiveSuiteId ? [{ label: suite?.name ?? 'Suite', path: `/suites/${effectiveSuiteId}` }] : []),
        { label: isEdit ? 'Edit Test Case' : 'New Test Case' },
      ]} />

      <Title level={2}>{isEdit ? 'Edit Test Case' : 'New Test Case'}</Title>

      <Card style={{ maxWidth: 760 }}>
        <Form form={form} layout="vertical" initialValues={{ status: 'DRAFT', priority: 'MEDIUM' }}>
          <Form.Item label="Title" name="title" rules={[{ required: true, message: 'Title is required' }]}>
            <Input placeholder="Verify login with valid credentials" aria-label="Test case title" />
          </Form.Item>

          <Form.Item label="Description" name="description">
            <Input.TextArea rows={2} aria-label="Description" />
          </Form.Item>

          <Form.Item label="Preconditions" name="preconditions">
            <Input.TextArea rows={2} placeholder="User must have an active account" aria-label="Preconditions" />
          </Form.Item>

          <Form.Item label="Steps">
            <StepEditor value={steps} onChange={setSteps} />
          </Form.Item>

          <Form.Item label="Expected Result" name="expected_result" rules={[{ required: true, message: 'Expected result is required' }]}>
            <Input.TextArea rows={2} placeholder="User is redirected to dashboard" aria-label="Expected result" />
          </Form.Item>

          <Space size="large">
            <Form.Item label="Priority" name="priority" rules={[{ required: true }]}>
              <Select style={{ width: 140 }} aria-label="Priority">
                {(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const).map((p) => <Option key={p} value={p}>{p}</Option>)}
              </Select>
            </Form.Item>

            <Form.Item label="Status" name="status" rules={[{ required: true }]}>
              <Select style={{ width: 140 }} aria-label="Status">
                <Option value="DRAFT">Draft</Option>
                <Option value="READY">Ready</Option>
              </Select>
            </Form.Item>
          </Space>

          <Form.Item>
            <Space>
              <Button type="primary" onClick={handleSubmit} loading={saving} aria-label={isEdit ? 'Save test case' : 'Create test case'}>
                {isEdit ? 'Save Changes' : 'Create Test Case'}
              </Button>
              <Button onClick={() => navigate(-1)} aria-label="Cancel">Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
