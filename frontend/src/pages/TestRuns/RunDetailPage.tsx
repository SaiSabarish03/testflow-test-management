import { useState } from 'react';
import {
  Typography, Card, Descriptions, Button, Space, Row, Col,
  Table, Input, notification, Alert, Statistic, Progress, Popconfirm,
} from 'antd';
import { useParams } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import { useAsync } from '../../hooks/useAsync';
import { getRun, startRun, completeRun, abortRun, listResults, recordResult, getRunSummary } from '../../api/testRuns';
import { getProject } from '../../api/projects';
import { listUsers } from '../../api/users';
import { PageLoader } from '../../components/common/PageLoader';
import { PageError } from '../../components/common/PageError';
import { StatusTag } from '../../components/common/StatusTag';
import { AppBreadcrumb } from '../../components/common/AppBreadcrumb';
import { usePermissions } from '../../hooks/usePermissions';
import { extractErrorMessage } from '../../api/client';
import { TEST_RUN_STATUS_LABELS, TEST_RESULT_STATUS_LABELS } from '../../constants';
import type { TestResult, TestResultStatus, TestRunStatus } from '../../types';

const { Title, Text } = Typography;

export function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const { canWrite } = usePermissions();
  const id = Number(runId);

  const [actualResults, setActualResults] = useState<Record<number, string>>({});
  const [submitting, setSubmitting] = useState<Record<number, boolean>>({});
  const [actionLoading, setActionLoading] = useState(false);

  const { data: run, isLoading, error, reload: reloadRun } = useAsync(() => getRun(id), [id]);
  const { data: project } = useAsync(() => (run ? getProject(run.project_id) : Promise.resolve(null)), [run?.project_id]);
  const { data: resultsData, reload: reloadResults } = useAsync(() => listResults(id, { page: 1, page_size: 100 }), [id]);
  const { data: summary, reload: reloadSummary } = useAsync(() => getRunSummary(id), [id]);
  // listUsers requires ADMIN or QA_ENGINEER — only fetch when the current user has write access
  const { data: usersData } = useAsync(
    () => canWrite ? listUsers({ page: 1, page_size: 100 }) : Promise.resolve(null),
    [canWrite],
  );

  const reload = () => { reloadRun(); reloadResults(); reloadSummary(); };

  const handleAction = async (action: () => Promise<unknown>, successMsg: string) => {
    setActionLoading(true);
    try {
      await action();
      notification.success({ message: successMsg });
      reload();
    } catch (err) {
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRecord = async (result: TestResult, status: TestResultStatus) => {
    setSubmitting((s) => ({ ...s, [result.id]: true }));
    try {
      await recordResult(id, result.id, { status, actual_result: actualResults[result.id] });
      notification.success({ message: `Result recorded: ${TEST_RESULT_STATUS_LABELS[status]}` });
      reload();
    } catch (err) {
      notification.error({ message: extractErrorMessage(err) });
    } finally {
      setSubmitting((s) => ({ ...s, [result.id]: false }));
    }
  };

  if (isLoading) return <PageLoader />;
  if (error) return <PageError message={error} />;
  if (!run) return null;

  const isInProgress = run.status === 'IN_PROGRESS';
  const results = resultsData?.items ?? [];
  const userLabel = (userId: number | null) => {
    if (userId === null) return null;
    const user = usersData?.items.find((item) => item.id === userId);
    return user ? `${user.name} (${user.email})` : `User #${userId}`;
  };


  const columns: ColumnsType<TestResult> = [
    {
      title: 'Test Case', key: 'test_case',
      render: (_: unknown, record: TestResult) => record.test_case?.title ?? `Case #${record.test_case_id}`,
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: TestResultStatus) => <StatusTag value={s} label={TEST_RESULT_STATUS_LABELS[s]} />,
    },
    {
      title: 'Actual Result', key: 'actual',
      render: (_: unknown, record: TestResult) => {
        if (!isInProgress || record.status !== 'NOT_RUN' || !canWrite) {
          return <Text type="secondary">{record.actual_result ?? '—'}</Text>;
        }
        return (
          <Input
            size="small"
            placeholder="Actual result (optional)"
            value={actualResults[record.id] ?? ''}
            onChange={(e) => setActualResults((prev) => ({ ...prev, [record.id]: e.target.value }))}
            aria-label={`Actual result for ${record.test_case?.title ?? record.test_case_id}`}
            style={{ width: 200 }}
          />
        );
      },
    },
    {
      title: 'Executed By', dataIndex: 'executed_by', key: 'executed_by',
      render: (v: number | null) => userLabel(v) ?? <Text type="secondary">—</Text>,
    },
    {
      title: 'Executed At', dataIndex: 'executed_at', key: 'executed_at',
      render: (v: string | null) => v ? new Date(v).toLocaleString() : <Text type="secondary">—</Text>,
    },
    ...(isInProgress && canWrite ? [{
      title: 'Actions', key: 'record_actions',
      render: (_: unknown, record: TestResult) => {
        if (record.status !== 'NOT_RUN') return null;
        const busy = submitting[record.id] ?? false;
        return (
          <Space>
            <Button size="small" style={{ color: 'green', borderColor: 'green' }} loading={busy} onClick={() => handleRecord(record, 'PASSED')}>Pass</Button>
            <Button size="small" danger loading={busy} onClick={() => handleRecord(record, 'FAILED')}>Fail</Button>
            <Button size="small" loading={busy} onClick={() => handleRecord(record, 'BLOCKED')}>Blocked</Button>
          </Space>
        );
      },
    }] : []),
  ];

  const notRunCount = summary?.not_run ?? 0;

  return (
    <div>
      <AppBreadcrumb items={[
        { label: 'Projects', path: '/projects' },
        { label: project?.name ?? 'Project', path: `/projects/${run.project_id}` },
        { label: 'Test Runs', path: `/projects/${run.project_id}?tab=runs` },
        { label: run.name },
      ]} />

      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space align="center">
            <Title level={2} style={{ margin: 0 }}>{run.name}</Title>
            <StatusTag value={run.status} label={TEST_RUN_STATUS_LABELS[run.status as TestRunStatus]} />
          </Space>
        </Col>
        {canWrite && (
          <Col>
            <Space>
              {run.status === 'NOT_STARTED' && (
                <Button type="primary" loading={actionLoading} onClick={() => handleAction(() => startRun(id), 'Run started')} aria-label="Start Run">Start Run</Button>
              )}
              {run.status === 'IN_PROGRESS' && (
                <>
                  <Button
                    type="primary"
                    loading={actionLoading}
                    onClick={() => handleAction(() => completeRun(id), 'Run completed')}
                    aria-label="Complete Run"
                  >
                    Complete Run
                  </Button>
                  <Popconfirm title="Abort this run?" onConfirm={() => handleAction(() => abortRun(id), 'Run aborted')} okText="Abort" okButtonProps={{ danger: true }}>
                    <Button danger loading={actionLoading} aria-label="Abort Run">Abort Run</Button>
                  </Popconfirm>
                </>
              )}
            </Space>
          </Col>
        )}
      </Row>

      {run.status === 'IN_PROGRESS' && notRunCount > 0 && (
        <Alert message={`${notRunCount} result(s) still NOT_RUN — record all results before completing.`} type="info" showIcon style={{ marginBottom: 16 }} />
      )}

      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={{ xs: 1, sm: 2 }}>
          <Descriptions.Item label="Environment">{run.environment}</Descriptions.Item>
          <Descriptions.Item label="Status"><StatusTag value={run.status} label={TEST_RUN_STATUS_LABELS[run.status as TestRunStatus]} /></Descriptions.Item>
          <Descriptions.Item label="Created By">{userLabel(run.created_by)}</Descriptions.Item>
          <Descriptions.Item label="Created">{new Date(run.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="Started">{run.started_at ? new Date(run.started_at).toLocaleString() : <Text type="secondary">—</Text>}</Descriptions.Item>
          <Descriptions.Item label="Completed">{run.completed_at ? new Date(run.completed_at).toLocaleString() : <Text type="secondary">—</Text>}</Descriptions.Item>
        </Descriptions>
      </Card>

      {summary && (
        <Card title="Summary" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col><Statistic title="Total" value={summary.total} /></Col>
            <Col><Statistic title="Passed" value={summary.passed} valueStyle={{ color: '#3f8600' }} /></Col>
            <Col><Statistic title="Failed" value={summary.failed} valueStyle={{ color: '#cf1322' }} /></Col>
            <Col><Statistic title="Blocked" value={summary.blocked} valueStyle={{ color: '#d46b08' }} /></Col>
            <Col><Statistic title="Not Run" value={summary.not_run} /></Col>
            <Col>
              <div>
                <Text type="secondary">Pass Rate</Text>
                <Progress percent={summary.pass_rate} size="small" style={{ width: 120 }} />
              </div>
            </Col>
          </Row>
        </Card>
      )}

      <Card title="Results">
        <Table<TestResult>
          rowKey="id"
          columns={columns}
          dataSource={results}
          pagination={false}
          aria-label="Test results table"
        />
      </Card>
    </div>
  );
}
