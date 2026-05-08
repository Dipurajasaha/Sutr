export type FileSystemItem = {
  id: string
  name: string
  type: 'file' | 'folder'
  fileType?: 'pdf' | 'video' | 'audio'
  filePath?: string
  children?: FileSystemItem[]
  isOpen?: boolean
}
