# KdG-Kiosk Website

This is the Firebase-hosted website for the KdG-Kiosk project.

## Setup

1. Install Firebase CLI:
   ```bash
   npm install -g firebase-tools
   ```

2. Login to Firebase:
   ```bash
   firebase login
   ```

3. Create a new Firebase project at https://console.firebase.google.com/

4. Update `.firebaserc` with your project ID:
   ```json
   {
     "projects": {
       "default": "your-project-id"
     }
   }
   ```

5. Copy the installer files to this directory:
   ```bash
   cp ../install-kdg-kiosk.py ./
   ```

## Deploy

Deploy to Firebase Hosting:

```bash
firebase deploy
```

Or deploy only hosting:

```bash
firebase deploy --only hosting
```

## Test Locally

Test the website locally before deploying:

```bash
firebase serve
```

Then visit http://localhost:5000

## Files

- `index.html` - Main website page
- `style.css` - Styles
- `script.js` - JavaScript functionality
- `firebase.json` - Firebase hosting configuration
- `.firebaserc` - Firebase project configuration
- `install.sh` - Quick install script
- `install-kdg-kiosk.py` - Python installer (copy from parent directory)

## Custom Domain

To use a custom domain:

1. Go to Firebase Console > Hosting
2. Click "Add custom domain"
3. Follow the instructions to verify and configure DNS

## Notes

- The website includes download links for the installer
- Make sure to copy `install-kdg-kiosk.py` to this directory before deploying
- The install.sh script downloads the Python installer from the hosted site

