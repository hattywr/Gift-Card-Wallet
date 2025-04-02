// src/theme/index.ts
export const theme = {
    colors: {
      primary: '#007AFF',
      secondary: '#5856D6',
      background: '#FFFFFF',
      text: '#000000',
      gray: '#8E8E93',
      error: '#FF3B30',
      success: '#34C759',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
    },
    typography: {
      h1: {
        fontSize: 28,
        fontWeight: 'bold' as const,
      },
      h2: {
        fontSize: 24,
        fontWeight: 'bold' as const,
      },
      body: {
        fontSize: 16,
      },
    },
  } as const;
  
  export type Theme = typeof theme;