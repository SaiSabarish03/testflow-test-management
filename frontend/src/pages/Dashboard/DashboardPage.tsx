import { Row, Col, Card, Statistic, Typography } from 'antd';
import { ProjectOutlined, PlayCircleOutlined, BugOutlined } from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';
import { useAsync } from '../../hooks/useAsync';
import { listProjects } from '../../api/projects';
import { listDefects } from '../../api/defects';
import { PageLoader } from '../../components/common/PageLoader';

const { Title, Text } = Typography;

export function DashboardPage() {
  const { user } = useAuth();

  const projects = useAsync(() => listProjects({ page: 1, page_size: 1 }), []);
  const openDefects = useAsync(
    () => listDefects({ status: 'OPEN', page: 1, page_size: 1 }),
    [],
  );

  return (
    <div>
      <Title level={2} style={{ marginBottom: 4 }}>
        Dashboard
      </Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
        Welcome back, {user?.name ?? user?.email}
      </Text>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            {projects.isLoading ? (
              <PageLoader />
            ) : (
              <Statistic
                title="Projects"
                value={projects.data?.total ?? '—'}
                prefix={<ProjectOutlined />}
              />
            )}
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            {openDefects.isLoading ? (
              <PageLoader />
            ) : (
              <Statistic
                title="Open Defects"
                value={openDefects.data?.total ?? '—'}
                prefix={<BugOutlined />}
                valueStyle={
                  (openDefects.data?.total ?? 0) > 0 ? { color: '#cf1322' } : undefined
                }
              />
            )}
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Test Runs"
              value="—"
              prefix={<PlayCircleOutlined />}
              suffix={
                <Text type="secondary" style={{ fontSize: 12 }}>
                  select a project
                </Text>
              }
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
