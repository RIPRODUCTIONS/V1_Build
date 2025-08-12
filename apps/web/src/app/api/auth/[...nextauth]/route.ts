import NextAuth, { type Account, type NextAuthOptions, type Profile, type Session, type User } from 'next-auth';
import type { AdapterUser } from 'next-auth/adapters';
import type { JWT } from 'next-auth/jwt';
import Credentials from 'next-auth/providers/credentials';

export const authOptions: NextAuthOptions = {
  providers: [
    Credentials({
      name: 'demo',
      credentials: { username: { label: 'Username', type: 'text' } },
      authorize: async creds =>
        creds?.username
          ? {
              id: 'u1',
              name: creds.username,
              role: creds.username === 'admin' ? 'admin' : 'viewer',
            }
          : null,
    }),
  ],
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, user, account: _account, profile: _profile }: { token: JWT; user?: User | AdapterUser | null; account?: Account | null; profile?: Profile | null }) {
      const t = token as JWT & { role?: string };
      if (user) t.role = (user as { role?: string }).role ?? 'viewer';
      return t;
    },
    async session({ session, token }: { session: Session; token: JWT }) {
      (session as Session & { role?: string }).role = (token as JWT & { role?: string }).role ?? 'viewer';
      return session;
    },
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
