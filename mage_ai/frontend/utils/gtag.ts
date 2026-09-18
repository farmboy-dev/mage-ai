import type { EventParametersType } from '@interfaces/EventPropertiesType';

// Compatibility hooks: browser analytics are removed from the internal build.
export const logGAPageview = (_params?: { href?: string; title?: string }) => {};
export const logGAEvent = (_eventName: string, _eventParameters: EventParametersType) => {};
export const logUserOS = () => {};
