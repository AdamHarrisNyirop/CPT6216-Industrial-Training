function MainPage({
  file,
  studentId,
  assignmentId,
  status,
  error,
  onStudentIdChange,
  onAssignmentIdChange,
  onFileChange,
  onSubmit,
})

{
  return (
    <main className="min-h-screen bg-black px-4 py-10 text-gray-100">
      <section className="mx-auto max-w-2xl">
        <h1 className="text-2xl font-bold">Automatic Code Quality Report</h1>
        <p className="mt-2 text-sm text-gray-400">
          Submit a Python file to run the analysis service.
        </p>
        <form className="mt-6 space-y-5 rounded border border-neutral-800 bg-neutral-950 p-6 shadow-sm" onSubmit={onSubmit}>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm font-medium">
              Student ID
              <input
                className="mt-1 block w-full rounded border border-neutral-700 bg-black px-3 py-2 font-normal text-gray-100 focus:border-gray-400 focus:outline-none"
                onChange={(event) => onStudentIdChange(event.target.value)}
                required
                value={studentId}
              />
            </label>
            <label className="block text-sm font-medium">
              Assignment ID
              <input
                className="mt-1 block w-full rounded border border-neutral-700 bg-black px-3 py-2 font-normal text-gray-100 focus:border-gray-400 focus:outline-none"
                onChange={(event) => onAssignmentIdChange(event.target.value)}
                required
                value={assignmentId}
              />
            </label>
          </div>

          <label className="block text-sm font-medium">
            Python Source File
            <input
              accept=".py,text/x-python"
              className="mt-1 block w-full rounded border border-neutral-700 bg-black px-3 py-2 font-normal text-gray-100 file:mr-3 file:rounded file:border-0 file:bg-neutral-800 file:px-3 file:py-1 file:text-gray-100 hover:file:bg-neutral-700"
              onChange={onFileChange}
              required
              type="file"
            />
          </label>

          {error && (
            <p className="rounded border border-red-900 bg-red-950 p-3 text-sm text-red-200" role="alert">
              {error}
            </p>
          )}
          {status && <p className="text-sm text-gray-400" role="status">{status}</p>}

          <button
            className="rounded bg-neutral-800 px-4 py-2 font-medium text-gray-100 hover:bg-neutral-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!file || Boolean(status)}
            type="submit"
          >
            {status ? 'Working...' : 'Analyze File'}
          </button>
        </form>
      </section>
    </main>
  );
}

export default MainPage;