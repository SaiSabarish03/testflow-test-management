import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

export function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <Result
      status="404"
      title="404"
      subTitle="The page you are looking for does not exist."
      extra={
        <Button type="primary" onClick={() => navigate('/dashboard')} aria-label="Go to dashboard">
          Back to Dashboard
        </Button>
      }
    />
  );
}
