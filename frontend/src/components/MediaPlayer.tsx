import { useEffect, useMemo, useRef, useState } from 'react'
import { Pause, Play, Volume2, VolumeX } from 'lucide-react'

type MediaPlayerProps = {
  fileUrl: string
  fileType: 'audio' | 'video'
  seekTime: number
}

export default function MediaPlayer({ fileUrl, fileType, seekTime }: MediaPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [isHovering, setIsHovering] = useState(false)
  const [isFloating, setIsFloating] = useState(false)
  const lastFileUrlRef = useRef(fileUrl)
  const hasMountedRef = useRef(false)
  const observerRef = useRef<IntersectionObserver | null>(null)

  const mediaRef = fileType === 'video' ? videoRef : audioRef

  const mediaElement = mediaRef.current

  const formatTime = (seconds: number) => {
    if (!Number.isFinite(seconds) || Number.isNaN(seconds)) return '00:00'
    const total = Math.max(0, Math.floor(seconds))
    const minutes = Math.floor(total / 60)
    const remainingSeconds = total % 60
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const syncMediaVolume = (nextVolume: number, nextMuted: boolean) => {
    if (!mediaElement) return
    mediaElement.volume = nextVolume
    mediaElement.muted = nextMuted
  }

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
          setIsPlaying(false)
        } else if (hasMountedRef.current) {
          void el.play()
          setIsPlaying(true)
        }
      } catch {
        // Autoplay may be blocked by browser policies; ignore.
      }
    }

    hasMountedRef.current = true
  }, [seekTime, fileType, fileUrl, mediaRef])

  useEffect(() => {
    const el = mediaRef.current
    if (!el) return

    const handleTimeUpdate = () => setCurrentTime(el.currentTime)
    const handleLoadedMetadata = () => {
      setDuration(Number.isFinite(el.duration) ? el.duration : 0)
      setCurrentTime(el.currentTime || 0)
    }
    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)
    const handleVolumeChange = () => {
      setVolume(el.volume)
      setIsMuted(el.muted || el.volume === 0)
    }

    el.addEventListener('timeupdate', handleTimeUpdate)
    el.addEventListener('loadedmetadata', handleLoadedMetadata)
    el.addEventListener('play', handlePlay)
    el.addEventListener('pause', handlePause)
    el.addEventListener('volumechange', handleVolumeChange)

    handleLoadedMetadata()
    handleVolumeChange()

    return () => {
      el.removeEventListener('timeupdate', handleTimeUpdate)
      el.removeEventListener('loadedmetadata', handleLoadedMetadata)
      el.removeEventListener('play', handlePlay)
      el.removeEventListener('pause', handlePause)
      el.removeEventListener('volumechange', handleVolumeChange)
    }
  }, [fileUrl, fileType, mediaRef])

  useEffect(() => {
    const node = containerRef.current
    if (!node) return

    observerRef.current?.disconnect()
    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        setIsFloating(!entry.isIntersecting && isPlaying)
      },
      { threshold: 0.2 },
    )

    observerRef.current.observe(node)

    return () => {
      observerRef.current?.disconnect()
      observerRef.current = null
    }
  }, [isPlaying, fileUrl, fileType])

  useEffect(() => {
    if (isPlaying && !isFloating && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect()
      if (rect.bottom < 0 || rect.top > window.innerHeight) {
        setIsFloating(true)
      }
    }

    if (!isPlaying) {
      setIsFloating(false)
    }
  }, [isPlaying, isFloating])

  useEffect(() => {
    const el = mediaRef.current
    if (!el) return

    syncMediaVolume(volume, isMuted)
  }, [volume, isMuted, mediaRef])

  useEffect(() => {
    if (!isPlaying) {
      setIsFloating(false)
    }
  }, [isPlaying])

  useEffect(() => {
    if (isFloating && containerRef.current) {
      containerRef.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }, [isFloating])

  const togglePlay = async () => {
    const el = mediaRef.current
    if (!el) return

    try {
      if (el.paused) {
        await el.play()
        setIsPlaying(true)
      } else {
        el.pause()
        setIsPlaying(false)
      }
    } catch {
      // Ignore autoplay restrictions.
    }
  }

  const handleScrub = (event: React.ChangeEvent<HTMLInputElement>) => {
    const nextTime = Number(event.target.value)
    const el = mediaRef.current
    if (!el) return

    el.currentTime = nextTime
    setCurrentTime(nextTime)
  }

  const toggleMute = () => {
    const nextMuted = !isMuted
    setIsMuted(nextMuted)
    if (nextMuted) {
      setVolume(mediaElement?.volume ?? volume)
      syncMediaVolume(volume, true)
    } else {
      const restoredVolume = volume <= 0 ? 1 : volume
      setVolume(restoredVolume)
      syncMediaVolume(restoredVolume, false)
    }
  }

  const floatingClassName = isFloating
    ? 'fixed bottom-6 right-6 z-50 w-80 overflow-hidden rounded-xl border border-zinc-800 shadow-2xl shadow-black/50 transition-all duration-300'
    : ''

  const containerClassName = isFloating
    ? `${floatingClassName} bg-zinc-950/95 backdrop-blur-md`
    : 'relative w-full'

  const progress = useMemo(() => {
    if (!duration) return 0
    return Math.min(100, Math.max(0, (currentTime / duration) * 100))
  }, [currentTime, duration])

  return (
    <div ref={containerRef} className={containerClassName} onMouseEnter={() => setIsHovering(true)} onMouseLeave={() => setIsHovering(false)}>
      {fileType === 'video' ? (
        <div className="relative shrink-0 max-h-72 w-full overflow-hidden bg-black">
          <video
            key={fileUrl}
            ref={videoRef}
            src={fileUrl}
            autoPlay={false}
            preload="metadata"
            onLoadedMetadata={() => videoRef.current?.pause()}
            className="block max-h-72 w-full object-contain"
          />

          <div
            className={`absolute inset-x-0 bottom-0 bg-zinc-950/80 backdrop-blur-md border-t border-zinc-800 px-3 py-3 transition-all duration-200 ${
              isHovering || isPlaying ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0'
            }`}
          >
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={togglePlay}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-900 text-zinc-200 transition-colors hover:bg-zinc-800 hover:text-white"
                aria-label={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </button>

              <div className="flex flex-1 items-center gap-3">
                <span className="text-xs text-zinc-400 w-14 shrink-0">{formatTime(currentTime)}</span>

                <input
                  type="range"
                  min={0}
                  max={duration || 0}
                  step="0.1"
                  value={currentTime}
                  onChange={handleScrub}
                  className="media-scrubber h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-zinc-800"
                  style={{
                    background: `linear-gradient(to right, rgb(168 85 247) 0%, rgb(168 85 247) ${progress}%, rgb(39 39 42) ${progress}%, rgb(39 39 42) 100%)`,
                  }}
                  aria-label="Seek"
                />

                <span className="text-xs text-zinc-400 w-14 shrink-0 text-right">{formatTime(duration)}</span>
              </div>

              <button
                type="button"
                onClick={toggleMute}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-900 text-zinc-200 transition-colors hover:bg-zinc-800 hover:text-white"
                aria-label={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted || volume === 0 ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="shrink-0 border-b border-zinc-800 bg-zinc-900 p-4">
          <audio
            key={fileUrl}
            ref={audioRef}
            src={fileUrl}
            autoPlay={false}
            preload="metadata"
            onLoadedMetadata={() => audioRef.current?.pause()}
            className="hidden"
          />

          <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 px-4 py-3 backdrop-blur-md">
            <div className="mb-3 flex items-center gap-3">
              <button
                type="button"
                onClick={togglePlay}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-900 text-zinc-200 transition-colors hover:bg-zinc-800 hover:text-white"
                aria-label={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </button>

              <div className="flex flex-1 items-center gap-3">
                <span className="text-xs text-zinc-400 w-14 shrink-0">{formatTime(currentTime)}</span>
                <input
                  type="range"
                  min={0}
                  max={duration || 0}
                  step="0.1"
                  value={currentTime}
                  onChange={handleScrub}
                  className="media-scrubber h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-zinc-800"
                  style={{
                    background: `linear-gradient(to right, rgb(168 85 247) 0%, rgb(168 85 247) ${progress}%, rgb(39 39 42) ${progress}%, rgb(39 39 42) 100%)`,
                  }}
                  aria-label="Seek"
                />
                <span className="text-xs text-zinc-400 w-14 shrink-0 text-right">{formatTime(duration)}</span>
              </div>

              <button
                type="button"
                onClick={toggleMute}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-900 text-zinc-200 transition-colors hover:bg-zinc-800 hover:text-white"
                aria-label={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted || volume === 0 ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
              </button>
            </div>

            <div className="text-xs text-zinc-500">Audio controls stay visible while you browse the conversation.</div>
          </div>
        </div>
      )}
    </div>
  )
}
