"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { api } from "@/lib/api_client"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
    ArrowLeft,
    TrendingUp,
    Upload,
    CheckSquare,
    Square,
    Mail,
    FileText,
    Search,
    Eye,
    Download,
    FileDown,
    Trash2
} from "lucide-react"
import { toast } from "react-hot-toast"
import { Candidate, getErrorMessage, isApiError } from "@/types/api"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

export default function CandidatesPage() {
    const params = useParams()
    const router = useRouter()
    const jobId = params.id as string

    const [candidates, setCandidates] = useState<Candidate[]>([])
    const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set())
    const [loading, setLoading] = useState(true)
    const [ranking, setRanking] = useState(false)
    const [searchQuery, setSearchQuery] = useState("")
    const [deleting, setDeleting] = useState(false)
    const [sortBy, setSortBy] = useState("ranking") // ranking, name, date
    const [statusFilter, setStatusFilter] = useState("all") // all, ranked, unranked
    const [editingScores, setEditingScores] = useState<Record<string, string>>({}) // candidateId -> score value
    const [savingScores, setSavingScores] = useState<Set<string>>(new Set()) // candidateIds being saved

    const fetchCandidates = async () => {
        try {
            const response = await api.get(`/jobs/${jobId}/candidates`)
            setCandidates(response.data)
        } catch (err) {
            console.error(err)
            toast.error("Failed to load candidates")
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchCandidates()
    }, [jobId])

    const toggleCandidate = (candidateId: string) => {
        const newSelected = new Set(selectedCandidates)
        if (newSelected.has(candidateId)) {
            newSelected.delete(candidateId)
        } else {
            newSelected.add(candidateId)
        }
        setSelectedCandidates(newSelected)
    }

    const toggleSelectAll = () => {
        if (selectedCandidates.size === candidates.length) {
            setSelectedCandidates(new Set())
        } else {
            setSelectedCandidates(new Set(candidates.map(c => c.id)))
        }
    }

    const handleRank = async () => {
        setRanking(true)
        try {
            await api.post(`/jobs/${jobId}/rank`)
            toast.success("Ranking completed!")
            // Refresh candidates to get updated scores
            await fetchCandidates()
            // Auto-sort by ranking after completion
            setSortBy("ranking_score")
        } catch (err: unknown) {
            toast.error(getErrorMessage(err))
        } finally {
            setRanking(false)
        }
    }

    const handleExportCSV = () => {
        if (candidates.length === 0) {
            toast.error("No candidates to export")
            return
        }

        // Create CSV content
        const headers = ["Name", "Email", "Phone", "Skills", "Ranking Score", "Ranking Explanation", "My Score", "Readable"]
        const rows = candidates.map(c => [
            c.name,
            c.email || "",
            c.parsed_phone || "",
            (c.parsed_skills || []).join("; "),
            c.ranking_score !== null && c.ranking_score !== undefined ? c.ranking_score.toString() : "",
            c.ranking_explanation || "",
            c.user_score !== null && c.user_score !== undefined ? c.user_score.toString() : "",
            c.is_readable ? "Yes" : "No"
        ])

        const csvContent = [
            headers.join(","),
            ...rows.map(row => row.map(cell => `"${cell}"`).join(","))
        ].join("\n")

        // Download CSV
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement("a")
        const url = URL.createObjectURL(blob)
        link.setAttribute("href", url)
        link.setAttribute("download", `candidates_${jobId}.csv`)
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        toast.success(`Exported ${candidates.length} candidates to CSV`)
    }

    const handleBulkDelete = async () => {
        if (selectedCandidates.size === 0) {
            toast.error("No candidates selected")
            return
        }

        const deleteCount = selectedCandidates.size

        // Use setTimeout to ensure the confirm dialog appears after any pending state updates
        const confirmed = await new Promise<boolean>((resolve) => {
            setTimeout(() => {
                resolve(window.confirm(`Are you sure you want to delete ${deleteCount} candidate(s)? This action cannot be undone.`))
            }, 0)
        })

        if (!confirmed) {
            return
        }

        setDeleting(true)
        try {
            // Delete each selected candidate
            const candidatesToDelete = Array.from(selectedCandidates)
            await Promise.all(
                candidatesToDelete.map(candidateId =>
                    api.delete(`/jobs/${jobId}/candidates/${candidateId}`)
                )
            )

            setSelectedCandidates(new Set())
            await fetchCandidates()
            toast.success(`Deleted ${deleteCount} candidate(s)`)
        } catch (err: unknown) {
            toast.error(getErrorMessage(err))
        } finally {
            setDeleting(false)
        }
    }

    const handleSaveUserScore = async (candidateId: string) => {
        const scoreValue = editingScores[candidateId]
        if (!scoreValue) {
            toast.error("Please enter a score")
            return
        }

        const score = parseFloat(scoreValue)
        if (isNaN(score) || score < 0 || score > 100) {
            toast.error("Score must be between 0 and 100")
            return
        }

        setSavingScores(prev => new Set(prev).add(candidateId))
        try {
            await api.patch(`/jobs/${jobId}/candidates/${candidateId}`, {
                user_score: score
            })

            // Update local state
            setCandidates(prev => prev.map(c =>
                c.id === candidateId ? { ...c, user_score: score } : c
            ))

            // Clear editing state
            setEditingScores(prev => {
                const newState = { ...prev }
                delete newState[candidateId]
                return newState
            })

            toast.success("Score saved")
        } catch (err: unknown) {
            toast.error(getErrorMessage(err))
        } finally {
            setSavingScores(prev => {
                const newSet = new Set(prev)
                newSet.delete(candidateId)
                return newSet
            })
        }
    }

    const handleDownload = async (candidateId: string, candidateName: string, e: React.MouseEvent) => {
        e.stopPropagation()
        try {
            console.log('Starting download for candidate:', candidateId)
            const response = await api.get(`/jobs/${jobId}/candidates/${candidateId}/download`, {
                responseType: 'arraybuffer'  // Changed from 'blob' to 'arraybuffer'
            })

            const contentType = response.headers['content-type'] || 'application/pdf'

            console.log('Download response:', {
                status: response.status,
                contentType: contentType,
                dataType: typeof response.data,
                dataSize: response.data?.byteLength || 'unknown',
                isArrayBuffer: response.data instanceof ArrayBuffer
            })

            // Create blob from arraybuffer
            const blob = new Blob([response.data], { type: contentType })
            console.log('Created blob:', { size: blob.size, type: blob.type })

            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url

            const contentDisposition = response.headers['content-disposition']
            let filename = `${candidateName.replace(/\s+/g, '_')}_CV.pdf`
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename=\"?([^\"]+)\"?/)
                if (filenameMatch && filenameMatch.length === 2)
                    filename = filenameMatch[1]
            }

            link.setAttribute('download', filename)
            document.body.appendChild(link)
            link.click()

            // Clean up after a short delay to ensure download starts
            setTimeout(() => {
                link.remove()
                window.URL.revokeObjectURL(url)
            }, 100)

            toast.success("Download started")
        } catch (error: unknown) {
            console.error('Download error:', error)
            if (isApiError(error) && error.response?.data instanceof Blob) {
                const text = await error.response.data.text()
                try {
                    const json = JSON.parse(text)
                    toast.error(json.detail || "Failed to download CV")
                } catch {
                    toast.error("Failed to download CV")
                }
            } else {
                toast.error(getErrorMessage(error))
            }
        }
    }

    const handleView = async (candidateId: string, e: React.MouseEvent) => {
        e.stopPropagation()
        try {
            console.log('Starting view for candidate:', candidateId)
            const response = await api.get(`/jobs/${jobId}/candidates/${candidateId}/download?inline=true`, {
                responseType: 'arraybuffer'
            })

            const contentType = response.headers['content-type'] || 'application/pdf'

            console.log('View response:', {
                status: response.status,
                contentType: contentType,
                dataType: typeof response.data,
                dataSize: response.data?.byteLength || 'unknown',
                isArrayBuffer: response.data instanceof ArrayBuffer
            })

            const blob = new Blob([response.data], { type: contentType })
            console.log('Created blob for view:', { size: blob.size, type: blob.type })

            const fileURL = URL.createObjectURL(blob)
            window.open(fileURL, '_blank')

        } catch (error: unknown) {
            console.error('View error:', error)
            toast.error(getErrorMessage(error))
        }
    }

    // Derived stats for overview widgets
    const { totalCandidates, rankedCount, unrankedCount } = useMemo(() => {
        const total = candidates.length
        const ranked = candidates.filter(c => c.ranking_score !== null && c.ranking_score !== undefined).length
        return {
            totalCandidates: total,
            rankedCount: ranked,
            unrankedCount: total - ranked,
        }
    }, [candidates])

    // Filter and sort candidates (memoized for snappier UI)
    const filteredCandidates = useMemo(() => {
        const lowerQuery = searchQuery.toLowerCase()

        let processed = candidates.filter(candidate => {
            // Search filter
            const matchesSearch =
                candidate.name.toLowerCase().includes(lowerQuery) ||
                candidate.email.toLowerCase().includes(lowerQuery) ||
                (candidate.parsed_skills &&
                    candidate.parsed_skills.some(skill =>
                        skill.toLowerCase().includes(lowerQuery),
                    ))

            // Status filter
            const hasRanking = candidate.ranking_score !== null && candidate.ranking_score !== undefined
            const matchesStatus =
                statusFilter === "all" ||
                (statusFilter === "ranked" && hasRanking) ||
                (statusFilter === "unranked" && !hasRanking)

            return matchesSearch && matchesStatus
        })

        // Sort candidates
        processed = [...processed].sort((a, b) => {
            if (sortBy === "ranking") {
                // Sort by ranking score (high to low), unranked at bottom
                const scoreA = a.ranking_score ?? -1
                const scoreB = b.ranking_score ?? -1
                return scoreB - scoreA
            } else if (sortBy === "name") {
                return a.name.localeCompare(b.name)
            } else {
                // date - would need created_at field, for now use name
                return a.name.localeCompare(b.name)
            }
        })

        return processed
    }, [candidates, searchQuery, statusFilter, sortBy])

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <p className="text-muted-foreground">Loading candidates...</p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Page header */}
            <div className="flex flex-col gap-4">
                <Button
                    variant="ghost"
                    size="sm"
                    className="w-fit"
                    onClick={() => router.push(`/jobs/${jobId}`)}
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Job
                </Button>

                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Candidates</h1>
                        <p className="text-sm text-muted-foreground">
                            Review, rank, and export candidates for this job. Click a row to select; use “My Score” to
                            capture your own assessment on top of the AI ranking.
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-2 md:justify-end">
                        <Button
                            variant="outline"
                            onClick={() => router.push(`/jobs/${jobId}/upload`)}
                            className="gap-2"
                        >
                            <Upload className="h-4 w-4" />
                            Add Candidates
                        </Button>
                        <Button
                            variant="outline"
                            onClick={handleExportCSV}
                            disabled={candidates.length === 0}
                            className="gap-2"
                        >
                            <FileDown className="h-4 w-4" />
                            Export CSV
                        </Button>
                        <Button
                            onClick={handleRank}
                            disabled={candidates.length === 0 || ranking}
                            size="lg"
                            className="gap-2"
                        >
                            <TrendingUp className="h-5 w-5" />
                            {ranking ? "Ranking..." : "Rank All Candidates"}
                        </Button>
                    </div>
                </div>
            </div>

            {/* Overview stats */}
            {candidates.length > 0 && (
                <div className="grid gap-4 md:grid-cols-4">
                    <Card>
                        <CardContent className="pt-4 pb-4">
                            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Total candidates
                            </p>
                            <p className="mt-1 text-2xl font-semibold">{totalCandidates}</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-4 pb-4">
                            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Ranked by AI
                            </p>
                            <p className="mt-1 text-2xl font-semibold">{rankedCount}</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-4 pb-4">
                            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Unranked
                            </p>
                            <p className="mt-1 text-2xl font-semibold">{unrankedCount}</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-4 pb-4">
                            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Selected
                            </p>
                            <p className="mt-1 text-2xl font-semibold">{selectedCandidates.size}</p>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Search and Filters */}
            {candidates.length > 0 && (
                <Card className="border-dashed">
                    <CardContent className="flex flex-col gap-4 pt-6 md:flex-row md:items-center">
                        <div className="relative flex-1">
                            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                            <Input
                                placeholder="Search by name, email, or skills..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10"
                            />
                        </div>
                        <div className="flex flex-wrap gap-3">
                            <Select value={sortBy} onValueChange={setSortBy}>
                                <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Sort by" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="ranking">Ranking Score</SelectItem>
                                    <SelectItem value="name">Name (A–Z)</SelectItem>
                                    <SelectItem value="date">Date Added</SelectItem>
                                </SelectContent>
                            </Select>
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Candidates</SelectItem>
                                    <SelectItem value="ranked">Ranked Only</SelectItem>
                                    <SelectItem value="unranked">Unranked Only</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Selection Controls */}
            {candidates.length > 0 && (
                <Card>
                    <CardContent className="flex flex-col items-start justify-between gap-3 pt-4 pb-4 md:flex-row md:items-center">
                        <div className="flex flex-wrap gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={toggleSelectAll}
                                className="gap-2"
                            >
                                {selectedCandidates.size === candidates.length ? (
                                    <>
                                        <Square className="h-4 w-4" />
                                        Deselect All
                                    </>
                                ) : (
                                    <>
                                        <CheckSquare className="h-4 w-4" />
                                        Select All
                                    </>
                                )}
                            </Button>
                            {selectedCandidates.size > 0 && (
                                <Button
                                    variant="destructive"
                                    size="sm"
                                    onClick={(e) => {
                                        e.preventDefault()
                                        e.stopPropagation()
                                        handleBulkDelete()
                                    }}
                                    disabled={deleting}
                                    className="gap-2"
                                >
                                    <Trash2 className="h-4 w-4" />
                                    {deleting ? "Deleting..." : `Delete Selected (${selectedCandidates.size})`}
                                </Button>
                            )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                            Click anywhere on a card to select / deselect. Use the candidate name to open full details.
                        </p>
                    </CardContent>
                </Card>
            )}

            {/* Candidates List */}
            {filteredCandidates.length === 0 ? (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-16">
                        <FileText className="mb-4 h-16 w-16 text-muted-foreground" />
                        <h3 className="mb-2 text-xl font-semibold">
                            {searchQuery ? "No candidates found" : "No Candidates Yet"}
                        </h3>
                        <p className="mb-6 max-w-md text-center text-sm text-muted-foreground">
                            {searchQuery
                                ? `No candidates match “${searchQuery}”. Try adjusting your search or filters.`
                                : "Add candidates by uploading CVs or importing from other jobs so we can rank them for this role."}
                        </p>
                        {!searchQuery && (
                            <Button onClick={() => router.push(`/jobs/${jobId}/upload`)} className="gap-2">
                                <Upload className="h-4 w-4" />
                                Add Candidates
                            </Button>
                        )}
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4">
                    {filteredCandidates.map((candidate) => {
                        const isSelected = selectedCandidates.has(candidate.id)
                        const isRanked = candidate.ranking_score !== null && candidate.ranking_score !== undefined

                        return (
                            <Card
                                key={candidate.id}
                                className={`cursor-pointer transition-all ${isSelected
                                    ? "border-primary bg-primary/5 shadow-md"
                                    : "hover:border-primary/40 hover:bg-accent/40"
                                    }`}
                                onClick={() => toggleCandidate(candidate.id)}
                            >
                                <CardContent className="p-5 md:p-6">
                                    <div className="flex items-start justify-between gap-4">
                                        {/* Left: identity + skills + score controls */}
                                        <div className="flex-1 space-y-3">
                                            {/* Name row */}
                                            <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                                                <div className="space-y-1">
                                                    <div className="flex flex-wrap items-center gap-3">
                                                        <h3
                                                            className="text-lg font-semibold hover:text-primary"
                                                            onClick={(e) => {
                                                                e.stopPropagation()
                                                                router.push(
                                                                    `/jobs/${jobId}/candidates/${candidate.id}`,
                                                                )
                                                            }}
                                                        >
                                                            {candidate.name}
                                                        </h3>
                                                        {isRanked && (
                                                            <Badge
                                                                variant={
                                                                    candidate.ranking_score! >= 80
                                                                        ? "default"
                                                                        : candidate.ranking_score! >= 60
                                                                            ? "secondary"
                                                                            : "destructive"
                                                                }
                                                                className="flex items-center gap-1 text-sm font-semibold"
                                                            >
                                                                <TrendingUp className="h-3 w-3" />
                                                                {candidate.ranking_score}%
                                                            </Badge>
                                                        )}
                                                        <Badge variant="outline" className="text-xs font-normal">
                                                            {isRanked ? "Ranked" : "Not ranked yet"}
                                                        </Badge>
                                                        {!candidate.is_readable && (
                                                            <Badge variant="destructive" className="text-xs">
                                                                Unreadable CV
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                                                        <Mail className="h-4 w-4" />
                                                        <span className="truncate">{candidate.email}</span>
                                                    </div>
                                                </div>

                                                {/* Quick CV actions on desktop */}
                                                <div className="hidden items-center gap-2 md:flex">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={(e) => handleView(candidate.id, e)}
                                                        className="h-8 w-8 p-0"
                                                        title="View CV"
                                                    >
                                                        <Eye className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={(e) =>
                                                            handleDownload(candidate.id, candidate.name, e)
                                                        }
                                                        className="h-8 w-8 p-0"
                                                        title="Download CV"
                                                    >
                                                        <Download className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </div>

                                            {/* Skills */}
                                            {candidate.parsed_skills && candidate.parsed_skills.length > 0 && (
                                                <div className="space-y-1">
                                                    <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                                        Skills
                                                    </p>
                                                    <div className="flex flex-wrap gap-2">
                                                        {candidate.parsed_skills.slice(0, 10).map((skill, i) => (
                                                            <Badge key={i} variant="secondary">
                                                                {skill}
                                                            </Badge>
                                                        ))}
                                                        {candidate.parsed_skills.length > 10 && (
                                                            <Badge variant="outline">
                                                                +{candidate.parsed_skills.length - 10} more
                                                            </Badge>
                                                        )}
                                                    </div>
                                                </div>
                                            )}

                                            {/* My Score Section */}
                                            <div className="flex flex-col gap-3 border-t pt-3 md:flex-row md:items-center md:justify-between">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                                        My Score
                                                    </span>
                                                    <Input
                                                        type="number"
                                                        min="0"
                                                        max="100"
                                                        step="0.01"
                                                        placeholder="0.00"
                                                        value={
                                                            editingScores[candidate.id] ??
                                                            candidate.user_score?.toFixed(2) ??
                                                            ""
                                                        }
                                                        onChange={(e) => {
                                                            e.stopPropagation()
                                                            setEditingScores((prev) => ({
                                                                ...prev,
                                                                [candidate.id]: e.target.value,
                                                            }))
                                                        }}
                                                        onClick={(e) => e.stopPropagation()}
                                                        className="h-8 w-24"
                                                    />
                                                    {candidate.user_score !== null &&
                                                        candidate.user_score !== undefined && (
                                                            <span className="text-xs text-muted-foreground">
                                                                Last saved: {candidate.user_score.toFixed(2)}
                                                            </span>
                                                        )}
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        onClick={(e) => {
                                                            e.stopPropagation()
                                                            handleSaveUserScore(candidate.id)
                                                        }}
                                                        disabled={
                                                            savingScores.has(candidate.id) ||
                                                            !editingScores[candidate.id]
                                                        }
                                                        className="h-8"
                                                    >
                                                        {savingScores.has(candidate.id) ? "Saving..." : "Save score"}
                                                    </Button>

                                                    {/* Mobile CV actions */}
                                                    <div className="flex items-center gap-1 md:hidden">
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={(e) => handleView(candidate.id, e)}
                                                            className="h-8 w-8"
                                                            title="View CV"
                                                        >
                                                            <Eye className="h-4 w-4" />
                                                        </Button>
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={(e) =>
                                                                handleDownload(candidate.id, candidate.name, e)
                                                            }
                                                            className="h-8 w-8"
                                                            title="Download CV"
                                                        >
                                                            <Download className="h-4 w-4" />
                                                        </Button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Right: selection indicator */}
                                        <div className="mt-1 flex-shrink-0">
                                            {isSelected ? (
                                                <CheckSquare className="h-6 w-6 text-primary" />
                                            ) : (
                                                <Square className="h-6 w-6 text-muted-foreground" />
                                            )}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
