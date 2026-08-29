import { useEffect, useState } from 'react';
import {
  Typography, Table, Input, Select, Space, Button, Empty, Row, Col,
  Form, Modal, notification,
} from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import { useAsync } from '../../hooks/useAsync';
import { listDefects, createDefect } from '../../api/defects';
import { listProjects } from '../../api/projects';
import { listSuites } from '../../api/testSuites';
import { listTestCases } from '../../api/testCases';
import { listUsers } from '../../api/users';
import { usePermissions } from '../../hooks/usePermissions';
import { PageError } from '../../components/common/PageError';
import { StatusTag } from '../../components/common/StatusTag';
import { extractErrorMessage } from '../../api/client';
import { PAGE_SIZE_DEFAULT, DEFECT_STATUS_LABELS, DEFECT_SEVERITY_LABELS, DEFECT_PRIORITY_LABELS } from '../../constants';
import type { Defect, DefectStatus, DefectSeverity, DefectPriority, TestCase } from '../../types';

const { Title } = Typography;
const { Option } = Select;

export function DefectsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { canWrite } = usePermissions();
  const [form] = Form.useForm();

  const [search, setSearch] = useState('');
  const [projectFilter, setProjectFilter] = useState<number | ''>(
    searchParams.get('project_id') ? Number(searchParams.get('project_id')) : '',
  );
  const [severityFilter, setSeverityFilter] = useState<DefectSeverity | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<DefectPriority | ''>('');
  const [statusFilter, setStatusFilter] = useState<DefectStatus | ''>('');
  const [assigneeFilter, setAssigneeFilter] = useState<number | ''>('');
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(searchParams.get('create') === '1');
  const [saving, setSaving] = useState(false);
  const selectedProjectId = Form.useWatch('project_id', form) as number | undefined;

  const { data, isLoading, error, reload } = useAsync(
    () => listDefects({
      search: search || undefined,
      project_id: projectFilter || undefined,
      severity: severityFilter || undefined,
      priority: priorityFilter || undefined,
      status: statusFilter || undefined,
      assigned_to: assigneeFilter || undefined,
      page,
      page_size: PAGE_SIZE_DEFAULT,
    }),
    [search, projectFilter, severityFilter, priorityFilter, statusFilter, assigneeFilter, page],
  );

  const { data: projectsData } = useAsync(() => listProjects({ page: 1, page_size: 100 }), []);
  const { data: usersData } = useAsync(() => listUsers({ status: 'ACTIVE', page: 1, page_size: 100 }), []);
  const { data: suitesData } = useAsync(
    () => selectedProjectId ? listSuites(selectedProjectId, { page: 1, page_size: 100 }) : Promise.resolve({ items: [], total: 0, page: 1, page_size: 100, pages: 1 }),
    [selectedProjectId],
  );
  const suiteIds = suitesData?.items.map((suite) => suite.id) ?? [];
  const suiteNameById = new Map((suitesData?.items ?? []).map((suite) => [suite.id, suite.name]));
  const { data: testCasesData } = useAsync(
    async () => {
      if (suiteIds.length === 0) return { items: [] as TestCase[], total: 0, page: 1, page_size: 100, pages: 1 };
      const responses = await Promise.all(
        suiteIds.map((suiteId) => listTestCases(suiteId, { page: 1, page_size: 100 })),
      );
      const items = responses.flatMap((response) => response.items);
      return { items, total: items.length, page: 1, page_size: 100, pages: 1 };
    },
    [suiteIds.join(',')],
  );

  useEffect(() => {
    const projectId = searchParams.get('project_id');
    if (projectId) {
      form.setFieldsValue({ project_id: Number(projectId) });
    }
  }, [form, searchParams]);

  const projectName = (projectId: number) =>
    projectsData?.items.find((project) => project.id === projectId)?.name ?? `Project #${projectId}`;
  const userName = (userId: number | null) => {
    if (userId === null) return 'Unassigned';
    const user = usersData?.items.find((item) => item.id === userId);
    return user ? user.name : `User #${userId}`;
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const created = await createDefect(values);
      notification.success({ message: 'Defect created' });
      setModalOpen(false);
      form.resetFields();
      navigate(`/defects/${created.id}`);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setSaving(false);
    }
  };

  const columns: ColumnsType<Defect> = [
    {
      title: 'Title', dataIndex: 'title', key: 'title',
      render: (title: string, record) => (
        <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/defects/${record.id}`)} aria-label={`Open defect ${title}`}>{title}</Button>
      ),
    },
    { title: 'Severity', dataIndex: 'severity', key: 'severity', render: (s: DefectSeverity) => <StatusTag value={s} label={DEFECT_SEVERITY_LABELS[s]} /> },
    { title: 'Priority', dataIndex: 'priority', key: 'priority', render: (p: DefectPriority) => <StatusTag value={p} label={DEFECT_PRIORITY_LABELS[p]} /> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: DefectStatus) => <StatusTag value={s} label={DEFECT_STATUS_LABELS[s]} /> },
    { title: 'Project', dataIndex: 'project_id', key: 'project_id', render: (projectId: number) => projectName(projectId) },
    { title: 'Assignee', dataIndex: 'assigned_to', key: 'assigned_to', render: (userId: number | null) => userName(userId) },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleDateString() },
    {
      title: '', key: 'actions',
      render: (_: unknown, record: Defect) => (
        <Button size="small" onClick={() => navigate(`/defects/${record.id}`)} aria-label={`View defect ${record.title}`}>View</Button>
      ),
    },
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col><Title level={2} style={{ margin: 0 }}>Defects</Title></Col>
        {canWrite && (
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} aria-label="Create defect">New Defect</Button>
          </Col>
        )}
      </Row>

      <Space style={{ marginBottom: 16 }} wrap>
        <Input placeholder="Search defects…" prefix={<SearchOutlined />} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} style={{ width: 220 }} allowClear aria-label="Search defects" />
        <Select value={projectFilter} onChange={(v) => { setProjectFilter(v); setPage(1); }} style={{ width: 180 }} aria-label="Filter by project">
          <Option value="">All projects</Option>
          {projectsData?.items.map((p) => <Option key={p.id} value={p.id}>{p.name}</Option>)}
        </Select>
        <Select value={severityFilter} onChange={(v) => { setSeverityFilter(v); setPage(1); }} style={{ width: 140 }} aria-label="Filter by severity">
          <Option value="">All severities</Option>
          {(Object.keys(DEFECT_SEVERITY_LABELS) as DefectSeverity[]).map((s) => <Option key={s} value={s}>{DEFECT_SEVERITY_LABELS[s]}</Option>)}
        </Select>
        <Select value={priorityFilter} onChange={(v) => { setPriorityFilter(v); setPage(1); }} style={{ width: 140 }} aria-label="Filter by priority">
          <Option value="">All priorities</Option>
          {(Object.keys(DEFECT_PRIORITY_LABELS) as DefectPriority[]).map((p) => <Option key={p} value={p}>{DEFECT_PRIORITY_LABELS[p]}</Option>)}
        </Select>
        <Select value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1); }} style={{ width: 140 }} aria-label="Filter by status">
          <Option value="">All statuses</Option>
          {(Object.keys(DEFECT_STATUS_LABELS) as DefectStatus[]).map((s) => <Option key={s} value={s}>{DEFECT_STATUS_LABELS[s]}</Option>)}
        </Select>
        <Select value={assigneeFilter} onChange={(v) => { setAssigneeFilter(v); setPage(1); }} style={{ width: 180 }} aria-label="Filter by assignee">
          <Option value="">All assignees</Option>
          {usersData?.items.map((user) => <Option key={user.id} value={user.id}>{user.name}</Option>)}
        </Select>
      </Space>

      {error && <PageError message={error} onRetry={reload} />}

      <Table<Defect>
        rowKey="id" columns={columns} dataSource={data?.items ?? []} loading={isLoading}
        locale={{ emptyText: <Empty description="No defects found" /> }}
        pagination={{ current: page, pageSize: PAGE_SIZE_DEFAULT, total: data?.total ?? 0, onChange: setPage, showTotal: (t) => `${t} defect${t !== 1 ? 's' : ''}` }}
        aria-label="Defects table"
      />

      <Modal title="New Defect" open={modalOpen} onCancel={() => { setModalOpen(false); form.resetFields(); }} onOk={handleCreate} confirmLoading={saving} okText="Create" destroyOnClose width={600}>
        <Form form={form} layout="vertical">
          <Form.Item label="Project" name="project_id" rules={[{ required: true, message: 'Project is required' }]}>
            <Select
              placeholder="Select project"
              aria-label="Project"
              onChange={() => form.setFieldsValue({ test_case_id: undefined })}
            >
              {projectsData?.items.map((p) => <Option key={p.id} value={p.id}>{p.name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item label="Test Case" name="test_case_id">
            <Select allowClear placeholder="No linked test case" aria-label="Test case" disabled={!selectedProjectId}>
              {testCasesData?.items.map((testCase) => (
                <Option key={testCase.id} value={testCase.id}>
                  {testCase.title} ({suiteNameById.get(testCase.suite_id) ?? `Suite #${testCase.suite_id}`})
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="Title" name="title" rules={[{ required: true, message: 'Title is required' }]}>
            <Input aria-label="Defect title" />
          </Form.Item>
          <Form.Item label="Description" name="description">
            <Input.TextArea rows={2} aria-label="Description" />
          </Form.Item>
          <Space size="large">
            <Form.Item label="Severity" name="severity" rules={[{ required: true, message: 'Severity is required' }]}>
              <Select style={{ width: 140 }} aria-label="Severity">
                {(Object.keys(DEFECT_SEVERITY_LABELS) as DefectSeverity[]).map((s) => <Option key={s} value={s}>{DEFECT_SEVERITY_LABELS[s]}</Option>)}
              </Select>
            </Form.Item>
            <Form.Item label="Priority" name="priority" rules={[{ required: true, message: 'Priority is required' }]}>
              <Select style={{ width: 140 }} aria-label="Priority">
                {(Object.keys(DEFECT_PRIORITY_LABELS) as DefectPriority[]).map((p) => <Option key={p} value={p}>{DEFECT_PRIORITY_LABELS[p]}</Option>)}
              </Select>
            </Form.Item>
          </Space>
          <Form.Item label="Environment" name="environment">
            <Input placeholder="QA" aria-label="Environment" />
          </Form.Item>
          <Form.Item label="Assign To" name="assigned_to">
            <Select allowClear placeholder="Unassigned" aria-label="Assign to">
              {usersData?.items.map((u) => <Option key={u.id} value={u.id}>{u.name} ({u.email})</Option>)}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
