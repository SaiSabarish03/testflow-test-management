import { Typography, Card, Descriptions, Button, Space, Tag, List, Popconfirm, notification, Row, Col } from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useAsync } from '../../hooks/useAsync';
import { getTestCase, deprecateTestCase, updateTestCase } from '../../api/testCases';
import { getSuite } from '../../api/testSuites';
import { listUsers } from '../../api/users';
import { PageLoader } from '../../components/common/PageLoader';
import { PageError } from '../../components/common/PageError';
import { StatusTag } from '../../components/common/StatusTag';
import { AppBreadcrumb } from '../../components/common/AppBreadcrumb';
import { usePermissions } from '../../hooks/usePermissions';
import { extractErrorMessage } from '../../api/client';
import { TEST_CASE_STATUS_LABELS } from '../../constants';
import type { TestCasePriority } from '../../types';

const { Title, Text } = Typography;

const PRIORITY_COLORS: Record<TestCasePriority, string> = {
  LOW: 'default', MEDIUM: 'blue', HIGH: 'orange', CRITICAL: 'red',
};

export function TestCaseDetailPage() {
  const { testCaseId } = useParams<{ testCaseId: string }>();
  const navigate = useNavigate();
  const { canWrite } = usePermissions();
  const id = Number(testCaseId);

  const { data: tc, isLoading, error, reload } = useAsync(() => getTestCase(id), [id]);
  const { data: suite } = useAsync(() => (tc ? getSuite(tc.suite_id) : Promise.resolve(null)), [tc?.suite_id]);
  const { data: usersData } = useAsync(() => listUsers({ page: 1, page_size: 100 }), []);

  const handleDeprecate = async () => {
    try {
      await deprecateTestCase(id);
      notification.success({ message: 'Test case deprecated' });
      reload();
    } catch (err) {
      notification.error({ message: extractErrorMessage(err) });
    }
  };

  const handleMarkReady = async () => {
    try {
      await updateTestCase(id, { status: 'READY' });
      notification.success({ message: 'Test case marked as Ready' });
      reload();
    } catch (err) {
      notification.error({ message: extractErrorMessage(err) });
    }
  };

  if (isLoading) return <PageLoader />;
  if (error) return <PageError message={error} />;
  if (!tc) return null;
  const creator = usersData?.items.find((user) => user.id === tc.created_by);

  return (
    <div>
      <AppBreadcrumb items={[
        { label: 'Projects', path: '/projects' },
        ...(suite ? [{ label: 'Project', path: `/projects/${suite.project_id}` }, { label: suite.name, path: `/suites/${suite.id}` }] : []),
        { label: tc.title },
      ]} />

      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space align="center">
            <Title level={2} style={{ margin: 0 }}>{tc.title}</Title>
            <StatusTag value={tc.status} label={TEST_CASE_STATUS_LABELS[tc.status]} />
          </Space>
        </Col>
        {canWrite && (
          <Col>
            <Space>
              {tc.status === 'DRAFT' && (
                <Button type="primary" onClick={handleMarkReady} aria-label="Mark as Ready">Mark as Ready</Button>
              )}
              <Button icon={<EditOutlined />} onClick={() => navigate(`/test-cases/${id}/edit`)} aria-label="Edit test case">Edit</Button>
              {tc.status !== 'DEPRECATED' && (
                <Popconfirm title="Deprecate this test case?" onConfirm={handleDeprecate} okText="Deprecate" okButtonProps={{ danger: true }}>
                  <Button danger aria-label="Deprecate test case">Deprecate</Button>
                </Popconfirm>
              )}
            </Space>
          </Col>
        )}
      </Row>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label="Priority">
            <Tag color={PRIORITY_COLORS[tc.priority]}>{tc.priority}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <StatusTag value={tc.status} label={TEST_CASE_STATUS_LABELS[tc.status]} />
          </Descriptions.Item>
          <Descriptions.Item label="Description" span={2}>
            {tc.description ?? <Text type="secondary">—</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="Preconditions" span={2}>
            {tc.preconditions ?? <Text type="secondary">—</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="Expected Result" span={2}>
            {tc.expected_result}
          </Descriptions.Item>
          <Descriptions.Item label="Creator">{creator ? `${creator.name} (${creator.email})` : `User #${tc.created_by}`}</Descriptions.Item>
          <Descriptions.Item label="Created">{new Date(tc.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="Updated">{new Date(tc.updated_at).toLocaleString()}</Descriptions.Item>
        </Descriptions>
      </Card>

      {tc.steps && tc.steps.length > 0 && (
        <Card title="Steps">
          <List
            dataSource={[...tc.steps].sort((a, b) => a.order - b.order)}
            renderItem={(step) => (
              <List.Item>
                <Space>
                  <Tag>{step.order}</Tag>
                  <Text>{step.action}</Text>
                </Space>
              </List.Item>
            )}
            aria-label="Test steps"
          />
        </Card>
      )}
    </div>
  );
}
