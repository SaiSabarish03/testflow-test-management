import { useState } from 'react';
import {
  Typography, Table, Input, Select, Space, Button, Tag, Tooltip,
  Empty, Row, Col, Form, Modal, notification,
} from 'antd';
import { SearchOutlined, PlusOutlined, FolderOpenOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import { useAsync } from '../../hooks/useAsync';
import { listProjects, createProject } from '../../api/projects';
import { usePermissions } from '../../hooks/usePermissions';
import { PageError } from '../../components/common/PageError';
import { StatusTag } from '../../components/common/StatusTag';
import { PAGE_SIZE_DEFAULT, PROJECT_STATUS_LABELS } from '../../constants';
import { extractErrorMessage } from '../../api/client';
import type { Project, ProjectStatus } from '../../types';

const { Title } = Typography;
const { Option } = Select;

export function ProjectsPage() {
  const navigate = useNavigate();
  const { canWrite } = usePermissions();
  const [form] = Form.useForm();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | ''>('');
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const { data, isLoading, error, reload } = useAsync(
    () => listProjects({ search: search || undefined, status: statusFilter || undefined, page, page_size: PAGE_SIZE_DEFAULT }),
    [search, statusFilter, page],
  );

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      await createProject(values);
      notification.success({ message: 'Project created' });
      setModalOpen(false);
      form.resetFields();
      reload();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setSaving(false);
    }
  };

  const columns: ColumnsType<Project> = [
    {
      title: 'Name', dataIndex: 'name', key: 'name',
      render: (name: string, record) => (
        <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/projects/${record.id}`)} aria-label={`Open project ${name}`}>
          {name}
        </Button>
      ),
    },
    { title: 'Key', dataIndex: 'key', key: 'key', render: (key: string) => <Tag>{key}</Tag> },
    {
      title: 'Description', dataIndex: 'description', key: 'description',
      render: (desc: string | null) => desc
        ? <Tooltip title={desc}><span>{desc.length > 60 ? desc.slice(0, 60) + '…' : desc}</span></Tooltip>
        : <span style={{ color: '#bbb' }}>—</span>,
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (status: ProjectStatus) => <StatusTag value={status} label={PROJECT_STATUS_LABELS[status]} />,
    },
    {
      title: 'Created', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      title: '', key: 'actions',
      render: (_: unknown, record: Project) => (
        <Button icon={<FolderOpenOutlined />} size="small" onClick={() => navigate(`/projects/${record.id}`)} aria-label={`View project ${record.name}`}>
          View
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col><Title level={2} style={{ margin: 0 }}>Projects</Title></Col>
        {canWrite && (
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} aria-label="Create project">
              New Project
            </Button>
          </Col>
        )}
      </Row>

      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          placeholder="Search projects…" prefix={<SearchOutlined />} value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          style={{ width: 240 }} allowClear aria-label="Search projects"
        />
        <Select value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1); }} style={{ width: 160 }} aria-label="Filter by status">
          <Option value="">All statuses</Option>
          <Option value="ACTIVE">Active</Option>
          <Option value="ARCHIVED">Archived</Option>
        </Select>
      </Space>

      {error && <PageError message={error} onRetry={reload} />}

      <Table<Project>
        rowKey="id" columns={columns} dataSource={data?.items ?? []} loading={isLoading}
        locale={{ emptyText: <Empty description="No projects found" /> }}
        pagination={{ current: page, pageSize: PAGE_SIZE_DEFAULT, total: data?.total ?? 0, onChange: setPage, showTotal: (t) => `${t} project${t !== 1 ? 's' : ''}` }}
        aria-label="Projects table"
      />

      <Modal
        title="New Project" open={modalOpen} onCancel={() => { setModalOpen(false); form.resetFields(); }}
        onOk={handleCreate} confirmLoading={saving} okText="Create" destroyOnHidden aria-label="New Project"
      >
        <Form form={form} layout="vertical" aria-label="Create project form">
          <Form.Item label="Name" name="name" rules={[{ required: true, message: 'Name is required' }, { max: 255 }]}>
            <Input placeholder="My Project" aria-label="Project name" />
          </Form.Item>
          <Form.Item
            label="Key" name="key"
            rules={[
              { required: true, message: 'Key is required' },
              { pattern: /^[A-Z0-9]{2,20}$/, message: 'Key must be 2–20 uppercase letters/digits (e.g. TFW)' },
            ]}
          >
            <Input placeholder="TFW" style={{ textTransform: 'uppercase' }} aria-label="Project key" />
          </Form.Item>
          <Form.Item label="Description" name="description">
            <Input.TextArea rows={3} placeholder="Optional description" aria-label="Project description" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
