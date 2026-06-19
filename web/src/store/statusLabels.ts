/**
 * Shared status label mapping used by both `StatusBar` and
 * `CandlesPage` so the labels cannot drift between components.
 */

import type { LiveStatus } from './types';

export const STATUS_LABEL: Record<LiveStatus, string> = {
  idle: 'Idle',
  connecting: 'Connecting',
  open: 'Live',
  closed: 'Closed',
  reconnecting: 'Reconnecting',
};
