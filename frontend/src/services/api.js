import * as crawler from './api/crawler';
import * as events from './api/events';
import * as metrics from './api/metrics';
import * as privacy from './api/privacy';
import * as reviews from './api/reviews';
import * as rules from './api/rules';
import * as verification from './api/verification';

// Keep the existing api object as a stable boundary for view components.
export const api = {
  ...crawler,
  ...events,
  ...metrics,
  ...privacy,
  ...reviews,
  ...rules,
  ...verification,
};
