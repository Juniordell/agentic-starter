import { HTMLAttributes } from 'react'

type SpinnerSize = 'sm' | 'md' | 'lg'

interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: SpinnerSize
  className?: string
}

export function Spinner({ size = 'md', className = '', ...props }: SpinnerProps) {
  const sizes: Record<SpinnerSize, string> = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  }

  return (
    <div
      className={`animate-spin rounded-full border-2 border-gray-700 border-t-green-500 ${sizes[size]} ${className}`}
      role="status"
      aria-label="Loading"
      {...props}
    />
  )
}
