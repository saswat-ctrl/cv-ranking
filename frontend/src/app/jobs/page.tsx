"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Plus, Briefcase, Users, Search } from "lucide-react"
import { api } from "@/lib/api_client"
import { Job } from "@/types/api"

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

export default function JobsPage() {
    const router = useRouter()
    const [jobs, setJobs] = useState<Job[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [statusFilter, setStatusFilter] = useState("ALL")

    useEffect(() => {
        const token = localStorage.getItem("token")
        if (!token) {
            router.push("/login")
            return
        }

        fetchJobs()
        fetchJobs()
    }, [router])

    const fetchJobs = async () => {
        try {
            const response = await api.get("/jobs")
            const jobsData = response.data

            // Fetch candidate count for each job
            const jobsWithCounts = await Promise.all(
                jobsData.map(async (job: Job) => {
                    try {
                        const candidatesResponse = await api.get(`/jobs/${job.id}/candidates`)
                        return { ...job, candidate_count: candidatesResponse.data.length }
                    } catch {
                        return { ...job, candidate_count: 0 }
                    }
                })
            )

            setJobs(jobsWithCounts)
        } catch (error) {
            console.error("Failed to fetch jobs:", error)
        } finally {
            setLoading(false)
        }
    }

    // Filter jobs based on search query and status
    const filteredJobs = jobs.filter(job => {
        const matchesSearch = job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (job.extracted_text && job.extracted_text.toLowerCase().includes(searchQuery.toLowerCase()))

        const matchesStatus = statusFilter === "ALL" || (job.status || "OPEN") === statusFilter

        return matchesSearch && matchesStatus
    })

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <p className="text-muted-foreground">Loading jobs...</p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Jobs</h1>
                    <p className="text-muted-foreground">Manage your job postings and rankings</p>
                </div>
                <Link href="/jobs/new">
                    <Button size="lg" className="gap-2">
                        <Plus className="h-5 w-5" />
                        Create Job
                    </Button>
                </Link>
            </div>

            {/* Search and Filter */}
            {jobs.length > 0 && (
                <div className="flex gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input
                            placeholder="Search jobs by title or description..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10"
                        />
                    </div>
                    <Select
                        value={statusFilter}
                        onValueChange={setStatusFilter}
                    >
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Filter by Status" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="ALL">All Statuses</SelectItem>
                            <SelectItem value="OPEN">Open</SelectItem>
                            <SelectItem value="CLOSED">Closed</SelectItem>
                            <SelectItem value="DRAFT">Draft</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            )}

            {/* Jobs Grid */}
            {filteredJobs.length === 0 ? (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <Briefcase className="mb-4 h-16 w-16 text-muted-foreground" />
                        <h3 className="mb-2 text-xl font-semibold">
                            {searchQuery ? "No jobs found" : "No jobs yet"}
                        </h3>
                        <p className="mb-6 text-center text-muted-foreground">
                            {searchQuery
                                ? `No jobs match "${searchQuery}"`
                                : "Create your first job posting to start ranking candidates"}
                        </p>
                        {!searchQuery && (
                            <Link href="/jobs/new">
                                <Button size="lg">
                                    <Plus className="mr-2 h-5 w-5" />
                                    Create Your First Job
                                </Button>
                            </Link>
                        )}
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {filteredJobs.map((job) => (
                        <Card key={job.id} className="group cursor-pointer">
                            <Link href={`/jobs/${job.id}`}>
                                <CardHeader>
                                    <div className="flex items-start justify-between">
                                        <CardTitle className="line-clamp-1">{job.title}</CardTitle>
                                        <Badge variant={job.status === "open" ? "default" : "secondary"}>
                                            {job.status || "open"}
                                        </Badge>
                                    </div>
                                    <CardDescription className="line-clamp-2">
                                        {job.extracted_text?.substring(0, 100)}...
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                        <div className="flex items-center gap-1">
                                            <Users className="h-4 w-4" />
                                            <span>{job.candidate_count || 0} candidates</span>
                                        </div>
                                        <div>
                                            {new Date(job.created_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                    <div className="mt-4 flex gap-2">
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            className="flex-1"
                                            onClick={(e) => {
                                                e.preventDefault()
                                                router.push(`/jobs/${job.id}/upload`)
                                            }}
                                        >
                                            Upload CVs
                                        </Button>
                                        <Button
                                            size="sm"
                                            className="flex-1"
                                            onClick={(e) => {
                                                e.preventDefault()
                                                router.push(`/jobs/${job.id}/candidates`)
                                            }}
                                        >
                                            View Candidates
                                        </Button>
                                    </div>
                                </CardContent>
                            </Link>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    )
}
