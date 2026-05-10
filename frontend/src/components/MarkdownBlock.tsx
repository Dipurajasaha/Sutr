import { useState, useMemo } from 'react'
import { marked } from 'marked'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check } from 'lucide-react'
import DOMPurify from 'dompurify'

type MarkdownBlockProps = {
  content: string
  className?: string
}

// Custom code block renderer
function CodeBlock({ code, language }: { code: string; language?: string }) {
  const [isCopied, setIsCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    })
  }

  const lang = language || 'plaintext'

  return (
    <div className="group relative my-4 rounded-lg bg-zinc-900 overflow-hidden border border-zinc-800">
      <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
        <div className="text-xs text-zinc-400 bg-zinc-950/90 px-2 py-1 rounded font-mono">{lang}</div>
        <button
          onClick={handleCopy}
          className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1.5 rounded bg-zinc-950/90 hover:bg-zinc-800 text-zinc-400 hover:text-white"
          title="Copy code"
          type="button"
        >
          {isCopied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
        </button>
      </div>

      <SyntaxHighlighter
        language={lang}
        style={atomDark}
        customStyle={{
          margin: 0,
          padding: '1rem',
          fontSize: '0.875rem',
          lineHeight: '1.5',
          backgroundColor: 'transparent',
          paddingRight: '5rem',
        }}
        wrapLongLines
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}

export default function MarkdownBlock({ content, className = '' }: MarkdownBlockProps) {
  const { htmlContent, codeBlocks } = useMemo(() => {
    const blocks: Array<{ id: string; code: string; language: string }> = []
    let blockIndex = 0

    const renderer = new marked.Renderer()
    renderer.code = ({ text, lang }) => {
      const id = `code-${blockIndex++}`
      blocks.push({ id, code: text, language: lang || 'plaintext' })
      return `<div class="code-block-placeholder" id="${id}"></div>`
    }

    const html = marked.parse(content, {
      breaks: true,
      gfm: true,
      renderer,
    }) as string

    return {
      htmlContent: DOMPurify.sanitize(html),
      codeBlocks: blocks,
    }
  }, [content])

  return (
    <MarkdownRenderer html={htmlContent} codeBlocks={codeBlocks} className={className} />
  )
}

function MarkdownRenderer({
  html,
  codeBlocks,
  className,
}: {
  html: string
  codeBlocks: Array<{ id: string; code: string; language: string }>
  className?: string
}) {
  // Create a map of code block IDs to components
  const codeBlockMap = Object.fromEntries(
    codeBlocks.map((block) => [
      block.id,
      <CodeBlock key={block.id} code={block.code} language={block.language} />,
    ]),
  )

  // Split HTML by code block placeholders
  const parts: Array<{ type: 'html' | 'code'; id?: string; html?: string }> = []
  const regex = /<div class="code-block-placeholder" id="(code-\d+)"><\/div>/g

  let lastIndex = 0
  let match

  while ((match = regex.exec(html)) !== null) {
    // Add HTML before the match
    if (match.index > lastIndex) {
      parts.push({ type: 'html', html: html.substring(lastIndex, match.index) })
    }
    // Add the code block reference
    parts.push({ type: 'code', id: match[1] })
    lastIndex = match.index + match[0].length
  }

  // Add remaining HTML
  if (lastIndex < html.length) {
    parts.push({ type: 'html', html: html.substring(lastIndex) })
  }

  return (
    <div
      className={`prose prose-invert max-w-none prose-code:bg-zinc-900 prose-code:text-purple-300 prose-code:rounded prose-code:px-1.5 prose-code:py-0.5 prose-a:text-purple-400 prose-a:hover:text-purple-300 ${className}`}
    >
      {parts.map((part, idx) => {
        if (part.type === 'code' && part.id) {
          return codeBlockMap[part.id] || null
        }
        return (
          <div key={idx} dangerouslySetInnerHTML={{ __html: part.html || '' }} />
        )
      })}
    </div>
  )
}