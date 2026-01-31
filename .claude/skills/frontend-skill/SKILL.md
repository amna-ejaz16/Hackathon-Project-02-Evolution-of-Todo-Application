---
name: frontend-skill
description: Build frontend pages, components, styling, and layouts for modern web applications.
---

# Frontend Skill – Pages, Components & Styling

## Instructions

1. **Page Layout**
   - Define overall page structure (header, main, footer)
   - Use responsive, mobile-first design
   - Organize content clearly for user flow

2. **Components**
   - Build reusable UI components (buttons, cards, modals)
   - Follow consistent naming and folder structure
   - Support props and dynamic content
   - Ensure accessibility (ARIA labels, focus management)

3. **Styling**
   - Use CSS, Tailwind, or CSS-in-JS consistently
   - Apply modern UI techniques (glassmorphism, gradients, shadows)
   - Ensure visual hierarchy and spacing
   - Support dark/light modes if applicable

4. **Animations & Interactivity**
   - Add subtle motion for hover, click, and transitions
   - Use Framer Motion for smooth animations
   - Avoid overwhelming the user with excessive effects

5. **State & Data Handling**
   - Pass data via props or state management
   - Connect components to backend APIs or context providers
   - Handle loading and error states gracefully

## Best Practices

- Keep components small and reusable
- Follow consistent naming conventions
- Maintain responsive design for all screen sizes
- Use semantic HTML for accessibility
- Document components clearly for reuse

## Example Component (React + Tailwind)

```tsx
export function Card({ title, description }: { title: string; description: string }) {
  return (
    <div className="bg-white/30 backdrop-blur-md rounded-xl p-4 shadow-md">
      <h2 className="text-xl font-bold">{title}</h2>
      <p className="text-gray-700">{description}</p>
    </div>
  );
}
