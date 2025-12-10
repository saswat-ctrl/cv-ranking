"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Upload, Users, ArrowLeft, Trash2, Edit } from "lucide-react"
import { api } from "@/lib/api_client"
import { Job, Candidate, getErrorMessage } from "@/types/api"
import { toast } from "react-hot-toast"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

export default function JobDetailPage() {
    const params = useParams()
    const router = useRouter()
    const jobId = params.id as string

    const [job, setJob] = useState<Job | null>(null)
    const [candidates, setCandidates] = useState<Candidate[]>([])
    const [loading, setLoading] = useState(true)
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
    const [deleting, setDeleting] = useState(false)

    // Edit State
    const [editDialogOpen, setEditDialogOpen] = useState(false)
    const [updating, setUpdating] = useState(false)
    const [editForm, setEditForm] = useState({
        title: "",
        description: "",
        status: "OPEN"
    })

    useEffect(() => {
        const token = localStorage.getItem("token")
        if (!token) {
            router.push("/login")
            return
        }

        fetchJobDetails()
    }, [jobId, router])

    const fetchJobDetails = async () => {
        try {
            const [jobResponse, candidatesResponse] = await Promise.all([
                api.get(`/jobs/${jobId}`),
                api.get(`/jobs/${jobId}/candidates`)
            ])

            setJob(jobResponse.data)
            setEditForm({
                title: jobResponse.data.title,
                description: jobResponse.data.extracted_text || "",
                status: jobResponse.data.status || "OPEN"
            })
            setCandidates(candidatesResponse.data)
        } catch (error) {
            console.error("Failed to fetch job details:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleUpdate = async () => {
        setUpdating(true)
        try {
            const response = await api.patch(`/jobs/${jobId}`, editForm)
            setJob(response.data)
            toast.success("Job updated successfully")
            setEditDialogOpen(false)
        } catch (error: unknown) {
            toast.error(getErrorMessage(error))
        } finally {
            setUpdating(false)
        }
    }

    const handleDelete = async () => {
        setDeleting(true)
        try {
            await api.delete(`/jobs/${jobId}`)
            toast.success("Job deleted successfully")
            router.push("/jobs")
        } catch (error: unknown) {
            toast.error(getErrorMessage(error))
        } finally {
            setDeleting(false)
        }
    }

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <p className="text-muted-foreground">Loading job details...</p>
            </div>
        )
    }

    if (!job) {
        return (
            <div className="flex h-full items-center justify-center">
                <p className="text-muted-foreground">Job not found</p>
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
                    onClick={() => router.push("/jobs")}
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Jobs
                </Button>

                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">{job.title}</h1>
                        <p className="text-muted-foreground">
                            Created {new Date(job.created_at).toLocaleDateString()}
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <Badge variant={job.status === "open" ? "default" : "secondary"}>
                            {job.status || "open"}
                        </Badge>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setEditDialogOpen(true)}
                            className="gap-2"
                        >
                            <Edit className="h-4 w-4" />
                            Edit Job
                        </Button>
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => setDeleteDialogOpen(true)}
                            className="gap-2"
                        >
                            <Trash2 className="h-4 w-4" />
                            Delete Job
                        </Button>
                    </div>
                </div>
            </div>

            {/* Edit Dialog */}
            <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
                <DialogContent className="sm:max-w-[600px]">
                    <DialogHeader>
                        <DialogTitle>Edit Job</DialogTitle>
                        <DialogDescription>
                            Update job details and status.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label htmlFor="title">Job Title</Label>
                            <Input
                                id="title"
                                value={editForm.title}
                                onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="status">Status</Label>
                            <Select
                                value={editForm.status}
                                onValueChange={(value) => setEditForm({ ...editForm, status: value })}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="OPEN">Open</SelectItem>
                                    <SelectItem value="CLOSED">Closed</SelectItem>
                                    <SelectItem value="DRAFT">Draft</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="description">Job Description</Label>
                            <Textarea
                                id="description"
                                value={editForm.description}
                                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                                className="h-[200px]"
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setEditDialogOpen(false)}
                            disabled={updating}
                        >
                            Cancel
                        </Button>
                        <Button onClick={handleUpdate} disabled={updating}>
                            {updating ? "Updating..." : "Save Changes"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Job?</DialogTitle>
                        <DialogDescription>
                            This will permanently delete &quot;{job.title}&quot; and all {candidates.length} candidate{candidates.length !== 1 ? "s" : ""}.
                            This action cannot be undone.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setDeleteDialogOpen(false)}
                            disabled={deleting}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={handleDelete}
                            disabled={deleting}
                        >
                            {deleting ? "Deleting..." : "Delete Job"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Quick Actions */}
            <div className="grid gap-4 md:grid-cols-2">
                <Card className="cursor-pointer transition-shadow hover:shadow-md">
                    <Link href={`/jobs/${jobId}/upload`}>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Upload CVs</CardTitle>
                            <Upload className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <p className="text-xs text-muted-foreground">
                                Add candidate resumes
                            </p>
                        </CardContent>
                    </Link>
                </Card>

                <Card className="cursor-pointer transition-shadow hover:shadow-md">
                    <Link href={`/jobs/${jobId}/candidates`}>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Candidates</CardTitle>
                            <Users className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{candidates.length}</div>
                            <p className="text-xs text-muted-foreground">
                                View, rank, and manage candidates
                            </p>
                        </CardContent>
                    </Link>
                </Card>
            </div>

            {/* Job Description */}
            <Card>
                <CardHeader>
                    <CardTitle>Job Description</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="whitespace-pre-wrap text-sm">
                        {job.extracted_text || "No description available"}
                    </div>
                </CardContent>
            </Card>

            {/* Recent Candidates */}
            {candidates.length > 0 && (
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle>Recent Candidates</CardTitle>
                            <Link href={`/jobs/${jobId}/candidates`}>
                                <Button variant="outline" size="sm">View All</Button>
                            </Link>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {candidates.slice(0, 5).map((candidate) => (
                                <div
                                    key={candidate.id}
                                    className="flex items-center justify-between rounded-lg border p-3"
                                >
                                    <div>
                                        <p className="font-medium">{candidate.name}</p>
                                        <p className="text-sm text-muted-foreground">{candidate.email}</p>
                                    </div>
                                    <Badge variant="secondary">
                                        {candidate.ranking_score ? `${candidate.ranking_score}%` : "Not ranked"}
                                    </Badge>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
