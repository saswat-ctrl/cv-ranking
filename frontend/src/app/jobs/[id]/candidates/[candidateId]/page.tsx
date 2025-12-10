"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Eye, Download, Mail, Phone, TrendingUp, FileText } from "lucide-react"
import { api } from "@/lib/api_client"
import { toast } from "react-hot-toast"
import { Candidate, Job, getErrorMessage, isApiError } from "@/types/api"

export default function CandidateDetailPage() {
    const params = useParams()
    const router = useRouter()
    const jobId = params.id as string
    const candidateId = params.candidateId as string

    const [candidate, setCandidate] = useState<Candidate | null>(null)
    const [job, setJob] = useState<Job | null>(null)
    const [loading, setLoading] = useState(true)

    const fetchCandidateDetails = async () => {
        try {
            const [candidatesResponse, jobResponse] = await Promise.all([
                api.get(`/jobs/${jobId}/candidates`),
                api.get(`/jobs/${jobId}`)
            ])

            const foundCandidate = candidatesResponse.data.find((c: Candidate) => c.id === candidateId)
            if (!foundCandidate) {
                throw new Error("Candidate not found")
            }

            setCandidate(foundCandidate)
            setJob(jobResponse.data)
        } catch (error: unknown) {
            console.error("Failed to fetch candidate details:", error)
            toast.error("Failed to load candidate details")
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        const token = localStorage.getItem("token")
        if (!token) {
            router.push("/login")
            return
        }

        fetchCandidateDetails()
    }, [jobId, candidateId, router])

    const handleDownload = async () => {
        if (!candidate) return;

        try {
            const response = await api.get(`/jobs/${jobId}/candidates/${candidateId}/download`, {
                responseType: 'blob'
            })

            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url

            const contentDisposition = response.headers['content-disposition']
            let filename = `${candidate.name.replace(/\s+/g, '_')}_CV.pdf`
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
                if (filenameMatch && filenameMatch.length === 2)
                    filename = filenameMatch[1]
            }

            link.setAttribute('download', filename)
            document.body.appendChild(link)
            link.click()
            link.remove()
            window.URL.revokeObjectURL(url)

            toast.success("Download started")
        } catch (error: unknown) {
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

    const handleView = async () => {
        try {
            const response = await api.get(`/jobs/${jobId}/candidates/${candidateId}/download?inline=true`, {
                responseType: 'blob'
            })

            const file = new Blob([response.data], { type: 'application/pdf' })
            const fileURL = URL.createObjectURL(file)
            window.open(fileURL, '_blank')

        } catch (error: unknown) {
            if (isApiError(error) && error.response?.data instanceof Blob) {
                const text = await error.response.data.text()
                try {
                    const json = JSON.parse(text)
                    toast.error(json.detail || "Failed to view CV")
                } catch {
                    toast.error("Failed to view CV")
                }
            } else {
                toast.error(getErrorMessage(error))
            }
        }
    }

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <p className="text-muted-foreground">Loading candidate details...</p>
            </div>
        )
    }

    if (!candidate) {
        return (
            <div className="flex h-full items-center justify-center">
                <p className="text-muted-foreground">Candidate not found</p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <Button
                    variant="ghost"
                    size="sm"
                    className="mb-4"
                    onClick={() => router.push(`/jobs/${jobId}/candidates`)}
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Candidates
                </Button>

                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">{candidate.name}</h1>
                        <p className="text-muted-foreground">
                            Applied to: {job?.title}
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        {!candidate.is_readable && (
                            <Badge variant="destructive">Unreadable</Badge>
                        )}
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleView}
                            className="gap-2"
                        >
                            <Eye className="h-4 w-4" />
                            View CV
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleDownload}
                            className="gap-2"
                        >
                            <Download className="h-4 w-4" />
                            Download CV
                        </Button>
                    </div>
                </div>
            </div>

            {/* Contact Info */}
            <Card>
                <CardHeader>
                    <CardTitle>Contact Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                    {candidate.email && (
                        <div className="flex items-center gap-2">
                            <Mail className="h-4 w-4 text-muted-foreground" />
                            <span>{candidate.email}</span>
                        </div>
                    )}
                    {candidate.parsed_phone && (
                        <div className="flex items-center gap-2">
                            <Phone className="h-4 w-4 text-muted-foreground" />
                            <span>{candidate.parsed_phone}</span>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Ranking Score */}
            {candidate.ranking_score !== null && candidate.ranking_score !== undefined && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5" />
                            Ranking Score
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold text-primary">
                            {candidate.ranking_score}%
                        </div>
                        {candidate.ranking_explanation && (
                            <div className="mt-4">
                                <p className="text-sm font-medium mb-2">Explanation:</p>
                                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                                    {candidate.ranking_explanation}
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Skills */}
            {candidate.parsed_skills && candidate.parsed_skills.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Skills</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex flex-wrap gap-2">
                            {candidate.parsed_skills.map((skill: string, i: number) => (
                                <Badge key={i} variant="secondary">
                                    {skill}
                                </Badge>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* CV Text */}
            {candidate.extracted_text && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FileText className="h-5 w-5" />
                            Extracted CV Text
                        </CardTitle>
                        <CardDescription>
                            Full text extracted from the CV
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="whitespace-pre-wrap text-sm bg-muted p-4 rounded-md max-h-[600px] overflow-y-auto">
                            {candidate.extracted_text}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
