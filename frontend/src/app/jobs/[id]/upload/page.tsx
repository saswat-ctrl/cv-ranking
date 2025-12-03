"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter, useParams } from "next/navigation"
import { api } from "@/lib/api_client"
import { getErrorMessage } from "@/types/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import {
    Upload,
    ArrowLeft,
    Download,
    CheckSquare,
    Square,
    Briefcase,
    X,
    ShoppingCart,
    Trash2
} from "lucide-react"
import { toast } from "react-hot-toast"

interface Candidate {
    id: string
    name: string
    email: string
    parsed_skills: string[]
}

interface Job {
    id: string
    title: string
}

interface SelectedCandidate extends Candidate {
    sourceJobId: string
    sourceJobTitle: string
}

export default function UploadCVsPage() {
    const router = useRouter()
    const params = useParams()
    const jobId = params.id as string

    const [files, setFiles] = useState<File[]>([])
    const [uploading, setUploading] = useState(false)

    // Import dialog state
    const [importDialogOpen, setImportDialogOpen] = useState(false)
    const [jobs, setJobs] = useState<Job[]>([])
    const [selectedJob, setSelectedJob] = useState<string | null>(null)
    const [candidates, setCandidates] = useState<Candidate[]>([])
    const [importing, setImporting] = useState(false)
    const [importStatus, setImportStatus] = useState<{ imported: number, skipped: number } | null>(null)

    // Shopping cart for candidates from multiple jobs
    const [candidateCart, setCandidateCart] = useState<Map<string, SelectedCandidate>>(new Map())

    // Simple derived counts for UI summaries (no business logic)
    const cartSize = candidateCart.size
    const sourceJobCount = useMemo(
        () => new Set(Array.from(candidateCart.values()).map((c) => c.sourceJobId)).size,
        [candidateCart],
    )

    const fetchJobs = async () => {
        try {
            const response = await api.get("/jobs")
            // FILTER OUT CURRENT JOB
            const otherJobs = response.data.filter((job: Job) => job.id !== jobId)
            setJobs(otherJobs)
        } catch {
            toast.error("Failed to load jobs")
        }
    }

    const fetchCandidates = async (sourceJobId: string) => {
        try {
            const response = await api.get(`/jobs/${sourceJobId}/candidates`)
            setCandidates(response.data)
        } catch {
            toast.error("Failed to load candidates")
        }
    }

    useEffect(() => {
        if (importDialogOpen) {
            fetchJobs()
        } else {
            // Reset job selection when dialog closes, but keep the cart
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setSelectedJob(null)
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setImportStatus(null)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [importDialogOpen])

    useEffect(() => {
        if (selectedJob) {
            fetchCandidates(selectedJob)
        } else {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setCandidates([])
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedJob])

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const newFiles = Array.from(e.target.files)

            setFiles(prev => {
                const existingNames = new Set(prev.map(f => f.name))
                const uniqueNewFiles = newFiles.filter(f => !existingNames.has(f.name))

                if (uniqueNewFiles.length < newFiles.length) {
                    toast("Some duplicate files were skipped", { icon: "ℹ️" })
                }

                return [...prev, ...uniqueNewFiles]
            })

            // Reset input so same files can be selected again if removed
            e.target.value = ""
        }
    }

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index))
    }

    const toggleCandidateInCart = (candidate: Candidate) => {
        if (!selectedJob) return

        const newCart = new Map(candidateCart)
        const selectedJobData = jobs.find(j => j.id === selectedJob)

        if (newCart.has(candidate.id)) {
            newCart.delete(candidate.id)
        } else {
            newCart.set(candidate.id, {
                ...candidate,
                sourceJobId: selectedJob,
                sourceJobTitle: selectedJobData?.title || "Unknown Job"
            })
        }
        setCandidateCart(newCart)
    }

    const removeCandidateFromCart = (candidateId: string) => {
        const newCart = new Map(candidateCart)
        newCart.delete(candidateId)
        setCandidateCart(newCart)
    }

    const clearCart = () => {
        setCandidateCart(new Map())
    }

    const handleSaveAndContinue = async () => {
        if (files.length === 0 && candidateCart.size === 0) {
            toast.error("Please select files or candidates first")
            return
        }

        setUploading(true)

        // Stats tracking
        let uploadedCount = 0
        let uploadErrors = 0
        let importedCount = 0
        let importSkippedCount = 0
        const errorMessages: string[] = []

        try {
            // 1. Upload Files
            if (files.length > 0) {
                for (const file of files) {
                    const formData = new FormData()
                    formData.append("file", file)
                    try {
                        await api.post(`/jobs/${jobId}/candidates`, formData, {
                            headers: { "Content-Type": "multipart/form-data" },
                        })
                        uploadedCount++
                    } catch (error: unknown) {
                        console.error(`Failed to upload ${file.name}`, error)
                        uploadErrors++
                        const msg = getErrorMessage(error)
                        // Simplify duplicate message
                        if (msg.includes("already exists")) {
                            errorMessages.push(`${file.name}: Duplicate email`)
                        } else {
                            errorMessages.push(`${file.name}: ${msg}`)
                        }
                    }
                }
            }

            // 2. Import Candidates
            if (candidateCart.size > 0) {
                // Group candidates by source job
                const candidatesByJob = new Map<string, string[]>()
                candidateCart.forEach((candidate) => {
                    const existing = candidatesByJob.get(candidate.sourceJobId) || []
                    existing.push(candidate.id)
                    candidatesByJob.set(candidate.sourceJobId, existing)
                })

                for (const [sourceJobId, candidateIds] of candidatesByJob.entries()) {
                    try {
                        const response = await api.post(`/jobs/${jobId}/import_candidates`, {
                            source_job_id: sourceJobId,
                            candidate_ids: candidateIds,
                        })
                        importedCount += response.data.imported
                        importSkippedCount += response.data.skipped
                    } catch (error) {
                        console.error("Import failed for a batch", error)
                        toast.error("Failed to import some candidates")
                    }
                }
            }

            // 3. Construct Summary Message
            const parts: string[] = []
            if (uploadedCount > 0) parts.push(`✅ Uploaded ${uploadedCount} file(s)`)
            if (uploadErrors > 0) parts.push(`❌ Failed to upload ${uploadErrors} file(s)`)
            if (importedCount > 0) parts.push(`✅ Imported ${importedCount} candidate(s)`)
            if (importSkippedCount > 0) parts.push(`⚠️ Skipped ${importSkippedCount} duplicate(s)`)

            // Show detailed feedback
            if (uploadErrors > 0 || importSkippedCount > 0) {
                toast(() => (
                    <div className="text-sm">
                        <div className="font-semibold mb-1">Processing Complete</div>
                        {parts.map((part, i) => <div key={i}>{part}</div>)}
                    </div>
                ), { duration: 5000 })
            } else {
                toast.success(`Successfully added ${uploadedCount + importedCount} candidates!`)
            }

            // Redirect after a short delay to let them read, or immediately if all good
            const delay = (uploadErrors > 0 || importSkippedCount > 0) ? 2000 : 500
            setTimeout(() => {
                router.push(`/jobs/${jobId}/candidates`)
            }, delay)

        } catch {
            toast.error("Something went wrong during save")
            setUploading(false) // Only reset if we crash completely, otherwise we redirect
        }
    }

    // Check if candidate is in cart
    const isInCart = (candidateId: string) => candidateCart.has(candidateId)

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="space-y-2">
                <Button
                    variant="ghost"
                    size="sm"
                    className="w-fit"
                    onClick={() => router.push(`/jobs/${jobId}`)}
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Job
                </Button>

                <div className="space-y-1">
                    <h1 className="text-3xl font-bold tracking-tight">Upload candidates</h1>
                    <p className="max-w-2xl text-sm text-muted-foreground">
                        Add candidates to this job by uploading new CVs or reusing strong profiles from other jobs.
                        We&apos;ll extract text and skills so they&apos;re ready for ranking.
                    </p>
                </div>
            </div>

            {/* Upload Section */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Upload className="h-5 w-5" />
                        Step 1 (optional) – Upload new CVs
                    </CardTitle>
                    <CardDescription>
                        Drag and drop or click to upload CVs. We&apos;ll extract text and attempt to parse key details
                        like name, email, phone and skills.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <div className="flex items-center justify-center w-full">
                            <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 border-gray-300">
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    <Upload className="w-8 h-8 mb-3 text-gray-400" />
                                    <p className="mb-2 text-sm text-gray-500"><span className="font-semibold">Click to upload</span> or drag and drop</p>
                                    <p className="text-xs text-gray-500">PDF, DOCX (MAX. 10MB)</p>
                                </div>
                                <input
                                    id="dropzone-file"
                                    type="file"
                                    multiple
                                    accept=".pdf,.docx,.doc"
                                    onChange={handleFileChange}
                                    className="hidden"
                                />
                            </label>
                        </div>
                    </div>

                    {/* Selected Files List */}
                    {files.length > 0 && (
                        <div className="rounded-lg border bg-card">
                            <div className="p-3 border-b bg-muted/50 flex justify-between items-center">
                                <div className="space-y-0.5">
                                    <h4 className="font-semibold text-sm">
                                        Selected files ({files.length})
                                    </h4>
                                    <p className="text-xs text-muted-foreground">
                                        PDF / DOC / DOCX • Max ~10MB per file • Duplicates by filename are skipped
                                    </p>
                                </div>
                                <Button variant="ghost" size="sm" onClick={() => setFiles([])} className="h-auto p-1 text-xs text-muted-foreground hover:text-destructive">
                                    Clear All
                                </Button>
                            </div>
                            <div className="max-h-60 overflow-y-auto divide-y">
                                {files.map((file, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 text-sm hover:bg-muted/50 transition-colors">
                                        <div className="flex items-center gap-3 min-w-0">
                                            <div className="h-8 w-8 rounded bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0">
                                                <span className="text-xs font-bold">
                                                    {file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "DOC"}
                                                </span>
                                            </div>
                                            <div className="min-w-0">
                                                <p className="font-medium truncate">{file.name}</p>
                                                <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                            </div>
                                        </div>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => removeFile(idx)}
                                            className="text-muted-foreground hover:text-destructive"
                                        >
                                            <X className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Import Section */}
            <Card className="border-blue-100 bg-blue-50/30">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Download className="h-5 w-5" />
                        Step 2 (optional) – Import from other jobs
                    </CardTitle>
                    <CardDescription>
                        Reuse candidates you&apos;ve already uploaded for other jobs. We&apos;ll avoid duplicates in this
                        job based on candidate email.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Shopping Cart Summary */}
                    {cartSize > 0 && (
                        <div className="rounded-lg border-2 border-blue-200 bg-blue-50 p-4">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    <ShoppingCart className="h-5 w-5 text-blue-600" />
                                    <h4 className="font-semibold text-blue-900">
                                        {cartSize} candidate{cartSize !== 1 ? "s" : ""} selected from{" "}
                                        {sourceJobCount} job{sourceJobCount !== 1 ? "s" : ""}
                                    </h4>
                                </div>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={clearCart}
                                        className="gap-2"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                        Clear All
                                    </Button>
                                </div>
                            </div>
                            <div className="max-h-40 overflow-y-auto space-y-1">
                                {Array.from(candidateCart.values()).map((candidate) => (
                                    <div
                                        key={candidate.id}
                                        className="flex items-center justify-between bg-white rounded p-2 text-sm"
                                    >
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium text-gray-900 truncate">{candidate.name}</div>
                                            <div className="text-xs text-gray-500">from {candidate.sourceJobTitle}</div>
                                        </div>
                                        <button
                                            onClick={() => removeCandidateFromCart(candidate.id)}
                                            className="text-red-600 hover:text-red-800 p-1"
                                        >
                                            <X className="h-4 w-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
                        <DialogTrigger asChild>
                            <Button variant="outline" className="gap-2">
                                <Briefcase className="h-4 w-4" />
                                Browse & select candidates
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-3xl max-h-[90vh] bg-white" style={{ backgroundColor: '#FFFFFF', zIndex: 100 }}>
                            <DialogHeader>
                                <DialogTitle className="text-xl">
                                    Browse candidates from other jobs
                                </DialogTitle>
                                <DialogDescription>
                                    1. Pick a source job • 2. Click candidates to add/remove • 3. Close this dialog to
                                    review your cart.
                                </DialogDescription>
                            </DialogHeader>

                            <div className="space-y-4 overflow-y-auto max-h-[60vh] pr-2">
                                {/* Job Selection */}
                                <div>
                                    <label className="mb-2 block text-sm font-semibold text-gray-900">
                                        1. Select source job
                                    </label>
                                    <div className="grid gap-2 max-h-48 overflow-y-auto rounded-lg border-2 border-gray-200 p-3 bg-gray-50">
                                        {jobs.map((job) => (
                                            <button
                                                key={job.id}
                                                onClick={() => setSelectedJob(job.id)}
                                                className={`text-left cursor-pointer rounded-lg border-2 p-3 transition-all ${selectedJob === job.id
                                                    ? "border-blue-600 bg-blue-50 shadow-sm"
                                                    : "border-gray-300 bg-white hover:border-blue-300 hover:bg-blue-50/50"
                                                    }`}
                                            >
                                                <div className="font-medium text-gray-900">{job.title}</div>
                                            </button>
                                        ))}
                                        {jobs.length === 0 && (
                                            <div className="py-8 text-center">
                                                <Briefcase className="mx-auto h-12 w-12 text-gray-400 mb-2" />
                                                <p className="text-sm font-medium text-gray-900">No other jobs available</p>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    Current job is automatically excluded
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Candidate Selection */}
                                {selectedJob && (
                                    <div>
                                        <div className="mb-2 flex items-center justify-between">
                                            <label className="text-sm font-semibold text-gray-900">
                                                2. Select candidates (click to add to cart)
                                            </label>
                                        </div>
                                        <div className="space-y-2 max-h-80 overflow-y-auto rounded-lg border-2 border-gray-200 p-3 bg-gray-50">
                                            {candidates.map((candidate) => {
                                                const inCart = isInCart(candidate.id)
                                                return (
                                                    <button
                                                        key={candidate.id}
                                                        onClick={() => toggleCandidateInCart(candidate)}
                                                        className={`w-full text-left cursor-pointer rounded-lg border-2 p-3 transition-all ${inCart
                                                            ? "border-green-600 bg-green-50 shadow-sm"
                                                            : "border-gray-300 bg-white hover:border-blue-300 hover:bg-blue-50/50"
                                                            }`}
                                                    >
                                                        <div className="flex items-start justify-between gap-3">
                                                            <div className="flex-1 min-w-0">
                                                                <div className="font-medium text-gray-900 truncate">{candidate.name}</div>
                                                                <div className="text-sm text-gray-600 truncate">{candidate.email}</div>
                                                                {candidate.parsed_skills && candidate.parsed_skills.length > 0 && (
                                                                    <div className="mt-2 flex flex-wrap gap-1">
                                                                        {candidate.parsed_skills.slice(0, 3).map((skill, i) => (
                                                                            <Badge key={i} variant="secondary" className="text-xs">
                                                                                {skill}
                                                                            </Badge>
                                                                        ))}
                                                                        {candidate.parsed_skills.length > 3 && (
                                                                            <Badge variant="outline" className="text-xs">
                                                                                +{candidate.parsed_skills.length - 3}
                                                                            </Badge>
                                                                        )}
                                                                    </div>
                                                                )}
                                                            </div>
                                                            {inCart ? (
                                                                <div className="flex items-center gap-1 flex-shrink-0 text-green-600">
                                                                    <CheckSquare className="h-5 w-5" />
                                                                    <span className="text-xs font-medium">In Cart</span>
                                                                </div>
                                                            ) : (
                                                                <Square className="h-5 w-5 text-gray-400 flex-shrink-0" />
                                                            )}
                                                        </div>
                                                    </button>
                                                )
                                            })}
                                            {candidates.length === 0 && (
                                                <p className="py-8 text-center text-sm text-gray-500">
                                                    No candidates found in this job yet.
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Import Status */}
                                {importStatus && (
                                    <div className="rounded-lg border-2 border-green-200 bg-green-50 p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <CheckSquare className="h-5 w-5 text-green-600" />
                                            <h4 className="font-semibold text-green-900">Import Complete!</h4>
                                        </div>
                                        <div className="space-y-1 text-sm">
                                            <p className="text-green-700">✅ {importStatus.imported} candidates imported successfully</p>
                                            {importStatus.skipped > 0 && (
                                                <p className="text-yellow-700">⚠️ {importStatus.skipped} candidates skipped (duplicates based on email)</p>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>

                            <DialogFooter>
                                <div className="flex items-center justify-between w-full">
                                    <div className="text-sm text-gray-600">
                                        3. In cart: {cartSize} candidate{cartSize !== 1 ? "s" : ""} from{" "}
                                        {sourceJobCount} job{sourceJobCount !== 1 ? "s" : ""}. They&apos;ll be added
                                        when you save on the main page.
                                    </div>
                                    <Button
                                        variant="outline"
                                        onClick={() => setImportDialogOpen(false)}
                                    >
                                        {importStatus ? "Close" : "Done selecting"}
                                    </Button>
                                </div>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </CardContent>
            </Card>

            {/* Save and Continue */}
            <div className="flex flex-col items-stretch gap-3 border-t pt-4 md:flex-row md:items-center md:justify-between">
                <p className="text-sm text-muted-foreground">
                    Ready to add{" "}
                    <span className="font-medium">
                        {files.length} uploaded file{files.length !== 1 ? "s" : ""}{" "}
                    </span>
                    and{" "}
                    <span className="font-medium">
                        {cartSize} imported candidate{cartSize !== 1 ? "s" : ""}.
                    </span>
                </p>
            <div className="flex justify-end gap-3">
                <Button
                    variant="outline"
                    onClick={() => router.push(`/jobs/${jobId}`)}
                >
                    Cancel
                </Button>
                <Button
                    onClick={handleSaveAndContinue}
                        disabled={uploading || (files.length === 0 && cartSize === 0)}
                    size="lg"
                    className="gap-2"
                >
                        {uploading ? "Saving..." : "Save candidates & view list"}
                    <ArrowLeft className="h-4 w-4 rotate-180" />
                </Button>
                </div>
            </div>
        </div>
    )
}
