import { useState } from 'react';
import {
  Typography, Card, Descriptions, Button, Space, Row, Col, Tabs,
  Modal, Form, Input, notification, Popconfirm,
} from 'antd';
import { ArrowLeftOutlined, EditOutlined, StopOutlined } from '@ant-design/icons';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useAsync } from '../../hooks/useAsync';
import { getProject, updateProject, archiveProject } from '../../api/projects';
import { listUsers } from '../../api/users';
import { PageLoader } from '../../components/common/PageLoader';
import { PageError } from '../../components/common/PageError';
import { StatusTag } from '../../components/common/StatusTag';
import { AppBreadcrumb } from '../../components/common/AppBreadcrumb';
import { usePermissions } from '../../hooks/usePermissions';
import { extractErrorMessage } from '../../api/client';
import { PROJECT_STATUS_LABELS } from '../../constants';
import { SuitesTab } from './tabs/SuitesTab';
import { RunsTab } from './tabs/RunsTab';
import { DefectsTab } from './tabs/DefectsTab';

const { Title, Text } = Typography;

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { canWrite } = usePermissions();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'suites';
  const id = Number(projectId);
  const [editOpen, setEditOpen] = useState(false);
  const [editSaving, setEditSaving] = useState(false);
  const [form] = Form.useForm();

  const { data: project, isLoading, error, reload } = useAsync(() => getProject(id), [id]);
  const { data: usersData } = useAsync(() => listUsers({ page: 1, page_size: 100 }), []);

  const handleEdit = async () => {
    try {
      const values = await form.validateFields();
      setEditSaving(true);
      await updateProject(id, values);
      notification.success({ message: 'Project updated' });
      setEditOpen(false);
      reload();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setEditSaving(false);
    }
  };

  const handleArchive = async () => {
    try {
      await archiveProject(id);
      notification.success({ message: 'Project archived' });
      reload();
    } catch (err) {
      notification.error({ message: extractErrorMessage(err) });
    }
  };

  if (isLoading) return <PageLoader />;
  if (error) return <PageError message={error} onRetry={reload} />;
  if (!project) return null;

  const isArchived = project.status === 'ARCHIVED';
  const creator = usersData?.items.find((user) => user.id === project.created_by);

  const tabItems = [
    { key: 'suites', label: 'Test Suites', children: <SuitesTab project={project} /> },
    { key: 'runs', label: 'Test Runs', children: <RunsTab project={project} /> },
    { key: 'defects', label: 'Defects', children: <DefectsTab project={project} /> },
  ];

  return (
    <div>
      <AppBreadcrumb items={[{ label: 'Projects', path: '/projects' }, { label: project.name }]} />

      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space align="center">
            <Button icon={<ArrowLeftOutlined />} type="text" onClick={() => navigate('/projects')} aria-label="Back to projects" />
            <Title level={2} style={{ margin: 0 }}>{project.name}</Title>
            <StatusTag value={project.status} label={PROJECT_STATUS_LABELS[project.status]} />
          </Space>
        </Col>
        {canWrite && (
          <Col>
            <Space>
              <Button icon={<EditOutlined />} onClick={() => { form.setFieldsValue({ name: project.name, description: project.description }); setEditOpen(true); }} aria-label="Edit project">
                Edit
              </Button>
              {!isArchived && (
                <Popconfirm
                  title="Archive this project?"
                  description="The project will be archived. All historical data is preserved."
                  onConfirm={handleArchive}
                  okText="Archive"
                  okButtonProps={{ danger: true }}
                >
                  <Button icon={<StopOutlined />} danger aria-label="Archive project">Archive</Button>
                </Popconfirm>
              )}
            </Space>
          </Col>
        )}
      </Row>

      <Card style={{ marginBottom: 24 }}>
        <Descriptions column={{ xs: 1, sm: 2 }}>
          <Descriptions.Item label="Key">{project.key}</Descriptions.Item>
          <Descriptions.Item label="Status">
            <StatusTag value={project.status} label={PROJECT_STATUS_LABELS[project.status]} />
          </Descriptions.Item>
          <Descriptions.Item label="Description" span={2}>
            {project.description ?? <Text type="secondary">No description</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="Created">{new Date(project.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="Updated">{new Date(project.updated_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="Creator" span={2}>{creator ? `${creator.name} (${creator.email})` : `User #${project.created_by}`}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Tabs activeKey={activeTab} onChange={(key) => setSearchParams({ tab: key })} items={tabItems} />

      <Modal
        title="Edit Project" open={editOpen}
        onCancel={() => setEditOpen(false)} onOk={handleEdit}
        confirmLoading={editSaving} okText="Save" destroyOnHidden aria-label="Edit Project"
      >
        <Form form={form} layout="vertical">
          <Form.Item label="Name" name="name" rules={[{ required: true, message: 'Name is required' }]}>
            <Input aria-label="Project name" />
          </Form.Item>
          <Form.Item label="Description" name="description">
            <Input.TextArea rows={3} aria-label="Project description" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
