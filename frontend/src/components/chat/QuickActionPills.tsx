'use client'

import { motion } from 'framer-motion'

interface QuickActionPillsProps {
  onPillClick: (message: string) => void
  disabled: boolean
}

interface Pill {
  label: string
  message: string
}

const pills: Pill[] = [
  { label: 'Show all tasks', message: 'Show all my tasks' },
  { label: 'Add a task', message: 'I want to add a new task' },
  { label: "What's overdue?", message: 'Show me overdue tasks' },
]

export default function QuickActionPills({ onPillClick, disabled }: QuickActionPillsProps) {
  return (
    <div className="flex flex-wrap gap-2 px-4 py-2">
      {pills.map((pill) => (
        <motion.button
          key={pill.label}
          whileHover={{ scale: 1.05, y: -1 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onPillClick(pill.message)}
          disabled={disabled}
          className={`
            rounded-full px-3 py-1.5 text-xs font-medium
            border border-purple-500/30 bg-purple-500/10 text-purple-300
            hover:bg-purple-500/20 transition-colors cursor-pointer
            ${disabled ? 'opacity-50 pointer-events-none' : ''}
          `}
        >
          {pill.label}
        </motion.button>
      ))}
    </div>
  )
}
