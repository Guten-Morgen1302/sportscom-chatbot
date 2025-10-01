# Fix Vercel Deployment - 500 Error

## Problem
Getting 500 errors and "Something went wrong! Ask this on sports update group" message when chatting with bot on Vercel.

## Root Cause
GEMINI_API_KEY environment variable is not set in Vercel.

## Solution (3 Simple Steps)

### 1. Go to Vercel Dashboard
- Open your Vercel project
- Click on "Settings" tab

### 2. Add Environment Variable
- Go to "Environment Variables" section
- Click "Add New"
- Add:
  - **Key**: `GEMINI_API_KEY`
  - **Value**: `AIzaSyCNe1gaa7EwQoVum6zJf35n2UNKjwiyuIs` (your API key)
- Select all environments (Production, Preview, Development)
- Click "Save"

### 3. Redeploy
- Go to "Deployments" tab
- Click the 3 dots (...) on the latest deployment
- Click "Redeploy"
- Wait for deployment to complete

## Verification
After redeployment:
1. Visit your Vercel URL
2. Try chatting with the bot
3. Should work without 500 errors

## Additional Optional Variables
You can also add (but these have defaults):
- `GEMINI_MODEL`: gemini-2.5-flash
- `API_TEMPERATURE`: 0.3
- `API_MAX_TOKENS`: 500

---

**That's it!** Your bot should work perfectly on Vercel now.
