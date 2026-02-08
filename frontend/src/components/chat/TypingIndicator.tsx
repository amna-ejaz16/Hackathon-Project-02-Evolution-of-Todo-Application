"use client";

import { motion } from "framer-motion";

/**
 * TypingIndicator - Animated three-dot loading indicator
 *
 * Features:
 * - Three purple dots with staggered scale animation
 * - Infinite loop with smooth easing
 * - Wrapped in assistant-style bubble
 */
export default function TypingIndicator() {
  return (
    <div className="flex items-start mb-4">
      {/* Assistant-style bubble container */}
      <div
        className="mr-auto rounded-2xl rounded-bl-md px-5 py-4"
        style={{
          background: "rgba(17, 17, 24, 0.85)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          border: "1px solid rgba(168, 85, 247, 0.2)",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.2)",
        }}
      >
        {/* Three animated dots */}
        <div className="flex items-center gap-1.5">
          {[0, 1, 2].map((index) => (
            <motion.div
              key={index}
              className="w-2 h-2 rounded-full bg-purple-400"
              animate={{
                scale: [1, 1.3, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: index * 0.15,
                ease: "easeInOut",
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
