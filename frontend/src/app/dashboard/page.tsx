"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Briefcase, Users, TrendingUp, Plus } from "lucide-react"
import { api } from "@/lib/api_client"
import { Job } from "@/types/api"

export default function Dashboard() {
  const router = useRouter()
  const [stats, setStats] = useState({ totalJobs: 0, totalCandidates: 0, avgScore: 0 })
  const [recentJobs, setRecentJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }

    // Fetch dashboard data
    fetchDashboardData()
  }, [router])

  const fetchDashboardData = async () => {
    try {
      const response = await api.get("/jobs/")
      const jobs = response.data

      // Fetch candidate counts for all jobs
      let totalCandidates = 0
      for (const job of jobs) {
        try {
          const candidatesResponse = await api.get(`/jobs/${job.id}/candidates/`)
          totalCandidates += candidatesResponse.data.length
        } catch {
          // If fetching candidates fails, just skip
        }
      }

      setStats({
        totalJobs: jobs.length,
        totalCandidates: totalCandidates,
        avgScore: 85, // Placeholder - would need to calculate from all rankings
      })

      setRecentJobs(jobs.slice(0, 5))
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Welcome to HR CV Shortlisting</p>
          <p className="text-xs text-gray-400 mt-1">
            Debug: Token is {typeof window !== 'undefined' && localStorage.getItem('token') ? 'Present' : 'Missing'}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={async () => {
              const token = localStorage.getItem('token');
              const cookieToken = typeof document !== 'undefined' ? document.cookie : '';
              alert(`Debug Info:\nToken (LS): ${token ? token.slice(0, 10) + '...' : 'Missing'}\nCookie: ${cookieToken.includes('token') ? 'Present' : 'Missing'}`);

              try {
                await api.get('/jobs/');
                alert('Connection Test: SUCCESS (Protected API works)');
              } catch (e: any) {
                alert(`Connection Test: FAILED\n${e.message}\nStatus: ${e.response?.status}`);
              }
            }}
          >
            Test Auth
          </Button>
          <Link href="/jobs/new">
            <Button size="lg" className="gap-2">
              <Plus className="h-5 w-5" />
              Create New Job
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Widgets */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalJobs}</div>
            <p className="text-xs text-muted-foreground">Active job postings</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Candidates Ranked</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalCandidates}</div>
            <p className="text-xs text-muted-foreground">CVs processed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Match Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avgScore}%</div>
            <p className="text-xs text-muted-foreground">Across all rankings</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Jobs</CardTitle>
          <CardDescription>Your most recently created job postings</CardDescription>
        </CardHeader>
        <CardContent>
          {recentJobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Briefcase className="mb-4 h-12 w-12 text-muted-foreground" />
              <p className="mb-2 text-lg font-medium">No jobs yet</p>
              <p className="mb-4 text-sm text-muted-foreground">
                Create your first job to start ranking candidates
              </p>
              <Link href="/jobs/new">
                <Button>Create Job</Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recentJobs.map((job) => (
                <Link
                  key={job.id}
                  href={`/jobs/${job.id}`}
                  className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-accent"
                >
                  <div className="flex-1">
                    <h4 className="font-medium">{job.title}</h4>
                    <p className="text-sm text-muted-foreground">
                      Created {new Date(job.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary">
                      {job.status || "OPEN"}
                    </Badge>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
