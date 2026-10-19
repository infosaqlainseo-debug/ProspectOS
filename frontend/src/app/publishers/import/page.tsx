"use client"
import { useState } from "react"

export default function ImportPage() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<any>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append("file", file)
      const res = await fetch("http://127.0.0.1:8000/publishers/import/preview", {
        method: "POST",
        body: formData
      })
      if (!res.ok) throw new Error(await res.text())
      setPreview(await res.json())
    } catch (e: any) {
      alert("Upload failed: " + e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCommit = async () => {
    if (!preview) return
    setLoading(true)
    try {
      // In a real implementation we would have a mapping UI.
      // Here we assume mapping is hardcoded or auto-detected for the demo.
      const payload = {
        batch_id: "00000000-0000-0000-0000-000000000000", // placeholder
        mapping: {
          url_column: preview.headers.includes("Website") ? "Website" : preview.headers[0],
          publisher_name_column: preview.headers.includes("Publisher Name") ? "Publisher Name" : undefined,
          price_column: preview.headers.includes("Price") ? "Price" : undefined,
          currency_column: preview.headers.includes("Currency") ? "Currency" : undefined
        },
        rows: preview.preview_rows // the actual endpoint expects rows. In production, read whole file.
      }
      const res = await fetch("http://127.0.0.1:8000/publishers/import/commit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
      if (!res.ok) throw new Error(await res.text())
      setResult(await res.json())
    } catch (e: any) {
      alert("Commit failed: " + e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
        <div className="max-w-4xl mx-auto bg-white p-8 rounded-xl shadow-sm border border-gray-200">
          <h1 className="text-2xl font-bold mb-6">Import Publisher Inventory</h1>
          
          {!preview && !result && (
            <div className="space-y-4">
              <input 
                type="file" 
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
              <button 
                onClick={handleUpload}
                disabled={!file || loading}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {loading ? "Uploading..." : "Upload & Preview"}
              </button>
            </div>
          )}

          {preview && !result && (
            <div className="space-y-6">
              <div className="bg-blue-50 p-4 rounded-md text-blue-800">
                Found {preview.headers.length} columns in {preview.file_name}.
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr>
                      {preview.headers.map((h: string) => (
                        <th key={h} className="px-4 py-2 text-left text-gray-600 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.preview_rows.map((r: any, i: number) => (
                      <tr key={i}>
                        {preview.headers.map((h: string) => (
                          <td key={h} className="px-4 py-2 border-t">{r[h]}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <button 
                onClick={handleCommit}
                disabled={loading}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? "Importing..." : "Confirm & Import"}
              </button>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <div className="p-6 bg-green-50 rounded-md border border-green-200">
                <h3 className="text-lg font-medium text-green-900 mb-2">Import Complete</h3>
                <ul className="space-y-1 text-sm text-green-800">
                  <li>Total Rows: {result.total_rows}</li>
                  <li>Created: {result.created_records}</li>
                  <li>Updated: {result.updated_records}</li>
                  <li>Failed: {result.failed_rows}</li>
                </ul>
              </div>
              <a href="/publishers" className="text-indigo-600 hover:underline">
                &larr; Back to Publishers
              </a>
            </div>
          )}
        </div>
    </div>
  )
}
