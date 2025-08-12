import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = { vus: 10, duration: '1m' };

export default function () {
  const base = __ENV.API || 'http://127.0.0.1:8000';
  const res = http.get(`${base}/health`);
  check(res, { 'status 200': r => r.status === 200 });
  sleep(1);
}


