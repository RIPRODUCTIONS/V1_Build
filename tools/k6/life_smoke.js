import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 1,
  iterations: 5,
};

function token() {
  // For demo, hit login endpoint to get token
  const base = __ENV.API_BASE_URL || 'http://127.0.0.1:8000';
  const email = `k6+${Date.now()}@test.dev`;
  http.post(`${base}/users/register`, JSON.stringify({ email, password: 'secret123' }), {
    headers: { 'Content-Type': 'application/json' },
  });
  const res = http.post(`${base}/users/login`, JSON.stringify({ email, password: 'secret123' }), {
    headers: { 'Content-Type': 'application/json' },
  });
  return res.json('access_token');
}

export default function () {
  const base = __ENV.API_BASE_URL || 'http://127.0.0.1:8000';
  const tok = token();
  const res = http.post(`${base}/life/calendar/organize`, JSON.stringify({}), {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
  });
  check(res, { 'status is 200/202': r => r.status === 200 || r.status === 202 });
  sleep(1);
}
