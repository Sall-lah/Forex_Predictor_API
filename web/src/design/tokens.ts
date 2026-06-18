/**
 * Design tokens for the candlestick frontend.
 *
 * Single source of truth for colour, spacing, type, and radii. Components
 * should import these constants directly (preferred) or the matching CSS
 * custom properties defined in `index.css`.
 */

export const colors = {
  surface: '#0e0e0e',
  surfaceElevated: '#191a1a',
  border: '#252626',
  borderStrong: '#484848',
  textPrimary: '#e7e5e4',
  textMuted: '#767575',
  textSubtle: '#acabaa',
  bull: '#00d9a4',
  bear: '#ee7d77',
  info: '#7ab8ff',
  warning: '#f0b252',
  reconnecting: '#f0b252',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

export const radii = {
  sm: 4,
  md: 8,
  lg: 12,
  pill: 999,
} as const;

export const fontSizes = {
  xs: 11,
  sm: 12,
  md: 14,
  lg: 16,
  xl: 20,
  xxl: 28,
} as const;

export const fontWeights = {
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

// Backwards-compatible alias used in some components.
export const weights = fontWeights;

export type ColorToken = keyof typeof colors;
export type SpacingToken = keyof typeof spacing;
