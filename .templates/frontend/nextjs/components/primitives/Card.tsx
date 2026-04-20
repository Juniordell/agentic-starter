import { HTMLAttributes } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  className?: string
}

export function Card({ className = '', children, ...props }: CardProps) {
  return (
    <div
      className={`rounded-lg border border-gray-800 bg-gray-900 p-4 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
