export const adminCookie = (baseURL = 'http://localhost:3000') => [
  { name: 'role', value: 'admin', url: baseURL, httpOnly: false },
];

