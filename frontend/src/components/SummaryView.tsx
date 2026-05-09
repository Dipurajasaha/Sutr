import { useState } from 'react'
import axios from 'axios'
import { FileText, AlertCircle, Zap } from 'lucide-react'
import { apiClient } from '../api/client'
import type { FileSystemItem } from './types'
import MarkdownBlock from './MarkdownBlock'

type SummaryViewProps = {
  activeFile: FileSystemItem | null
}

type SummaryResponse = {
  summary: string
  summary_type: 'short' | 'detailed'
}

function SummaryLoadingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="h-8 w-48 animate-pulse rounded bg-zinc-800" />
      <div className="space-y-2">
        <div className="h-4 w-full animate-pulse rounded bg-zinc-800" />
        <div className="h-4 w-full animate-pulse rounded bg-zinc-800" />
        <div className="h-4 w-3/4 animate-pulse rounded bg-zinc-800" />
      </div>
      <div className="space-y-2 pt-4">
        <div className="h-4 w-40 animate-pulse rounded bg-zinc-800" />
        <div className="space-y-2">
          <div className="h-4 w-full animate-pulse rounded bg-zinc-800" />
          <div className="h-4 w-full animate-pulse rounded bg-zinc-800" />
          <div className="h-4 w-5/6 animate-pulse rounded bg-zinc-800" />
        </div>
      </div>
    </div>
  )
}

export default function SummaryView({ activeFile }: SummaryViewProps) {
  const isFile = activeFile?.type === 'file'
  const [summaryData, setSummaryData] = useState<string>('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string>('')
  const [summaryType, setSummaryType] = useState<'short' | 'detailed'>('short')

  const generateSummary = async (type: 'short' | 'detailed') => {
    if (!isFile || !activeFile) return

    setSummaryType(type)
    setIsGenerating(true)
    setError('')
    setSummaryData('')

    try {
      const response = await apiClient.post<SummaryResponse>('/api/summary/generate', {
        file_id: activeFile.id,
        summary_type: type,
      })

      setSummaryData(response.data.summary)
    } catch (err) {
      const errorMessage =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? typeof err.response.data.detail === 'string'
            ? err.response.data.detail
            : 'Failed to generate summary'
          : err instanceof Error
            ? err.message
            : 'An error occurred while generating the summary'

      setError(errorMessage)
    } finally {
      setIsGenerating(false)
    }
  }



  return (
    <div className="h-full overflow-y-auto bg-zinc-950 px-6 py-6 text-zinc-300">
      {isFile ? (
        <article className="mx-auto max-w-4xl rounded-3xl border border-zinc-800 bg-zinc-900/50 p-8">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3 text-purple-400">
              <FileText className="h-5 w-5" />
              <span className="text-sm font-semibold uppercase tracking-[0.22em]">Summary Report</span>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => generateSummary('short')}
                disabled={isGenerating}
                className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  summaryType === 'short'
                    ? 'bg-purple-600 text-white'
                    : 'border border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800'
                } disabled:opacity-50`}
              >
                <Zap className="h-3.5 w-3.5" />
                Quick Summary
              </button>
              <button
                type="button"
                onClick={() => generateSummary('detailed')}
                disabled={isGenerating}
                className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  summaryType === 'detailed'
                    ? 'bg-purple-600 text-white'
                    : 'border border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800'
                } disabled:opacity-50`}
              >
                <FileText className="h-3.5 w-3.5" />
                Detailed Notes
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-6 flex gap-3 rounded-xl border border-red-500/50 bg-red-500/10 p-4">
              <AlertCircle className="h-5 w-5 shrink-0 text-red-400" />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          {isGenerating ? (
            <div className="py-8">
              <SummaryLoadingSkeleton />
            </div>
          ) : summaryData ? (
            <div className="prose prose-invert max-w-none">
              <MarkdownBlock className="text-base leading-relaxed text-zinc-300" content={summaryData} />
            </div>
          ) : (
            <div className="py-8 text-center text-zinc-500">
              Click a button to generate a summary
            </div>
          )}
        </article>
      ) : (
        <div className="flex h-full items-center justify-center text-zinc-500">
          Select a file to view the summary.
        </div>
      )}
    </div>
  )
}
