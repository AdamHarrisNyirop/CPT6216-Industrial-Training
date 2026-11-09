import ReportViewer from './ReportViewer.jsx';

function ResultPage({
  result,
  sourceCode,
  fixError,
  onNewSubmission,
  onFixCode,
})

{
  return (
    <div className="flex h-screen flex-col bg-black text-gray-100">
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-neutral-800 bg-black px-6">
        <div>
          <h1 className="font-semibold text-gray-100">Python Code Result</h1>
          <p className="text-sm text-gray-400">{result.filename}</p>
        </div>
        <button
          className="rounded border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm font-medium text-gray-100 hover:bg-neutral-800"
          onClick={onNewSubmission}
          type="button"
        >
          New Submission
        </button>
      </header>
      <div className="min-h-0 flex-1">
        <ReportViewer
          code={sourceCode}
          language={result.language}
          report={result.report_json || []}
          qualityScore={result.quality_score}
        />

        <div className="border-t border-neutral-800 bg-black p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="text-lg font-semibold text-gray-100">Auto-fix</h2>
            <button
              className="rounded bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-500"
              onClick={onFixCode}
              type="button"
            >
              Fix the Python Code
            </button>
          </div>

          {fixError && (
              <p className="mb-3 rounded border border-red-900 bg-red-950 p-3 text-sm text-red-200">{fixError}</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default ResultPage;