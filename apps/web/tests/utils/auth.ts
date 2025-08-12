export async function programmaticLogin(page: any, email: string, password: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  const res = await page.request.post(`${base}/users/login`, { data: { email, password } });
  const json = await res.json();
  const token = json.access_token as string;
  await page.addInitScript((t: string) => localStorage.setItem('token', t), token);
}


