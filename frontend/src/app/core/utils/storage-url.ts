import { environment } from '../../../environments/environment';

/**
 * Normalizes image URLs coming from the backend.
 *
 * The backend django-storages config produces malformed URLs
 * (double protocol, e.g. "http//http://host/bucket//path") because
 * AWS_S3_CUSTOM_DOMAIN already contains the scheme while
 * AWS_S3_URL_PROTOCOL prepends another one.
 *
 * This function extracts the storage-relative path and rebuilds a
 * correct absolute URL using the environment storageBase.
 */
export function normalizeStorageUrl(url: string | null | undefined): string {
    if (!url) return '';
    // Already a well-formed absolute URL — use as-is
    if (/^https?:\/\/[^/]/.test(url)) return url;
    // Extract the storage-relative path from the malformed URL
    const match = url.match(/(profile_images\/.+)$/);
    if (match) return `${environment.storageBase}/${match[1]}`;
    // Fallback: treat whatever we got as a relative path
    return `${environment.storageBase}/${url}`;
}
