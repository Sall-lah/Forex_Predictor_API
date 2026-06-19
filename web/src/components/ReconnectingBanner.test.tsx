import { render, screen, act } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ReconnectingBanner } from './ReconnectingBanner';
import { candleStore } from '../store';

describe('ReconnectingBanner', () => {
  it('is visible when status is reconnecting', () => {
    act(() => {
      candleStore.setStatus('reconnecting');
    });

    render(<ReconnectingBanner />);

    expect(screen.getByTestId('reconnecting-banner')).toBeInTheDocument();
    expect(screen.getByText('Reconnecting…')).toBeInTheDocument();
  });

  it('is hidden when status is live', () => {
    act(() => {
      candleStore.setStatus('open');
    });

    render(<ReconnectingBanner />);

    expect(screen.queryByTestId('reconnecting-banner')).not.toBeInTheDocument();
  });
});
