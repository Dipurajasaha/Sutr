import { useEffect, useRef } from 'react'

type MediaPlayerProps = {
  fileUrl: string
  fileType: 'audio' | 'video'
  seekTime: number
}

export default function MediaPlayer({ fileUrl, fileType, seekTime }: MediaPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const lastFileUrlRef = useRef(fileUrl)
  const hasMountedRef = useRef(false)

  const mediaRef = fileType === 'video' ? videoRef : audioRef

  useEffect(() => {
    const el = mediaRef.current
    if (!el) return

    const fileChanged = lastFileUrlRef.current !== fileUrl
    if (fileChanged) {
      lastFileUrlRef.current = fileUrl
    }

    // If seekTime is a valid number, update currentTime.
    // Only play on subsequent seek updates, not when a file is first selected.
    if (!Number.isNaN(seekTime) && typeof seekTime === 'number') {
      try {
        el.currentTime = Math.max(0, seekTime)
        if (fileChanged) {
          el.pause()
        } else if (hasMountedRef.current) {
          void el.play()
        }
      } catch {
        // Autoplay may be blocked by browser policies; ignore.
      }
    }

    hasMountedRef.current = true
  }, [seekTime, fileType, fileUrl, mediaRef])

  return (
    <>
      {fileType === 'video' ? (
        <div className="shrink-0 max-h-72 w-full overflow-hidden bg-black">
          <video
            key={fileUrl}
            ref={videoRef}
            src={fileUrl}
            controls
            autoPlay={false}
            preload="metadata"
            onLoadedMetadata={() => videoRef.current?.pause()}
            className="block max-h-72 w-full object-contain"
          />
        </div>
      ) : (
        <div className="shrink-0 border-b border-zinc-800 bg-zinc-900 p-4">
          <audio
            key={fileUrl}
            ref={audioRef}
            src={fileUrl}
            controls
            autoPlay={false}
            preload="metadata"
            onLoadedMetadata={() => audioRef.current?.pause()}
            className="block w-full"
          />
        </div>
      )}
    </>
  )
}
