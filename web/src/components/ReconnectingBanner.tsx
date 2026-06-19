/**
 * Renders a visible banner while `candleStore` is in the
 * `'reconnecting'` state. Otherwise renders nothing.
 */

import { useSyncExternalStore } from 'react';
import { candleStore } from '../store';
import { colors, fontSizes, fontWeights, spacing } from '../design/tokens';

export const ReconnectingBanner: React.FC = () => {
  const status = useSyncExternalStore(candleStore.subscribe, candleStore.getSnapshot).status;

  if (status !== 'reconnecting') return null;

  return (
    <div
      data-testid="reconnecting-banner"
      role="status"
      style={{
        background: colors.reconnecting,
        color: '#000',
        fontFamily: 'Inter, sans-serif',
        fontSize: fontSizes.sm,
        fontWeight: fontWeights.semibold,
        padding: `${spacing.xs}px ${spacing.md}px`,
        textAlign: 'center',
        borderRadius: 6,
      }}
    >
      Reconnecting…
    </div>
  );
};
