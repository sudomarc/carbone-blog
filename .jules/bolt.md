# Bolt's Journal

## 2026-07-21 - Eliminating Cumulative Layout Shift (CLS) on Dynamic Image Layouts
**Learning:** In lightweight, static blogs that fetch remote placeholder images (such as from Unsplash), Cumulative Layout Shift (CLS) is a major performance bottleneck. Without specifying explicit width and height on `<img>` tags, the browser cannot reserve space on initial paint, causing the page content to shift down as soon as the image loads. To solve this cleanly, we must pair the HTML `width` and `height` attributes with API-level image cropping/resizing queries (e.g., `&h=450&fit=crop`) to guarantee a stable 16:9 aspect ratio and precise pixel dimensions.
**Action:** Always enforce exact image dimensions in URL queries when fetching third-party images, and specify matching `width` and `height` attributes alongside `decoding="async"` on the HTML image tags.
