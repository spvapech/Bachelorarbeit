import { useState, useRef, useCallback } from "react"
import { Loader2, X, FileSpreadsheet, CheckCircle2, AlertCircle, Upload } from "lucide-react"
import ModalShell from "./ModalShell"
import { API_URL } from "@/config"

/* ---- constants ---- */
const VALID_TYPES = [
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "text/csv",
  "application/csv",
]
const MAX_FILES = 2
const PREVIEW_ROWS = 10

/* ---- helpers ---- */
function isValidFile(file) {
  return (
    VALID_TYPES.includes(file.type) ||
    file.name.endsWith(".xlsx") ||
    file.name.endsWith(".xls") ||
    file.name.endsWith(".csv")
  )
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function saveImportHistory(companyId, entry) {
  if (!companyId) return
  const key = `import_history_${companyId}`
  const existing = JSON.parse(localStorage.getItem(key) || "[]")
  const updated = [entry, ...existing].slice(0, 10)
  localStorage.setItem(key, JSON.stringify(updated))
}

export function getImportHistory(companyId) {
  if (!companyId) return []
  return JSON.parse(localStorage.getItem(`import_history_${companyId}`) || "[]")
}

/* ---- sub-components ---- */

function FileChip({ file, onRemove }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-[13px]">
      <FileSpreadsheet className="w-4 h-4 text-emerald-600 flex-none" />
      <span className="flex-1 min-w-0 truncate text-slate-700">{file.name}</span>
      <span className="text-slate-400 flex-none">{formatBytes(file.size)}</span>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="text-slate-400 hover:text-slate-600 flex-none"
          aria-label="Datei entfernen"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  )
}

