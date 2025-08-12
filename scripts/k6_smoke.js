import http from 'k6/http';
import { check, sleep } from 'k6';
export const options = {
  vus: 5,
  duration: '10s',
  thresholds: { http_req_failed: ['rate<0.05'], http_req_duration: ['p(95)<1000'] },
};
export default function () {
  const base = __ENV.API || 'http://127.0.0.1:8000';
  const res = http.get(`${base}/health/live`);
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(0.5);
}
