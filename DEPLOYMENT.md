# KdG-Kiosk Website Deployment Guide

## Quick Start

### 1. Prerequisites

- Node.js and npm installed
- Firebase account (free tier is sufficient)

### 2. Install Firebase CLI

```bash
npm install -g firebase-tools
```

### 3. Login to Firebase

```bash
firebase login
```

This will open your browser for authentication.

### 4. Create a Firebase Project

1. Go to https://console.firebase.google.com/
2. Click "Add project"
3. Enter a project name (e.g., `kdg-kiosk`)
4. Follow the setup wizard

### 5. Configure the Project

Edit `.firebaserc` and replace `your-project-id` with your actual Firebase project ID:

```json
{
  "projects": {
    "default": "kdg-kiosk"
  }
}
```

### 6. Initialize Firebase (Optional)

If you want to reconfigure:

```bash
firebase init hosting
```

Select:
- Use an existing project → Select your project
- Public directory → `.` (current directory)
- Configure as single-page app → Yes
- Set up automatic builds → No

### 7. Deploy

```bash
firebase deploy
```

Or deploy only hosting:

```bash
firebase deploy --only hosting
```

### 8. Access Your Site

After deployment, Firebase will provide a URL like:
- `https://kdg-kiosk.web.app`
- `https://kdg-kiosk.firebaseapp.com`

## Testing Locally

Before deploying, test locally:

```bash
firebase serve
```

Then visit http://localhost:5000

## Continuous Deployment

### GitHub Actions

Add this to `.github/workflows/deploy-website.yml`:

```yaml
name: Deploy Website to Firebase

on:
  push:
    branches:
      - main
    paths:
      - 'website/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Copy installer
        run: cp install-kdg-kiosk.py website/
      
      - name: Deploy to Firebase
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
          channelId: live
          projectId: kdg-kiosk
          entryPoint: ./website
```

To set this up:
1. Generate a Firebase service account key from Firebase Console
2. Add it as `FIREBASE_SERVICE_ACCOUNT` secret in GitHub Settings

## Custom Domain

### Add Custom Domain

1. Go to Firebase Console > Hosting
2. Click "Add custom domain"
3. Enter your domain (e.g., `kiosk.kdg.be`)
4. Follow verification steps:
   - Add TXT record to DNS
   - Wait for verification
   - Add A records provided by Firebase

### Example DNS Records

```
Type    Name    Value
TXT     @       firebase-verify=abc123...
A       @       199.36.158.100
A       @       199.36.158.101
```

## Updating Content

### Update installer

```bash
# Copy latest installer
cp ../install-kdg-kiosk.py ./

# Deploy
firebase deploy --only hosting
```

### Update website content

1. Edit `index.html`, `style.css`, or `script.js`
2. Test locally: `firebase serve`
3. Deploy: `firebase deploy`

## Useful Commands

```bash
# View current project
firebase projects:list

# Switch project
firebase use <project-id>

# View hosting info
firebase hosting:sites:list

# Delete old hosting files
firebase hosting:sites:delete <site-name>

# View deployment history
firebase hosting:clone SOURCE_SITE_ID:SOURCE_CHANNEL DESTINATION_SITE_ID:live
```

## Troubleshooting

### "Permission denied" error

Re-authenticate:
```bash
firebase logout
firebase login
```

### "No project active" error

Initialize or set project:
```bash
firebase use --add
```

### 404 errors after deployment

Check `firebase.json` rewrites configuration:
```json
"rewrites": [
  {
    "source": "**",
    "destination": "/index.html"
  }
]
```

### Download links not working

Ensure files are in the website directory:
```bash
ls -la website/
```

Should include:
- `install-kdg-kiosk.py`
- `install.sh`

## Security

### Firebase Hosting Security

Firebase Hosting automatically provides:
- Free SSL certificates
- DDoS protection
- CDN distribution
- 99.95% uptime SLA

### Headers

Security headers are configured in `firebase.json`:
- Cache-Control for static assets
- Content-Type for downloads

## Performance

### Optimization Tips

1. **Images**: Compress images before uploading
2. **Caching**: Adjust cache headers in `firebase.json`
3. **CDN**: Automatically handled by Firebase

### Monitoring

View analytics in Firebase Console:
- Hosting → Usage tab
- View bandwidth, storage, requests

## Cost

Firebase Hosting free tier includes:
- 10 GB storage
- 360 MB/day transfer
- Custom domain support

This is more than sufficient for documentation sites.

## Support

- Firebase Documentation: https://firebase.google.com/docs/hosting
- Firebase Status: https://status.firebase.google.com/
- Community: https://stackoverflow.com/questions/tagged/firebase-hosting

