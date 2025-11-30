import { cva } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const progressTrack = cva('relative h-2 w-full overflow-hidden rounded-full bg-muted')

export const Progress = ({ value }: { value: number }) => {
  return (
    <div className={progressTrack()} role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
      <div className={cn('h-full bg-primary transition-all')} style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} />
    </div>
  )
}
