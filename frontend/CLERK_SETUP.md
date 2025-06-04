# Clerk Authentication Setup Guide

## Overview
This project uses Clerk for authentication. Follow these steps to set up Clerk for your development environment.

## 1. Create a Clerk Account
1. Go to [https://clerk.com/](https://clerk.com/)
2. Sign up for a free account
3. Create a new application

## 2. Get Your API Keys
1. In your Clerk dashboard, go to "API Keys"
2. Copy the following values:
   - **Publishable Key** (starts with `pk_test_`)
   - **Secret Key** (starts with `sk_test_`)

## 3. Set Environment Variables
Create a `.env` file in the `frontend` directory with:

```env
# Clerk Configuration
PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your-publishable-key-here
CLERK_SECRET_KEY=sk_test_your-secret-key-here

# API Configuration  
PUBLIC_API_URL=http://localhost:3000
```

## 4. Configure Clerk Application
In your Clerk dashboard:

1. **Set Redirect URLs:**
   - After sign-in URL: `http://localhost:5173/dashboard`
   - After sign-up URL: `http://localhost:5173/dashboard`

2. **Configure Sign-in/Sign-up URLs:**
   - Sign-in URL: `http://localhost:5173/sign-in`
   - Sign-up URL: `http://localhost:5173/sign-up`

## 5. Test the Integration
1. Start the development server: `npm run dev`
2. Navigate to `http://localhost:5173`
3. Try signing up for a new account
4. Verify you're redirected to the dashboard after authentication

## Protected Routes
The following routes are automatically protected by Clerk:
- `/dashboard`
- `/leads`
- `/analytics`

Users will be redirected to `/sign-in` if they try to access these routes without authentication.

## Troubleshooting
- Make sure your environment variables are properly set
- Check that your Clerk application is configured with the correct URLs
- Verify that the `clerk-sveltekit` package is installed
- Check the browser console for any authentication errors 