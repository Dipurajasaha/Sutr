import DOMPurify from 'dompurify'
import { marked } from 'marked'

type MarkdownBlockProps = {
  content: string
  className?: string
}

const markedOptions = {
  breaks: true,
  gfm: true,
}

export default function MarkdownBlock({ content, className = '' }: MarkdownBlockProps) {
  const html = DOMPurify.sanitize(marked.parse(content, markedOptions) as string)

  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />
}