function ProgressBar({ value }) {
  return (
    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
      <div
        className="h-full bg-indigo-500 rounded-full transition-all duration-300"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
}

function PreviewTable({ columns, rows }) {
  const visibleCols = columns.slice(0, 8)
  const truncated = columns.length > 8

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full text-[12px] text-left">
        <thead className="bg-slate-50 border-b border-slate-200">
          <tr>
            {visibleCols.map((col) => (
              <th
                key={col}
                className="px-3 py-2 font-medium text-slate-600 truncate max-w-[160px]"
                title={String(col)}
              >
                {String(col).length > 22 ? String(col).slice(0, 22) + "…" : String(col)}
              </th>
            ))}
            {truncated && (
              <th className="px-3 py-2 text-slate-400 italic">+{columns.length - 8} more…</th>
            )}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className={ri % 2 === 0 ? "bg-white" : "bg-slate-50"}>
              {visibleCols.map((_, ci) => {
                const val = row[ci]
                return (
                  <td
                    key={ci}
                    className="px-3 py-1.5 text-slate-700 truncate max-w-[160px]"
                    title={val != null ? String(val) : ""}
                  >
                    {val != null ? String(val).slice(0, 40) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                )
              })}
              {truncated && <td className="px-3 py-1.5 text-slate-300">…</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ================================================================
   ImportModal — main export
   ================================================================ */
export default function ImportModal({ open, onOpenChange, companyId, companyName, onImportSuccess }) {
  const [step, setStep] = useState("select") // select | preview | uploading | success | error
  const [files, setFiles] = useState([])
  const [dragActive, setDragActive] = useState(false)
  const [validationError, setValidationError] = useState("")

  /* preview state */
  const [previews, setPreviews] = useState([]) // array of { filename, columns, rows } per file
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [previewError, setPreviewError] = useState("")

  /* upload state */
  const [uploadProgress, setUploadProgress] = useState([]) // per-file progress 0-100
  const [uploadResults, setUploadResults] = useState([]) // per-file { ok, message }
  const [overallError, setOverallError] = useState("")

  /* success */
  const [successTimestamp, setSuccessTimestamp] = useState(null)
  const [importedCount, setImportedCount] = useState(0)

  const fileInputRef = useRef(null)

  /* ---- reset on close ---- */
  const handleOpenChange = useCallback((v) => {
    if (!v) {
      setStep("select")
      setFiles([])
      setDragActive(false)
      setValidationError("")
      setPreviews([])
      setPreviewError("")
      setUploadProgress([])
      setUploadResults([])
      setOverallError("")
      setSuccessTimestamp(null)
      setImportedCount(0)
    }
    onOpenChange(v)
  }, [onOpenChange])

  /* ---- file handling ---- */
  function addFiles(incoming) {
    setValidationError("")
    const valid = incoming.filter(isValidFile)
    const invalid = incoming.filter((f) => !isValidFile(f))
    if (invalid.length) {
      setValidationError("Nur Excel- oder CSV-Dateien (.xlsx, .xls oder .csv) sind erlaubt.")
      return
    }
    const combined = [...files, ...valid]
    if (combined.length > MAX_FILES) {
      setValidationError(`Maximal ${MAX_FILES} Dateien erlaubt.`)
      return
    }
    setFiles(combined)
  }

  function removeFile(idx) {
    setFiles((f) => f.filter((_, i) => i !== idx))
    setValidationError("")
  }

  const handleDrag = (e) => {
    e.preventDefault(); e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true)
    else if (e.type === "dragleave") setDragActive(false)
  }

  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation()
    setDragActive(false)
    addFiles(Array.from(e.dataTransfer.files || []))
  }

  const handleFileInput = (e) => {
    addFiles(Array.from(e.target.files || []))
    e.target.value = ""
  }

  /* ---- preview ---- */
  async function fetchPreviews() {
    setLoadingPreview(true)
    setPreviewError("")
    try {
      const results = await Promise.all(
        files.map(async (file) => {
          const fd = new FormData()
          fd.append("file", file)
          const res = await fetch(`${API_URL}/preview-excel`, { method: "POST", body: fd })
          if (!res.ok) {
            const err = await res.json().catch(() => ({}))
            throw new Error(err.detail || `Fehler bei ${file.name}`)
          }
          return res.json()
        })
      )
      setPreviews(results)
      setStep("preview")
    } catch (err) {
      setPreviewError(err.message || "Vorschau konnte nicht geladen werden.")
    } finally {
      setLoadingPreview(false)
    }
  }

  /* ---- upload via XHR for progress ---- */
  function uploadFileXHR(file, companyId, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open("POST", `${API_URL}/upload-excel`)
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
      }
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          onProgress(100)
          resolve({ ok: true, filename: file.name })
        } else {
          let msg = `HTTP ${xhr.status}`
          try { msg = JSON.parse(xhr.responseText)?.detail || msg } catch {}
          reject(new Error(msg))
        }
      }
      xhr.onerror = () => reject(new Error("Netzwerkfehler"))
      const fd = new FormData()
      fd.append("file", file)
      fd.append("company_id", companyId)
      xhr.send(fd)
    })
  }

  async function startUpload() {
    setStep("uploading")
    setUploadProgress(files.map(() => 0))
    setUploadResults([])
    setOverallError("")

    const results = []
    let anyFailed = false

    for (let i = 0; i < files.length; i++) {
      try {
        await uploadFileXHR(files[i], companyId, (pct) => {
          setUploadProgress((prev) => {
            const next = [...prev]
            next[i] = pct
            return next
          })
        })
        results.push({ ok: true, filename: files[i].name })
      } catch (err) {
        results.push({ ok: false, filename: files[i].name, message: err.message })
        anyFailed = true
      }
    }

    setUploadResults(results)

    const successCount = results.filter((r) => r.ok).length
    if (successCount > 0) {
      const ts = new Date().toISOString()
      setSuccessTimestamp(ts)
      setImportedCount(successCount)
      saveImportHistory(companyId, {
        timestamp: ts,
        files: results.filter((r) => r.ok).map((r) => r.filename),
      })
      onImportSuccess?.()
    }

    if (anyFailed && successCount === 0) {
      setOverallError("Import fehlgeschlagen. Bitte überprüfen Sie die Dateien und versuchen Sie es erneut.")
      setStep("error")
    } else {
      setStep("success")
    }
  }

  /* ---- tone / icon for ModalShell ---- */
  const modalTone = step === "success" ? "good" : step === "error" ? "bad" : "info"
  const stepTitle = {
    select: "Daten importieren",
    preview: "Datenvorschau",
    uploading: "Wird hochgeladen…",
    success: "Import erfolgreich",
    error: "Import fehlgeschlagen",
  }[step] ?? "Daten importieren"

  const stepSubtitle = companyName
    ? { select: companyName, preview: companyName, uploading: companyName, success: companyName, error: companyName }[step]
    : undefined

  /* ---- footer ---- */
  const footer = (() => {
    if (step === "select") return (
      <>
        <button
          className="ds-btn ds-btn-secondary"
          onClick={() => handleOpenChange(false)}
        >
          Abbrechen
        </button>
        <button
          className="ds-btn ds-btn-primary"
          disabled={files.length === 0 || loadingPreview}
          onClick={fetchPreviews}
        >
          {loadingPreview ? (
            <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Vorschau laden…</>
          ) : (
            "Vorschau anzeigen →"
          )}
        </button>
      </>
    )

    if (step === "preview") return (
      <>
        <button className="ds-btn ds-btn-secondary" onClick={() => setStep("select")}>
          ← Zurück
        </button>
        <button className="ds-btn ds-btn-primary" onClick={startUpload}>
          Jetzt importieren
        </button>
      </>
    )

    if (step === "uploading") return (
      <span className="text-[12px] text-slate-500 ml-auto">Bitte warten…</span>
    )

    if (step === "success") return (
      <button className="ds-btn ds-btn-primary ml-auto" onClick={() => handleOpenChange(false)}>
        Schließen
      </button>
    )

    if (step === "error") return (
      <>
        <button className="ds-btn ds-btn-secondary" onClick={() => setStep("select")}>
          Erneut versuchen
        </button>
        <button className="ds-btn ds-btn-primary ml-auto" onClick={() => handleOpenChange(false)}>
          Schließen
        </button>
      </>
    )
  })()

  /* ---- body ---- */
  const body = (() => {
    /* SELECT */
    if (step === "select") return (
      <div className="flex flex-col gap-4">
        {/* Drop zone */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={[
            "rounded-xl border-2 border-dashed cursor-pointer transition-colors",
            "flex flex-col items-center justify-center gap-2 py-10 px-6 text-center select-none",
            dragActive
              ? "border-indigo-400 bg-indigo-50"
              : "border-slate-200 bg-slate-50 hover:border-indigo-300 hover:bg-indigo-50/40",
          ].join(" ")}
        >
          <Upload className={`w-8 h-8 ${dragActive ? "text-indigo-500" : "text-slate-400"}`} />
          <p className="text-[13px] font-medium text-slate-700">
            Dateien hier ablegen oder <span className="text-indigo-600">auswählen</span>
          </p>
          <p className="text-[11px] text-slate-400">.xlsx / .xls / .csv · max. {MAX_FILES} Dateien</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls,.csv"
            multiple
            className="hidden"
            onChange={handleFileInput}
          />
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="flex flex-col gap-2">
            {files.map((file, i) => (
              <FileChip key={i} file={file} onRemove={() => removeFile(i)} />
            ))}
          </div>
        )}

        {/* Validation error */}
        {validationError && (
          <p className="text-[12px] text-rose-600 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 flex-none" />
            {validationError}
          </p>
        )}

        {/* Preview fetch error */}
        {previewError && (
          <p className="text-[12px] text-rose-600 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 flex-none" />
            {previewError}
          </p>
        )}
      </div>
    )

    /* PREVIEW */
    if (step === "preview") return (
      <div className="flex flex-col gap-5">
        <p className="text-[13px] text-slate-600">
          Vorschau der ersten {PREVIEW_ROWS} Zeilen. Überprüfen Sie die Daten, bevor Sie den Import starten.
        </p>
        {previews.map((preview, i) => (
          <div key={i} className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
              <span className="text-[13px] font-medium text-slate-700">{preview.filename}</span>
              <span className="text-[11px] text-slate-400 ml-auto">{preview.total_columns} Spalten</span>
            </div>
            <PreviewTable columns={preview.columns} rows={preview.rows} />
          </div>
        ))}
      </div>
    )

    /* UPLOADING */
    if (step === "uploading") return (
      <div className="flex flex-col gap-5">
        {files.map((file, i) => (
          <div key={i} className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-[13px]">
              <div className="flex items-center gap-2 min-w-0">
                <FileSpreadsheet className="w-4 h-4 text-slate-400 flex-none" />
                <span className="truncate text-slate-700">{file.name}</span>
              </div>
              <span className="text-slate-500 flex-none ml-3">{uploadProgress[i] ?? 0}%</span>
            </div>
            <ProgressBar value={uploadProgress[i] ?? 0} />
          </div>
        ))}
      </div>
    )

    /* SUCCESS */
    if (step === "success") return (
      <div className="flex flex-col gap-4">
        <div className="flex flex-col items-center gap-3 py-6">
          <CheckCircle2 className="w-12 h-12 text-emerald-500" />
          <p className="text-[15px] font-semibold text-slate-800">
            {importedCount} {importedCount === 1 ? "Datei" : "Dateien"} erfolgreich importiert
          </p>
          {successTimestamp && (
            <p className="text-[12px] text-slate-400">
              {new Date(successTimestamp).toLocaleString("de-DE", {
                day: "2-digit", month: "2-digit", year: "numeric",
                hour: "2-digit", minute: "2-digit",
              })}
            </p>
          )}
        </div>

        {/* Per-file results */}
        <div className="flex flex-col gap-2">
          {uploadResults.map((r, i) => (
            <div
              key={i}
              className={[
                "flex items-center gap-2 px-3 py-2 rounded-lg text-[12px]",
                r.ok ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700",
              ].join(" ")}
            >
              {r.ok
                ? <CheckCircle2 className="w-3.5 h-3.5 flex-none" />
                : <AlertCircle className="w-3.5 h-3.5 flex-none" />}
              <span className="flex-1 min-w-0 truncate">{r.filename}</span>
              {!r.ok && <span className="flex-none">{r.message}</span>}
            </div>
          ))}
        </div>
      </div>
    )

    /* ERROR */
    if (step === "error") return (
      <div className="flex flex-col gap-4">
        <div className="flex flex-col items-center gap-3 py-6">
          <AlertCircle className="w-12 h-12 text-rose-500" />
          <p className="text-[15px] font-semibold text-slate-800">Import fehlgeschlagen</p>
          {overallError && (
            <p className="text-[13px] text-slate-500 text-center max-w-sm">{overallError}</p>
          )}
        </div>
        <div className="flex flex-col gap-2">
          {uploadResults.map((r, i) => (
            <div
              key={i}
              className={[
                "flex items-center gap-2 px-3 py-2 rounded-lg text-[12px]",
                r.ok ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700",
              ].join(" ")}
            >
              {r.ok
                ? <CheckCircle2 className="w-3.5 h-3.5 flex-none" />
                : <AlertCircle className="w-3.5 h-3.5 flex-none" />}
              <span className="flex-1 min-w-0 truncate">{r.filename}</span>
              {!r.ok && <span className="flex-none">{r.message}</span>}
            </div>
          ))}
        </div>
      </div>
    )
  })()

  return (
    <ModalShell
      open={open}
      onOpenChange={handleOpenChange}
      tone={modalTone}
      eyebrow="Datenimport"
      title={stepTitle}
      subtitle={stepSubtitle}
      size="md"
      footer={footer}
    >
      {body}
    </ModalShell>
  )
}
