import { useLayoutEffect, useRef, useState } from 'react'
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
  const toggleRef = useRef<HTMLDivElement | null>(null)
  const quickButtonRef = useRef<HTMLButtonElement | null>(null)
  const detailedButtonRef = useRef<HTMLButtonElement | null>(null)
  const [indicatorStyle, setIndicatorStyle] = useState<{ left: number; width: number } | null>(null)

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

  useLayoutEffect(() => {
    const updateIndicator = () => {
      const containerRect = toggleRef.current?.getBoundingClientRect()
      const activeButton = summaryType === 'short' ? quickButtonRef.current : detailedButtonRef.current
      const buttonRect = activeButton?.getBoundingClientRect()

      if (!containerRect || !buttonRect) {
        return
      }

      setIndicatorStyle({
        left: buttonRect.left - containerRect.left,
        width: buttonRect.width,
      })
    }

    updateIndicator()
    window.addEventListener('resize', updateIndicator)

    return () => window.removeEventListener('resize', updateIndicator)
  }, [summaryType])



  return (
    <div className="h-full overflow-y-auto bg-zinc-950 px-6 py-6 text-zinc-300">
      {isFile ? (
        <article className="mx-auto max-w-4xl rounded-3xl border border-zinc-800 bg-zinc-900/50 p-8">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3 text-purple-400">
              <FileText className="h-5 w-5" />
              <span className="text-sm font-semibold uppercase tracking-[0.22em]">Summary Report</span>
            </div>
            <div ref={toggleRef} className="relative inline-flex rounded-full border border-zinc-700 bg-zinc-900 p-1">
              <div
                className="absolute top-1 h-[calc(100%-0.5rem)] rounded-full bg-purple-600 shadow-[0_0_0_1px_rgba(168,85,247,0.18),0_10px_24px_rgba(147,51,234,0.28)] transition-[left,width] duration-500 ease-[cubic-bezier(0.22,1,0.36,1)]"
                style={{
                  left: indicatorStyle ? `${indicatorStyle.left}px` : '0.25rem',
                  width: indicatorStyle ? `${indicatorStyle.width}px` : '0px',
                }}
              />
              <button
                ref={quickButtonRef}
                type="button"
                onClick={() => generateSummary('short')}
                disabled={isGenerating}
                className="relative z-10 inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition-colors duration-300 disabled:cursor-wait"
                style={{ color: summaryType === 'short' ? 'white' : '#d4d4d8' }}
              >
                <Zap className="h-3.5 w-3.5" />
                Quick Summary
              </button>
              <button
                ref={detailedButtonRef}
                type="button"
                onClick={() => generateSummary('detailed')}
                disabled={isGenerating}
                className="relative z-10 inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition-colors duration-300 disabled:cursor-wait"
                style={{ color: summaryType === 'detailed' ? 'white' : '#d4d4d8' }}
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
