'use client';

import { useState } from 'react';

import { useCreateRun } from '@/hooks/useCreateRun';

export default function CreateRunClientForm() {
  const [title, setTitle] = useState('');
  const { mutate, isPending } = useCreateRun();

  return (
    <form
      onSubmit={e => {
        e.preventDefault();
        if (!title.trim()) return;
        mutate({ title });
        setTitle('');
      }}
      className="flex gap-2 mb-4"
    >
      <input
        value={title}
        onChange={e => setTitle(e.target.value)}
        placeholder="Run title"
        className="border rounded px-2 py-1"
        aria-label="run-title"
      />
      <button type="submit" disabled={isPending} className="border rounded px-3 py-1">
        {isPending ? 'Creating…' : 'Create (client)'}
      </button>
    </form>
  );
}
