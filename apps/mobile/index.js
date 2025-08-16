import React, { useEffect, useState } from 'react';
import { View, Text, TextInput, Button, SafeAreaView, ScrollView, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import Constants from 'expo-constants';

const API = (Constants.expoConfig?.extra?.API_URL) || 'http://127.0.0.1:8000';

export default function App() {
  const [health, setHealth] = useState('?');
  const [topic, setTopic] = useState('mobile osint smoke');
  const [result, setResult] = useState('');
  const [running, setRunning] = useState(false);
  const [taskId, setTaskId] = useState('');
  const [runs, setRuns] = useState([]);

  useEffect(() => {
    fetch(`${API}/healthz`).then(r => setHealth(String(r.status))).catch(()=> setHealth('down'));
    fetch(`${API}/personal/runs`).then(r=>r.json()).then(j=> setRuns(j.items||[])).catch(()=>{});
  }, []);

  const run = async () => {
    setResult(''); setRunning(true); setTaskId('');
    try {
      const r = await fetch(`${API}/personal/run/research_assistant`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic })});
      const j = await r.json();
      setTaskId(j.task_id || '');
      setResult(JSON.stringify(j, null, 2));
    } catch (e) { setResult(String(e)); } finally { setRunning(false); }
  };

  const refresh = async () => {
    if (!taskId) return;
    try {
      const r = await fetch(`${API}/personal/result/${encodeURIComponent(taskId)}`);
      const j = await r.json();
      setResult(JSON.stringify(j, null, 2));
    } catch (e) { setResult(String(e)); }
  };

  return (
    <SafeAreaView style={s.root}>
      <ScrollView contentContainerStyle={s.container}>
        <Text style={s.h1}>Builder Mobile</Text>
        <Text style={s.mono}>API health: {health}</Text>
        <TextInput style={s.input} value={topic} onChangeText={setTopic} placeholder="topic" placeholderTextColor="#94a3b8" />
        <View style={{ flexDirection: 'row', gap: 12 }}>
          <Button title={running ? 'Running…' : 'Quick Research'} onPress={run} disabled={running} />
          <Button title="Refresh" onPress={refresh} disabled={!taskId} />
        </View>
        {taskId ? <Text style={s.mono}>Task: {taskId}</Text> : null}
        <Text style={s.h2}>Result</Text>
        <Text style={s.code}>{result}</Text>
        <Text style={s.h2}>Recent Personal Runs</Text>
        {runs.map((r, idx) => (
          <Text key={idx} style={s.mono}>[{r.status}] {r.template_id} • {r.task_id}</Text>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#0b1220' },
  container: { padding: 16, gap: 12 },
  h1: { color: '#e5e7eb', fontSize: 24, fontWeight: '700' },
  h2: { color: '#e5e7eb', fontSize: 18, fontWeight: '600', marginTop: 16 },
  mono: { color: '#93c5fd', fontFamily: 'Menlo' },
  input: { backgroundColor: '#0f172a', color: '#e5e7eb', borderColor: '#1f2937', borderWidth: 1, borderRadius: 8, padding: 10 },
  code: { color: '#e5e7eb', fontFamily: 'Menlo' }
});


