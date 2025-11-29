# Mkweli GitHub Pages Documentation

This folder contains the GitHub Pages site for [mkweli.tech](https://mkweli.tech).

## 📁 File Structure

```
docs/
├── index.html      # Main landing page (self-contained HTML/CSS)
├── _config.yml     # Jekyll configuration
├── CNAME           # Custom domain configuration
└── README.md       # This file
```

## 🚀 How GitHub Pages Works

1. **Source**: GitHub Pages serves content from the `docs/` folder on the `main` branch
2. **Build**: Jekyll processes the files (minimal processing since we use static HTML)
3. **Deploy**: Content is deployed to `mkweli.tech` (custom domain) or `gilbertbouic.github.io/Mkweli`

### Enabling GitHub Pages

1. Go to repository **Settings** → **Pages**
2. Under "Source", select:
   - Branch: `main`
   - Folder: `/docs`
3. Click **Save**
4. Wait 1-2 minutes for initial deployment

## ✏️ Updating Content

### Updating the Landing Page

Edit `docs/index.html` directly. The page is self-contained with:
- All CSS embedded in `<style>` tags
- All JavaScript embedded in `<script>` tags
- No external dependencies (except Formspree for forms)

### Common Updates

| What to Change | Where to Edit |
|----------------|---------------|
| Hero text | Search for `<header class="hero">` |
| Story section | Search for `id="story"` |
| Timeline dates | Search for `class="timeline-date"` |
| Features | Search for `class="features-grid"` |
| Comparison table | Search for `class="comparison-table"` |
| Contact info | Search for `id="contact"` |
| Footer links | Search for `class="footer"` |

### Styling Changes

All CSS is in the `<style>` block in `<head>`. Key variables:

```css
:root {
    --primary-blue: #1e40af;      /* Main brand color */
    --accent-green: #059669;       /* Accent/CTA color */
    --text-dark: #1f2937;          /* Body text */
    --text-light: #6b7280;         /* Secondary text */
}
```

## 🌐 Custom Domain Configuration

### Current Setup
- Domain: `mkweli.tech`
- CNAME file contains: `mkweli.tech`

### DNS Configuration (at your registrar)

Add these DNS records at your domain registrar:

**For apex domain (mkweli.tech):**

| Type | Name | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |

**For www subdomain (optional):**

| Type | Name | Value |
|------|------|-------|
| CNAME | www | gilbertbouic.github.io |

### Enabling HTTPS

1. After DNS propagates (can take up to 48 hours)
2. Go to repository **Settings** → **Pages**
3. Check "Enforce HTTPS"

## 📬 Contact Form (Formspree)

### Current Setup

The contact form uses [Formspree](https://formspree.io) for free form handling.

**Form endpoint:** `https://formspree.io/f/xwpkvwwz`

### Setting Up Your Own Formspree

1. Create account at [formspree.io](https://formspree.io)
2. Create a new form
3. Copy your form endpoint
4. Update `action` attribute in `index.html`:

```html
<form class="contact-form" action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
```

### Form Fields

| Field | Name Attribute | Required |
|-------|---------------|----------|
| Name | `name` | Yes |
| Email | `email` | Yes |
| Organization | `organization` | No |
| Subject | `subject` | Yes |
| Message | `message` | Yes |

### Hidden Fields

```html
<input type="hidden" name="_subject" value="New contact from mkweli.tech">
```

This sets the email subject line for submissions.

### Formspree Free Tier Limits
- 50 submissions/month
- Email notifications
- Basic spam filtering

## 🔧 Local Development

### Preview Locally

Since the page is static HTML, you can preview it by:

1. **Simple method**: Open `docs/index.html` directly in a browser

2. **With live reload** (using Python):
   ```bash
   cd docs
   python -m http.server 8000
   # Open http://localhost:8000
   ```

3. **With live reload** (using Node.js):
   ```bash
   npx serve docs
   ```

### Testing Responsive Design

Use browser DevTools (F12) → Toggle device toolbar (Ctrl+Shift+M)

Breakpoints:
- Mobile: < 640px
- Tablet: 640px - 968px
- Desktop: > 968px

## 🛠️ Troubleshooting

### Page Not Updating

1. Check GitHub Actions for deployment status
2. Clear browser cache (Ctrl+Shift+R)
3. Wait a few minutes for CDN cache to clear

### Custom Domain Not Working

1. Verify DNS records are correct
2. Check CNAME file has no trailing spaces
3. Wait for DNS propagation (up to 48 hours)
4. Verify in Settings → Pages

### Form Not Submitting

1. Check Formspree endpoint is correct
2. Verify form has all required fields
3. Check browser console for errors
4. Test with Formspree's test mode

## 📊 Analytics (Optional)

To add Google Analytics:

1. Get your tracking ID from Google Analytics
2. Add before `</head>` in `index.html`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-XXXXXXXXXX');
</script>
```

## 📝 License

This landing page is part of the Mkweli project, licensed under Apache 2.0.

## 📞 Support

- **Email:** gilbert@mkweli.tech
- **GitHub Issues:** [Report problems](https://github.com/gilbertbouic/Mkweli/issues)
