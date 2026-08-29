import { useState } from 'react';
import {
  Typography, Card, Descriptions, Button, Space, Row, Col,
  Form, Input, Select, Modal, notification,
} from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import { useAsync } from '../../hooks/useAsync';
import { getDefect, updateDefect } from '../../api/defects';
import { listProjects } from '../../api/projects';
import { listUsers } from '../../api/users';
import { PageLoader } from '../../components/common/PageLoader';
import { PageError } from '../../components/common/PageError';
import { StatusTag } from '../../components/common/StatusTag';
import { AppBreadcrumb } from '../../components/common/AppBreadcrumb';
import { usePermissions } from '../../hooks/usePermissions';
import { extractErrorMessage } from '../../api/client';
import { DEFECT_STATUS_LABELS, DEFECT_SEVERITY_LABELS, DEFECT_PRIORITY_LABELS } from '../../constants';
import type { DefectStatus, DefectSeverity, DefectPriority } from '../../types';

const { Title, Text } = Typography;
const { Option } = Select;

const TRANSITIONS: Record<DefectStatus, { label: string; target: DefectStatus }[]> = {
  OPEN:        [{ label: 'Start Work', target: 'IN_PROGRESS' }, { label: 'Reject', target: 'REJECTED' }],
  IN_PROGRESS: [{ label: 'Resolve', target: 'RESOLVED' }, { label: 'Reject', target: 'REJECTED' }],
  RESOLVED:    [{ label: 'Close', target: 'CLOSED' }, { label: 'Reopen Work', target: 'IN_PROGRESS' }],
  REJECTED:    [{ label: 'Reopen', target: 'OPEN' }],
  CLOSED:      [],
};

export function DefectDetailPage() {
  const { defectId } = useParams<{ defectId: string }>();
  const { canWrite } = usePermissions();
  const id = Number(defectId);

  const [editOpen, setEditOpen] = useState(false);
  const [editSaving, setEditSaving] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const [form] = Form.useForm();

  const { data: defect, isLoading, error, reload } = useAsync(() => getDefect(id), [id]);
  const { data: usersData } = useAsync(() => listUsers({ status: 'ACTIVE', page: 1, page_size: 100 }), []);
  const { data: projectsData } = useAsync(() => listProjects({ page: 1, page_size: 100 }), []);

  const handleTransition = async (target: DefectStatus) => {
    setTransitioning(true);
    try {
      await updateDefect(id, { status: target });
      notification.success({ message: `Status updated to ${DEFECT_STATUS_LABELS[target]}` });
      reload();
    } catch (err) {
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setTransitioning(false);
    }
  };

  const handleEdit = async () => {
    try {
      const values = await form.validateFields();
      setEditSaving(true);
      await updateDefect(id, values);
      notification.success({ message: 'Defect updated' });
      setEditOpen(false);
      reload();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setEditSaving(false);
    }
  };

  if (isLoading) return <PageLoader />;
  if (error) return <PageError message={error} />;
  if (!defect) return null;

  const transitions = TRANSITIONS[defect.status] ?? [];
  const userLabel = (userId: number | null) => {
    if (userId === null) return null;
    const user = usersData?.items.find((item) => item.id === userId);
    return user ? `${user.name} (${user.email})` : `User #${userId}`;
  };
  const project = projectsData?.items.find((item) => item.id === defect.project_id);

  return (
    <div>
      <AppBreadcrumb items={[{ label: 'Defects', path: '/defects' }, { label: defect.title }]} />

      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space align="center">
            <Title level={2} style={{ margin: 0 }}>{defect.title}</Title>
            <StatusTag value={defect.status} label={DEFECT_STATUS_LABELS[defect.status]} />
          </Space>
        </Col>
        {canWrite && (
          <Col>
            <Space>
              {transitions.map((t) => (
                <Button key={t.target} loading={transitioning} onClick={() => handleTransition(t.target)} aria-label={t.label}>
                  {t.label}
                </Button>
              ))}
              <Button icon={<EditOutlined />} onClick={() => {
                form.setFieldsValue({
                  title: defect.title,
                  description: defect.description,
                  severity: defect.severity,
                  priority: defect.priority,
                  environment: defect.environment,
                  assigned_to: defect.assigned_to,
                });
                setEditOpen(true);
              }} aria-label="Edit defect">Edit</Button>
            </Space>
          </Col>
        )}
      </Row>

      <Card>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label="Status"><StatusTag value={defect.status} label={DEFECT_STATUS_LABELS[defect.status]} /></Descriptions.Item>
          <Descriptions.Item label="Project">{project ? project.name : `Project #${defect.project_id}`}</Descriptions.Item>
          <Descriptions.Item label="Severity"><StatusTag value={defect.severity} label={DEFECT_SEVERITY_LABELS[defect.severity as DefectSeverity]} /></Descriptions.Item>
          <Descriptions.Item label="Priority"><StatusTag value={defect.priority} label={DEFECT_PRIORITY_LABELS[defect.priority as DefectPriority]} /></Descriptions.Item>
          <Descriptions.Item label="Environment">{defect.environment ?? <Text type="secondary">—</Text>}</Descriptions.Item>
          <Descriptions.Item label="Description" span={2}>{defect.description ?? <Text type="secondary">—</Text>}</Descriptions.Item>
          <Descriptions.Item label="Test Case">{defect.test_case_id ?? <Text type="secondary">—</Text>}</Descriptions.Item>
          <Descriptions.Item label="Created By">{userLabel(defect.created_by)}</Descriptions.Item>
          <Descriptions.Item label="Assigned To">{userLabel(defect.assigned_to) ?? <Text type="secondary">Unassigned</Text>}</Descriptions.Item>
          <Descriptions.Item label="Created">{new Date(defect.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="Updated">{new Date(defect.updated_at).toLocaleString()}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Modal title="Edit Defect" open={editOpen} onCancel={() => setEditOpen(false)} onOk={handleEdit} confirmLoading={editSaving} okText="Save" destroyOnClose width={560}>
        <Form form={form} layout="vertical">
          <Form.Item label="Title" name="title" rules={[{ required: true }]}>
            <Input aria-label="Defect title" />
          </Form.Item>
          <Form.Item label="Description" name="description">
            <Input.TextArea rows={2} aria-label="Description" />
          </Form.Item>
          <Space size="large">
            <Form.Item label="Severity" name="severity">
              <Select style={{ width: 140 }} aria-label="Severity">
                {(Object.keys(DEFECT_SEVERITY_LABELS) as DefectSeverity[]).map((s) => <Option key={s} value={s}>{DEFECT_SEVERITY_LABELS[s]}</Option>)}
              </Select>
            </Form.Item>
            <Form.Item label="Priority" name="priority">
              <Select style={{ width: 140 }} aria-label="Priority">
                {(Object.keys(DEFECT_PRIORITY_LABELS) as DefectPriority[]).map((p) => <Option key={p} value={p}>{DEFECT_PRIORITY_LABELS[p]}</Option>)}
              </Select>
            </Form.Item>
          </Space>
          <Form.Item label="Environment" name="environment">
            <Input aria-label="Environment" />
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
