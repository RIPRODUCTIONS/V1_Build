import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <div className="p-8 rounded-lg bg-white shadow w-full max-w-md text-center space-y-4">
        <h1 className="text-2xl font-semibold">AI Business Engine</h1>
        <p className="text-gray-600">Autonomous AI agents running your business end-to-end</p>
        <Link href="/dashboard" className="inline-block px-4 py-2 rounded bg-blue-600 text-white">
          Launch Dashboard
        </Link>
      </div>
    </main>
  );
}
