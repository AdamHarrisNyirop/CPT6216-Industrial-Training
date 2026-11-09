import { useState } from 'react';
import AutofixPage from './AutofixPage.jsx';
import MainPage from './MainPage.jsx';
import ResultPage from './ResultPage.jsx';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const POLL_INTERVAL_MS = 1200;
const MAX_POLL_ATTEMPTS = 150;

function App() {
  const [file, setFile] = useState(null);
  const [studentId, setStudentId] = useState('');
  const [assignmentId, setAssignmentId] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [sourceCode, setSourceCode] = useState('');
  const [result, setResult] = useState(null);
  const [fixedCode, setFixedCode] = useState('');
  const [fixError, setFixError] = useState('');
  const [isAutofixPage, setIsAutofixPage] = useState(false);

  async function getErrorMessage(response) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    if (typeof detail === 'string') return detail;
    if (detail) return JSON.stringify(detail);
    return `Request failed (${response.status})`;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) return;

    setError('');
    setResult(null);
    setStatus('Uploading submission...');

    try {
      const code = await file.text();
      const formData = new FormData();
      formData.append('student_id', studentId);
      formData.append('assignment_id', assignmentId);
      formData.append('language', 'python');
      formData.append('file', file);

      const submitResponse = await fetch(`${API_BASE_URL}/api/submissions`, {
        method: 'POST',
        body: formData,
      });
      if (!submitResponse.ok) {
        throw new Error(await getErrorMessage(submitResponse));
      }

      const submission = await submitResponse.json();
      setSourceCode(code);

      for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt += 1) {
        setStatus(`Analysis ${submission.status.toLowerCase()}...`);
        const reportResponse = await fetch(
          `${API_BASE_URL}/api/submissions/${encodeURIComponent(submission.id)}`,
        );
        if (!reportResponse.ok) {
          throw new Error(await getErrorMessage(reportResponse));
        }

        const report = await reportResponse.json();
        if (report.status === 'COMPLETED') {
          setResult(report);
          setStatus('');
          return;
        }
        if (report.status === 'FAILED') {
          const detail = report.report_json?.map((item) => item.message).join(' ');
          throw new Error(detail || 'The analysis worker could not process this file.');
        }

        setStatus(`Analysis ${report.status.toLowerCase()}...`);
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
      }

      throw new Error('Analysis timed out. Check the submission status and try again.');
    } catch (submitError) {
      setError(submitError.message || 'Could not connect to the analysis API.');
      setStatus('');
    }
  }

  async function handleFixCode() {
    if (!sourceCode) return;

    setFixError('');
    setStatus('Fixing Python code...');

    try {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      } else {
        formData.append('code', sourceCode);
      }

      const response = await fetch(`${API_BASE_URL}/api/fix-python`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      const payload = await response.json();
      setFixedCode(payload.fixed_code || '');
      setFixError('');
      setStatus('');
      setIsAutofixPage(true);
    } catch (fixErrorMessage) {
      setFixError(fixErrorMessage.message || 'Could not fix the submitted Python code.');
      setStatus('');
    }
  }

  function handleDownloadFixedFile() {
    if (!fixedCode) return;

    const sourceName = file?.name || result?.filename || 'python_code.py';
    const downloadName = sourceName.toLowerCase().endsWith('.py')
      ? sourceName.replace(/\.py$/i, '_fixed.py')
      : `${sourceName}_fixed.py`;

    const blob = new Blob([fixedCode], { type: 'text/x-python;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = downloadName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function resetForm() {
    setFile(null);
    setStudentId('');
    setAssignmentId('');
    setSourceCode('');
    setResult(null);
    setFixedCode('');
    setFixError('');
    setIsAutofixPage(false);
    setStatus('');
    setError('');
  }

  if (result && isAutofixPage) {
    return (
      <AutofixPage
        filename={result.filename}
        fixedCode={fixedCode}
        onBackToReport={() => setIsAutofixPage(false)}
        onDownloadFixedFile={handleDownloadFixedFile}
      />
    );
  }

  if (result) {
    return (
      <ResultPage
        result={result}
        sourceCode={sourceCode}
        fixError={fixError}
        onNewSubmission={resetForm}
        onFixCode={handleFixCode}
      />
    );
  }

  return (
    <MainPage
      file={file}
      studentId={studentId}
      assignmentId={assignmentId}
      status={status}
      error={error}
      onStudentIdChange={setStudentId}
      onAssignmentIdChange={setAssignmentId}
      onFileChange={(event) => setFile(event.target.files?.[0] || null)}
      onSubmit={handleSubmit}
    />
  );
}

export default App;