import { Alert, Button } from 'antd';

interface Props {
  message: string;
  onRetry?: () => void;
}

export function PageError({ message, onRetry }: Props) {
  return (
    <Alert
      type="error"
      message="Something went wrong"
      description={message}
      action={
        onRetry ? (
          <Button size="small" onClick={onRetry}>
            Retry
          </Button>
        ) : undefined
      }
      showIcon
    />
  );
}
