# Security and Performance

The security and performance architecture ensures enterprise-grade protection and optimal user experience across all client implementations while supporting the revolutionary agent-based permission system.

## Security Requirements

### Frontend Security
- **CSP Headers:** `default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.*.com.br wss://api.*.com.br`
- **XSS Prevention:** React's built-in XSS protection + DOMPurify for user-generated content + Content Security Policy enforcement
- **Secure Storage:** JWT tokens in httpOnly cookies for production, encrypted localStorage for development, sensitive data never in localStorage

### Backend Security
- **Input Validation:** Comprehensive Pydantic schemas with field validation + SQLModel constraints + validate-docbr for Brazilian document validation + file type/size validation
- **Rate Limiting:** Tiered limits: 100 requests/min (users), 500 requests/min (admins), 1000 requests/min (sysadmins) with Redis-based tracking
- **CORS Policy:** `https://*.com.br, https://iam-dashboard.com.br` with credentials support, preflight caching for 24 hours

### Authentication Security
- **Token Storage:** Production: httpOnly cookies with secure, sameSite flags; Development: encrypted localStorage with 1-hour expiration
- **Session Management:** JWT access tokens (1 hour) + refresh tokens (30 days) with automatic rotation, Redis-based session tracking, concurrent session limits (5 per user)
- **Password Policy:** Minimum 12 characters, mixed case + numbers + symbols, bcrypt hashing (12 rounds), password history (5 previous), account lockout after 5 failed attempts

## Performance Optimization

### Frontend Performance
- **Bundle Size Target:** Initial bundle <150KB gzipped, total JavaScript <500KB with code splitting by route and permission level
- **Loading Strategy:** Critical CSS inlined, progressive font loading with fallbacks, image optimization with Next.js Image component, lazy loading for non-critical components
- **Caching Strategy:** Static assets cached for 1 year, API responses cached for 5 minutes with SWR, permission data cached for 5 minutes with immediate invalidation

### Backend Performance
- **Response Time Target:** <200ms for API endpoints, <10ms for permission validation (Redis), <500ms for complex queries (database optimization)
- **Database Optimization:** Connection pooling (10-20 connections), query optimization with indexes, read replicas for reporting, prepared statements for security
- **Caching Strategy:** Redis for permissions (5-min TTL), query result caching (1-min TTL), session data (1-hour TTL), static data (1-day TTL)

---
