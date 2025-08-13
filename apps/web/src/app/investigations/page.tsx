"use client";
import { useEffect, useState } from "react";

type RunItem = { id: number; kind: string; status: string; created_at?: string; task_id?: string };

export default function InvestigationsPage() {
  const [subjectName, setSubjectName] = useState("");
  const [subjectLocation, setSubjectLocation] = useState("");
  const [running, setRunning] = useState(false);
  const [runningFx, setRunningFx] = useState<string | null>(null);
  const [recent, setRecent] = useState<RunItem[]>([]);
  const [message, setMessage] = useState<string>("");

  const loadRecent = async () => {
    try {
      const res = await fetch(`/api/investigations/recent`).then((x) => x.json());
      setRecent((res.items || []).map((r: any) => ({...r})));
    } catch {}
  };

  useEffect(() => {
    loadRecent();
    const t = setInterval(loadRecent, 5000);
    return () => clearInterval(t);
  }, []);

  const runOsint = async () => {
    if (!subjectName.trim()) {
      setMessage("Enter a subject name");
      return;
    }
    setMessage("");
    setRunning(true);
    try {
      const body = {
        subject: { name: subjectName.trim(), location: subjectLocation.trim() || undefined },
      };
      const res = await fetch(`/api/investigations/osint/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).then((x) => x.json());
      if (res?.task_id) setMessage(`Queued: ${res.task_id}`);
      await loadRecent();
    } catch (e: any) {
      setMessage(`Error: ${e?.message || "failed"}`);
    } finally {
      setRunning(false);
    }
  };

  const runForensicsTimeline = async () => {
    setRunningFx("forensics");
    try {
      const res = await fetch(`/api/investigations/forensics/timeline/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ source: "evidence.dd" }) }).then((x) => x.json());
      if (res?.task_id) setMessage(`Forensics queued: ${res.task_id}`);
      await loadRecent();
    } catch (e: any) {
      setMessage(`Error: ${e?.message || "failed"}`);
    } finally {
      setRunningFx(null);
    }
  };

  const runMalwareDynamic = async () => {
    setRunningFx("malware");
    try {
      const res = await fetch(`/api/investigations/malware/dynamic/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sample: "sample.exe" }) }).then((x) => x.json());
      if (res?.task_id) setMessage(`Malware queued: ${res.task_id}`);
      await loadRecent();
    } catch (e: any) {
      setMessage(`Error: ${e?.message || "failed"}`);
    } finally {
      setRunningFx(null);
    }
  };

  const runAptAttribution = async () => {
    setRunningFx("apt");
    try {
      const res = await fetch(`/api/investigations/threat/apt_attribution/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ candidate_groups: ["APT28", "APT29", "APT1"], evidence: { infrastructure: true } }) }).then((x) => x.json());
      if (res?.task_id) setMessage(`APT queued: ${res.task_id}`);
      await loadRecent();
    } catch (e: any) {
      setMessage(`Error: ${e?.message || "failed"}`);
    } finally {
      setRunningFx(null);
    }
  };

  const runSca = async () => {
    setRunningFx("sca");
    try {
      const res = await fetch(`/api/investigations/supplychain/sca/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ project: "backend/" }) }).then((x) => x.json());
      if (res?.task_id) setMessage(`SCA queued: ${res.task_id}`);
      await loadRecent();
    } catch (e: any) {
      setMessage(`Error: ${e?.message || "failed"}`);
    } finally {
      setRunningFx(null);
    }
  };

  const runAutopilot = async () => {
    setRunningFx("autopilot");
    try {
      const res = await fetch(`/api/investigations/autopilot/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) }).then((x) => x.json());
      if (res?.task_id) setMessage(`Autopilot queued: ${res.task_id}`);
      await loadRecent();
    } catch (e: any) {
      setMessage(`Error: ${e?.message || "failed"}`);
    } finally {
      setRunningFx(null);
    }
  };

  return (
    <section className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Investigations</h1>

      <div className="border rounded p-4 bg-white space-y-2">
        <div className="font-medium">OSINT Dossier</div>
        <label className="block text-sm font-medium">Subject Name</label>
        <input
          className="border rounded p-2 text-sm w-full"
          placeholder="Jane Doe"
          value={subjectName}
          onChange={(e) => setSubjectName(e.target.value)}
        />
        <label className="block text-sm font-medium mt-2">Location (optional)</label>
        <input
          className="border rounded p-2 text-sm w-full"
          placeholder="San Francisco, CA"
          value={subjectLocation}
          onChange={(e) => setSubjectLocation(e.target.value)}
        />
        <div className="mt-2">
          <button
            className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
            onClick={runOsint}
            disabled={running}
          >
            {running ? "Queuing…" : "Run OSINT"}
          </button>
          {message && <div className="text-xs text-gray-700 mt-2">{message}</div>}
        </div>
      </div>

      <div className="border rounded p-4 bg-white space-y-2">
        <div className="font-medium">Autopilot (End-to-End)</div>
        <button className="bg-purple-700 text-white px-3 py-1 rounded text-sm" onClick={runAutopilot} disabled={runningFx === 'autopilot'}>
          {runningFx === 'autopilot' ? 'Queuing…' : 'Run Autopilot'}
        </button>
      </div>

      <div className="border rounded p-4 bg-white space-y-2">
        <div className="font-medium">Forensics Timeline</div>
        <button className="bg-gray-800 text-white px-3 py-1 rounded text-sm" onClick={runForensicsTimeline} disabled={runningFx === 'forensics'}>
          {runningFx === 'forensics' ? 'Queuing…' : 'Run Timeline'}
        </button>
      </div>

      <div className="border rounded p-4 bg-white space-y-2">
        <div className="font-medium">Malware Dynamic Analysis</div>
        <button className="bg-gray-800 text-white px-3 py-1 rounded text-sm" onClick={runMalwareDynamic} disabled={runningFx === 'malware'}>
          {runningFx === 'malware' ? 'Queuing…' : 'Analyze Sample'}
        </button>
      </div>

      <div className="border rounded p-4 bg-white space-y-2">
        <div className="font-medium">APT Attribution</div>
        <button className="bg-gray-800 text-white px-3 py-1 rounded text-sm" onClick={runAptAttribution} disabled={runningFx === 'apt'}>
          {runningFx === 'apt' ? 'Queuing…' : 'Run Attribution'}
        </button>
      </div>

      <div className="border rounded p-4 bg-white space-y-2">
        <div className="font-medium">Supply Chain SCA</div>
        <button className="bg-gray-800 text-white px-3 py-1 rounded text-sm" onClick={runSca} disabled={runningFx === 'sca'}>
          {runningFx === 'sca' ? 'Queuing…' : 'Run SCA Scan'}
        </button>
      </div>

      <div className="border rounded p-4 bg-white">
        <div className="font-medium mb-2">Recent Investigations</div>
        {!recent.length && <div className="text-sm text-gray-600">No recent runs.</div>}
        {!!recent.length && (
          <ul className="space-y-2">
            {recent.map((r) => (
              <li key={r.id} className="text-sm flex items-center justify-between">
                <div>
                  <div className="font-mono text-xs">{r.kind}</div>
                  <div className={`text-xs ${r.status === 'completed' ? 'text-green-600' : r.status === 'error' ? 'text-red-600' : 'text-gray-600'}`}>{r.status}</div>
                  <div className="text-xs text-gray-500">{r.created_at}</div>
                  {r.task_id && (
                    <a className="underline text-blue-600 text-xs" href={`/investigations/${r.task_id}`}>View details</a>
                  )}
                </div>
                {r.kind === 'osint' && r.task_id && (
                  <a className="underline text-blue-600 text-xs" href={`/api/investigations/osint/report/${r.task_id}`} target="_blank" rel="noreferrer">Download Report</a>
                )}
                {r.kind === 'forensics_timeline' && r.task_id && (
                  <a className="underline text-blue-600 text-xs ml-2" href={`/api/investigations/forensics/report/${r.task_id}`} target="_blank" rel="noreferrer">Forensics PDF</a>
                )}
                {r.kind === 'malware_dynamic' && r.task_id && (
                  <a className="underline text-blue-600 text-xs ml-2" href={`/api/investigations/malware/report/${r.task_id}`} target="_blank" rel="noreferrer">Malware PDF</a>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}


