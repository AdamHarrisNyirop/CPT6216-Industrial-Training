function AutofixPage({ filename, fixedCode, onBackToReport, onDownloadFixedFile }) {
  return (
    <main className="flex h-screen flex-col bg-black text-gray-100">
      <header className="flex min-h-16 shrink-0 items-center justify-between gap-4 border-b border-neutral-800 bg-black px-6 py-3">
        <div className="min-w-0">
          <h1 className="font-semibold">Fixed Python Code</h1>
          <p className="truncate text-sm text-gray-400">{filename}</p>
        </div>
        <div className="flex shrink-0 gap-2">
          <button
            className="rounded border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm font-medium text-gray-100 hover:bg-neutral-800"
            onClick={onBackToReport}
            type="button"
          >
            Back to Report
          </button>
          <button
            className="rounded bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-500 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!fixedCode}
            onClick={onDownloadFixedFile}
            type="button"
          >
            Download the Fixed File
          </button>
        </div>
      </header>
      <section className="min-h-0 flex-1 overflow-auto p-4 sm:p-6">
        <pre className="min-h-full overflow-auto rounded border border-neutral-800 bg-neutral-950 p-4 text-sm leading-6 text-gray-100 whitespace-pre-wrap">
          <code>{fixedCode}</code>
        </pre>
      </section>
    </main>
  );
}

export default AutofixPage;