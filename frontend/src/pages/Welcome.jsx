import { useEffect, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { FileSpreadsheet, ArrowRight, Building2, Upload as UploadIcon, Loader2, X } from "lucide-react"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import { WorkPulseLogo } from "@/components/WorkPulseLogo"
import { Button } from "@/components/ui/button"
import { API_URL } from "../config"


export default function Welcome() {
    const [mode, setMode] = useState(1) // 1, 2, or 3 companies
    
    // State for each company (array index = company index)
    const [companies, setCompanies] = useState([
        { companyQuery: "", companyId: null, selectedCompany: null, files: [], isChecked: false, existsInDB: false },
        { companyQuery: "", companyId: null, selectedCompany: null, files: [], isChecked: false, existsInDB: false },
        { companyQuery: "", companyId: null, selectedCompany: null, files: [], isChecked: false, existsInDB: false }
    ])

    const [uploading, setUploading] = useState(false)
    const [checking, setChecking] = useState(null) // Index of company being checked
    const [deletingData, setDeletingData] = useState(null) // Index of company whose data is being deleted
    const [deletingCompany, setDeletingCompany] = useState(null) // Index of company being deleted
    const [error, setError] = useState("")
    const [dragActive, setDragActive] = useState(null) // Index of active drag zone
    const navigate = useNavigate()
    const location = useLocation()

    useEffect(() => {
        const prefillName = location.state?.prefillCompanyName
        if (!prefillName) return

        const trimmedName = String(prefillName).trim()
        if (!trimmedName) return

        setMode(1)
        setCompanies((prev) => {
            const next = [...prev]
            next[0] = {
                ...next[0],
                companyQuery: trimmedName,
                companyId: null,
                selectedCompany: null,
                existsInDB: false,
                isChecked: false,
                files: [],
            }
            return next
        })
    }, [location.state])

    const getCompanyName = (company) => {
        return (company.companyQuery || company.selectedCompany?.name || "").trim()
    }

    const buildSelectedCompanies = (list) => {
        return list
            .map((company) => {
                const id = company.companyId
                const name = getCompanyName(company)
                if (!id || !name) return null
                return { id, name }
            })
            .filter(Boolean)
    }

    const navigateToAnalysis = (selectedCompanies) => {
        if (selectedCompanies.length === 1) {
            navigate("/dashboard", {
                state: {
                    companyId: selectedCompanies[0].id,
                    companyName: selectedCompanies[0].name,
                },
            })
            return
        }

        if (selectedCompanies.length >= 2) {
            navigate("/compare", { state: { companies: selectedCompanies } })
        }
    }

    // Update company state helper
    const updateCompany = (index, updates) => {
        setCompanies(prev => {
            const newCompanies = [...prev]
            newCompanies[index] = { ...newCompanies[index], ...updates }
            return newCompanies
        })
    }

    const removeFile = (companyIndex, fileIndex) => {
        const company = companies[companyIndex]
        const updatedFiles = company.files.filter((_, idx) => idx !== fileIndex)
        updateCompany(companyIndex, { files: updatedFiles })
    }

    const handleCreateNewCompany = (companyIndex, companyName) => {
        // Direkt als neue Firma markieren und Upload-Bereich öffnen
        updateCompany(companyIndex, {
            companyQuery: companyName,
            existsInDB: false,
            isChecked: true,
            selectedCompany: null,
            companyId: null
        })
    }

    const handleFileChange = (companyIndex, e) => {
        const selectedFiles = Array.from(e.target.files || [])
        
        if (selectedFiles.length === 0) return
        
        const existingFiles = companies[companyIndex].files
        const combinedFiles = [...existingFiles, ...selectedFiles]
        
        // Max 2 files
        if (combinedFiles.length > 2) {
            setError("Maximal 2 Dateien pro Firma erlaubt")
            return
        }
        
        // Validate file types
        const validTypes = [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv',
            'application/csv',
        ]

        for (const file of selectedFiles) {
            if (!validTypes.includes(file.type) && !file.name.endsWith('.xlsx') && !file.name.endsWith('.xls') && !file.name.endsWith('.csv')) {
                setError("Bitte wählen Sie nur Excel- oder CSV-Dateien (.xlsx, .xls oder .csv)")
                return
            }
        }
        
        updateCompany(companyIndex, { files: combinedFiles })
        setError("")
    }
    
    const handleDrag = (e, companyIndex) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(companyIndex)
        } else if (e.type === "dragleave") {
            setDragActive(null)
        }
    }
    
    const handleDrop = (e, companyIndex) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(null)
        
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const droppedFiles = Array.from(e.dataTransfer.files)
            const existingFiles = companies[companyIndex].files
            const combinedFiles = [...existingFiles, ...droppedFiles]
            
            // Max 2 files
            if (combinedFiles.length > 2) {
                setError("Maximal 2 Dateien pro Firma erlaubt")
                return
            }
            
            const validTypes = [
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/csv',
                'application/csv',
            ]

            for (const file of droppedFiles) {
                if (!validTypes.includes(file.type) && !file.name.endsWith('.xlsx') && !file.name.endsWith('.xls') && !file.name.endsWith('.csv')) {
                    setError("Bitte wählen Sie nur Excel- oder CSV-Dateien (.xlsx, .xls oder .csv)")
                    return
                }
            }
            
            updateCompany(companyIndex, { files: combinedFiles })
            setError("")
        }
    }

    const handleCompanySelect = (companyIndex, company) => {
        updateCompany(companyIndex, {
            selectedCompany: company,
            companyId: company ? company.id : null,
            existsInDB: company ? true : false,
            isChecked: company ? true : false
        })
    }

    // Check if company exists in database
    const handleCheckCompany = async (companyIndex) => {
        const company = companies[companyIndex]
        
        if (!company.companyQuery.trim()) {
            setError(`Bitte geben Sie einen Firmennamen für Firma ${companyIndex + 1} ein.`)
            return
        }

        setChecking(companyIndex)
        setError("")

        try {
            const response = await fetch(`${API_URL}/companies`)
            if (!response.ok) throw new Error("Fehler beim Laden der Firmen")
            
            const allCompanies = await response.json()
            const match = allCompanies.find(
                (c) => c.name.toLowerCase() === company.companyQuery.trim().toLowerCase()
            )

            if (match) {
                // Company exists in database
                updateCompany(companyIndex, {
                    companyId: match.id,
                    selectedCompany: match,
                    existsInDB: true,
                    isChecked: true
                })
            } else {
                // Company does not exist, needs upload
                updateCompany(companyIndex, {
                    existsInDB: false,
                    isChecked: true
                })
            }
        } catch (err) {
            setError(`Fehler bei der Überprüfung von Firma ${companyIndex + 1}`)
        } finally {
            setChecking(null)
        }
    }
    // Delete company data and allow re-upload
    const handleDeleteCompanyData = async (companyIndex) => {
        const company = companies[companyIndex]
        
        if (!company.companyId) {
            setError("Keine Firma-ID gefunden")
            return
        }

        const confirmed = window.confirm(
            `Möchten Sie wirklich alle Daten von "${company.companyQuery}" löschen?\n\nDie Daten werden permanent gelöscht und können nicht wiederhergestellt werden.`
        )

        if (!confirmed) return

        setDeletingData(companyIndex)
        setError("")

        try {
            const response = await fetch(`${API_URL}/companies/${company.companyId}/data`, {
                method: "DELETE"
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || "Fehler beim Löschen der Firmendaten")
            }

            const result = await response.json()
            console.log("Firmendaten gelöscht:", result)

            // Reset company state to allow new upload
            updateCompany(companyIndex, {
                existsInDB: false,
                files: []
            })
        } catch (err) {
            setError(err.message || "Fehler beim Löschen der Firmendaten")
        } finally {
            setDeletingData(null)
        }
    }

    const handleDeleteCompany = async (companyIndex) => {
        const company = companies[companyIndex]

        if (!company.companyId) {
            setError("Keine Firma-ID gefunden")
            return
        }

        const companyName = getCompanyName(company) || company.companyQuery
        const confirmed = window.confirm(
            `Möchten Sie wirklich die Firma "${companyName}" löschen?\n\nAlle Daten werden permanent gelöscht und können nicht wiederhergestellt werden.`
        )

        if (!confirmed) return

        setDeletingCompany(companyIndex)
        setError("")

        try {
            const dataResponse = await fetch(`${API_URL}/companies/${company.companyId}/data`, {
                method: "DELETE",
            })

            if (!dataResponse.ok) {
                const errorData = await dataResponse.json().catch(() => ({}))
                throw new Error(errorData.detail || "Fehler beim Löschen der Firmendaten")
            }

            const companyResponse = await fetch(`${API_URL}/companies/${company.companyId}`, {
                method: "DELETE",
            })

            if (!companyResponse.ok) {
                const errorData = await companyResponse.json().catch(() => ({}))
                throw new Error(errorData.detail || "Fehler beim Löschen der Firma")
            }

            updateCompany(companyIndex, {
                companyQuery: "",
                companyId: null,
                selectedCompany: null,
                files: [],
                isChecked: false,
                existsInDB: false,
            })

            setError("")
        } catch (err) {
            setError(err.message || "Fehler beim Löschen der Firma")
        } finally {
            setDeletingCompany(null)
        }
    }
    const handleUpload = async () => {
        // Validate that all active companies are checked
        const activeCompanies = companies.slice(0, mode)
        
        for (let i = 0; i < activeCompanies.length; i++) {
            const company = activeCompanies[i]
            if (!company.isChecked) {
                setError(`Bitte prüfen Sie zuerst Firma ${i + 1}.`)
                return
            }
            // Only require files if company doesn't exist in DB
            if (!company.existsInDB && company.files.length < 2) {
                setError(`Bitte wählen Sie 2 Dateien für Firma ${i + 1} aus.`)
                return
            }
        }

        setUploading(true)
        setError("")

        const createdCompanyIds = []
        const existingCompanyIds = []
        const resolvedCompanies = []

        try {
            // Process each company
            for (let i = 0; i < activeCompanies.length; i++) {
                const company = activeCompanies[i]
                let finalCompanyId = company.companyId
                const companyName = getCompanyName(company)
                
                // If company exists in DB, just track it
                if (company.existsInDB) {
                    existingCompanyIds.push({ id: finalCompanyId, name: companyName })
                    resolvedCompanies.push({ id: finalCompanyId, name: companyName })
                    continue
                }
                
                // Create new company
                if (!finalCompanyId) {
                    const createRes = await fetch(`${API_URL}/companies/`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ name: company.companyQuery.trim() })
                    })
                    
                    if (!createRes.ok) {
                        const errorData = await createRes.json().catch(() => ({}))
                        throw new Error(errorData.detail || `Fehler beim Erstellen der Firma ${i + 1}`)
                    }
                    
                    const newCompany = await createRes.json()
                    finalCompanyId = newCompany.id
                    createdCompanyIds.push(finalCompanyId)
                }
                
                // Upload files for new companies
                for (let fileIndex = 0; fileIndex < company.files.length; fileIndex++) {
                    const file = company.files[fileIndex]
                    const formData = new FormData()
                    formData.append("file", file)
                    formData.append("company_id", String(finalCompanyId))

                    const response = await fetch(`${API_URL}/upload-excel`, {
                        method: "POST",
                        body: formData,
                    })

                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}))
                        throw new Error(errorData.detail || `Upload fehlgeschlagen für Firma ${i + 1}, Datei ${fileIndex + 1}`)
                    }
                }

                resolvedCompanies.push({ id: finalCompanyId, name: companyName })
            }

            console.log("Alle Uploads erfolgreich")

            // Clear any previous errors
            setError("")

            navigateToAnalysis(resolvedCompanies)
        } catch (err) {
            // Rollback: Delete all created companies
            for (const companyId of createdCompanyIds) {
                try {
                    await fetch(`${API_URL}/companies/${companyId}`, {
                        method: "DELETE",
                    })
                    console.log(`Rollback: Firma ${companyId} wurde gelöscht`)
                } catch (deleteErr) {
                    console.error("Fehler beim Rollback:", deleteErr)
                }
            }
            
            setError(err.message || "Fehler beim Hochladen der Dateien")
        } finally {
            setUploading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4 py-12"
             style={{ background: 'linear-gradient(160deg, #05223e 0%, #0a3158 60%, #0d3d6e 100%)' }}>
            <div className="w-full max-w-6xl">

                {/* Welcome Header */}
                <div className="text-center mb-10">
                    {/* Brand mark */}
                    <div className="mb-6">
                        <WorkPulseLogo variant="welcome" />
                    </div>
                    <p style={{ font: '400 16px/1.6 var(--font-sans)', color: 'rgba(255,255,255,0.65)', maxWidth: 520, margin: '0 auto' }}>
                        KI-gestützte Analyse von Arbeitgeberbewertungen &mdash; Firmen verstehen, vergleichen und verbessern.
                    </p>
                </div>

                {/* Mode Selection */}
                <div className="mb-8">
                    <p style={{ textAlign: 'center', marginBottom: 16, font: '500 12px/1 var(--font-mono)', letterSpacing: '0.06em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.5)' }}>
                        Wie viele Firmen analysieren?
                    </p>
                    <div className="flex justify-center gap-3">
                        {[1, 2, 3].map((n) => (
                            <button
                                key={n}
                                onClick={() => setMode(n)}
                                style={{
                                    padding: '12px 28px',
                                    borderRadius: 10,
                                    font: '600 14px/1 var(--font-sans)',
                                    border: `1px solid ${mode === n ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.15)'}`,
                                    background: mode === n ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.06)',
                                    color: mode === n ? '#fff' : 'rgba(255,255,255,0.6)',
                                    cursor: 'pointer',
                                    transition: 'all 150ms ease',
                                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                                }}
                            >
                                <div style={{ display: 'flex', gap: 3 }}>
                                    {Array.from({ length: n }).map((_, i) => (
                                        <Building2 key={i} className="h-5 w-5" />
                                    ))}
                                </div>
                                {n} Firma{n > 1 ? 'en' : ''}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Company Upload Cards */}
                <div className={`grid gap-5 mb-6 ${mode === 1 ? 'grid-cols-1 max-w-xl mx-auto' : mode === 2 ? 'grid-cols-2' : 'grid-cols-3'}`}>
                    {companies.slice(0, mode).map((company, index) => (
                        <div key={index} style={{
                            background: 'rgba(255,255,255,0.07)',
                            border: '1px solid rgba(255,255,255,0.15)',
                            borderRadius: 12,
                            padding: '20px',
                            backdropFilter: 'blur(12px)',
                        }}>
                            <div style={{ marginBottom: 16 }}>
                                <span style={{ font: '500 11px/1 var(--font-mono)', letterSpacing: '0.06em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', marginBottom: 4, display: 'block' }}>
                                    Firma {index + 1}
                                </span>
                            </div>

                            <div className="space-y-4">
                                {/* Company Name Input */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300">
                                        Firmenname <span className="text-red-400">*</span>
                                    </label>
                                    <CompanySearchSelect
                                        value={company.companyQuery}
                                        onValueChange={(value) => updateCompany(index, { companyQuery: value, isChecked: false })}
                                        onCompanySelect={(comp) => handleCompanySelect(index, comp)}
                                        onCreateNew={(companyName) => handleCreateNewCompany(index, companyName)}
                                        variant="dark"
                                    />
                                </div>

                                {/* Check Company Button */}
                                {!company.isChecked && (
                                    <button
                                        onClick={() => handleCheckCompany(index)}
                                        disabled={checking === index || !company.companyQuery.trim()}
                                        style={{
                                            width: '100%', height: 36,
                                            borderRadius: 8,
                                            font: '600 13px/1 var(--font-sans)',
                                            background: checking === index || !company.companyQuery.trim() ? 'rgba(255,255,255,0.1)' : 'rgba(37,99,235,0.8)',
                                            color: '#fff',
                                            border: '1px solid rgba(255,255,255,0.2)',
                                            cursor: checking === index || !company.companyQuery.trim() ? 'not-allowed' : 'pointer',
                                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                                            transition: 'background 150ms ease',
                                        }}
                                    >
                                        {checking === index ? (
                                            <><Loader2 className="h-4 w-4 animate-spin" /> Prüfe…</>
                                        ) : (
                                            "Firma prüfen"
                                        )}
                                    </button>
                                )}

                                {/* Status after check */}
                                {company.isChecked && (
                                    <>
                                        <div style={{
                                            padding: '8px 12px',
                                            borderRadius: 8,
                                            background: company.existsInDB ? 'rgba(16,185,129,0.15)' : 'rgba(59,130,246,0.15)',
                                            border: `1px solid ${company.existsInDB ? 'rgba(16,185,129,0.4)' : 'rgba(59,130,246,0.4)'}`,
                                            font: '500 12px/1.4 var(--font-sans)',
                                            color: company.existsInDB ? '#6ee7b7' : '#93c5fd',
                                        }}>
                                            {company.existsInDB
                                                ? `✓ Firma "${company.companyQuery}" existiert bereits`
                                                : `Neue Firma "${company.companyQuery}" – Dateien hochladen`}
                                        </div>
                                        
                                        {/* Button to replace existing company data */}
                                        {company.existsInDB && (
                                            <div className="flex flex-wrap items-center justify-center gap-6">
                                                <Button
                                                    onClick={() => handleDeleteCompanyData(index)}
                                                    disabled={deletingData === index}
                                                    className="
                                                        bg-transparent hover:bg-transparent
                                                        p-0 h-auto
                                                        cursor-default
                                                        active:scale-[0.99] transition-transform
                                                        disabled:opacity-60 disabled:cursor-not-allowed
                                                    "
                                                >
                                                    {deletingData === index ? (
                                                        <span className="inline-flex items-center cursor-default">
                                                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                                            Lösche Daten...
                                                        </span>
                                                    ) : (
                                                        <span
                                                            className="
                                                                text-blue-400 underline underline-offset-4
                                                                hover:text-blue-300
                                                                cursor-pointer
                                                                disabled:cursor-not-allowed
                                                            "
                                                        >
                                                            Neue Daten hochladen ?
                                                        </span>
                                                    )}
                                                </Button>

                                                <Button
                                                    onClick={() => handleDeleteCompany(index)}
                                                    disabled={deletingCompany === index}
                                                    className="
                                                        bg-transparent hover:bg-transparent
                                                        p-0 h-auto
                                                        cursor-default
                                                        active:scale-[0.99] transition-transform
                                                        disabled:opacity-60 disabled:cursor-not-allowed
                                                    "
                                                >
                                                    {deletingCompany === index ? (
                                                        <span className="inline-flex items-center cursor-default">
                                                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                                            Lösche Firma...
                                                        </span>
                                                    ) : (
                                                        <span
                                                            className="
                                                                text-red-400 underline underline-offset-4
                                                                hover:text-red-300
                                                                cursor-pointer
                                                                disabled:cursor-not-allowed
                                                            "
                                                        >
                                                            Firma "{getCompanyName(company)}" löschen ?
                                                        </span>
                                                    )}
                                                </Button>
                                            </div>

                                            
                                        )}
                                    </>
                                )}

                                {/* File Uploads - only show if company doesn't exist in DB */}
                                {company.isChecked && !company.existsInDB && (
                                    <div 
                                        className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors ${
                                            dragActive === index
                                                ? 'border-blue-400 bg-blue-900/20' 
                                                : 'border-slate-600 hover:border-blue-500'
                                        }`}
                                        onDragEnter={(e) => handleDrag(e, index)}
                                        onDragLeave={(e) => handleDrag(e, index)}
                                        onDragOver={(e) => handleDrag(e, index)}
                                        onDrop={(e) => handleDrop(e, index)}
                                    >
                                        <input
                                            type="file"
                                            id={`file-upload-${index}`}
                                            accept=".xlsx,.xls,.csv"
                                            multiple
                                            onChange={(e) => handleFileChange(index, e)}
                                            className="hidden"
                                        />
                                        <label
                                            htmlFor={`file-upload-${index}`}
                                            className="cursor-pointer flex flex-col items-center gap-3"
                                        >
                                            <div className="h-16 w-16 rounded-full bg-blue-900 flex items-center justify-center">
                                                <FileSpreadsheet className="h-8 w-8 text-blue-400" />
                                            </div>
                                            <div>
                                                <p className="text-base font-semibold text-white mb-1">
                                                    {company.files.length > 0
                                                        ? `${company.files.length} Datei(en) ausgewählt`
                                                        : "Excel- oder CSV-Dateien auswählen"}
                                                </p>
                                                <p className="text-sm text-slate-300 font-medium">
                                                    Genau 2 Dateien erforderlich (.xlsx, .xls oder .csv)
                                                </p>
                                                <p className="text-xs text-slate-400 mt-1">
                                                    Oder per Drag & Drop hier ablegen
                                                </p>
                                                {company.files.length === 1 && (
                                                    <p className="text-xs text-orange-400 mt-2 font-medium">
                                                        ⚠️ Bitte wählen Sie noch eine 2. Datei aus
                                                    </p>
                                                )}
                                            </div>
                                        </label>
                                        
                                        {/* Show selected files */}
                                        {company.files.length > 0 && (
                                            <div className="mt-4 space-y-2">
                                                {company.files.map((file, fileIdx) => (
                                                    <div key={fileIdx} className="bg-green-900/30 border border-green-700 rounded-lg p-3 flex items-center gap-2">
                                                        <FileSpreadsheet className="h-4 w-4 text-green-400 flex-shrink-0" />
                                                        <div className="flex-1 text-left">
                                                            <p className="text-sm font-semibold text-green-300 truncate">{file.name}</p>
                                                            <p className="text-xs text-green-400">
                                                                {(file.size / 1024).toFixed(2)} KB
                                                            </p>
                                                        </div>
                                                        <button
                                                            onClick={() => removeFile(index, fileIdx)}
                                                            className="p-1 hover:bg-red-900/30 rounded transition-colors group"
                                                            title="Datei entfernen"
                                                        >
                                                            <X className="h-4 w-4 text-green-400 group-hover:text-red-400" />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Error Message */}
                {error && (
                    <div style={{ maxWidth: 560, margin: '0 auto 16px', padding: '10px 14px', borderRadius: 8, background: 'rgba(244,63,94,0.15)', border: '1px solid rgba(244,63,94,0.4)', font: '400 13px/1.4 var(--font-sans)', color: '#fca5a5' }}>
                        {error}
                    </div>
                )}

                {/* Action Button - only show if all companies are checked */}
                {(() => {
                    const activeCompanies = companies.slice(0, mode)
                    const allChecked = activeCompanies.every(c => c.isChecked)
                    
                    if (!allChecked) return null
                    
                    const hasNewCompanies = activeCompanies.some(c => !c.existsInDB)
                    const allExisting = activeCompanies.every(c => c.existsInDB)
                    
                    const btnBase = {
                        width: '100%', height: 48, borderRadius: 10,
                        font: '600 15px/1 var(--font-sans)',
                        color: '#fff', border: 'none', cursor: 'pointer',
                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                        transition: 'background 150ms ease',
                    }

                    if (allExisting) {
                        return (
                            <div style={{ maxWidth: 480, margin: '0 auto' }}>
                                <button
                                    onClick={() => navigateToAnalysis(buildSelectedCompanies(activeCompanies))}
                                    style={{ ...btnBase, background: '#059669' }}
                                >
                                    <ArrowRight className="h-5 w-5" />
                                    Weiter zur Analyse
                                </button>
                            </div>
                        )
                    }

                    if (hasNewCompanies) {
                        return (
                            <div style={{ maxWidth: 480, margin: '0 auto' }}>
                                <button
                                    onClick={handleUpload}
                                    disabled={uploading}
                                    style={{ ...btnBase, background: uploading ? 'rgba(255,255,255,0.15)' : '#2563eb', cursor: uploading ? 'not-allowed' : 'pointer' }}
                                >
                                    {uploading ? (
                                        <><div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> Wird hochgeladen…</>
                                    ) : (
                                        <><UploadIcon className="h-5 w-5" /> Dateien hochladen & Fortfahren <ArrowRight className="h-5 w-5" /></>
                                    )}
                                </button>
                            </div>
                        )
                    }
                    
                    return null
                })()}

                {/* Skip Option */}
                <div style={{ textAlign: 'center', paddingTop: 16 }}>
                    <button
                        onClick={() => navigate("/dashboard")}
                        style={{ font: '400 13px/1 var(--font-sans)', color: 'rgba(255,255,255,0.45)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                    >
                        Überspringen und Dashboard ansehen
                    </button>
                </div>

            </div>
        </div>
    )
}
