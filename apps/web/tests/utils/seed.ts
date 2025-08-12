// Deterministic seeding via public API
const API =
  process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

async function register(email: string, password: string) {
  const res = await fetch(`${API}/users/register`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok && res.status !== 400) {
    throw new Error(`register failed: ${res.status} ${await res.text()}`);
  }
}

async function login(email: string, password: string) {
  const res = await fetch(`${API}/users/login`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(`login failed: ${res.status} ${await res.text()}`);
  const data = (await res.json()) as { access_token: string };
  return data.access_token;
}

async function authedPost(path: string, token: string, body: unknown) {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function seedDashboardData() {
  const ts = Date.now();
  const email = `seed+${ts}@test.dev`;
  const password = 'secret123';
  await register(email, password);
  const token = await login(email, password);

  const leads = await Promise.all([
    authedPost(`/leads/`, token, { name: `Alice Able ${ts}`, email: `alice.${ts}@test.dev` }),
    authedPost(`/leads/`, token, { name: `Bob Baker ${ts}`, email: `bob.${ts}@test.dev` }),
    authedPost(`/leads/`, token, { name: `Cara Coast ${ts}`, email: `cara.${ts}@test.dev` }),
  ]);

  const tasks = await Promise.all([
    authedPost(`/tasks/`, token, { title: `Email follow-up ${ts}` }),
    authedPost(`/tasks/`, token, { title: `Prepare proposal ${ts}` }),
    authedPost(`/tasks/`, token, { title: `Close deal ${ts}` }),
  ]);

  return { leads, tasks };
}
