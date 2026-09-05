# Student Profile Implementation Guide

## Overview
A comprehensive student profile system has been implemented with dedicated API endpoints and a full-featured profile page for managing personal, academic, and security information.

## API Endpoints

### 1. Get Student Profile (Complete)
**Endpoint:** `GET /api/student/profile`

**Authentication:** Required (student login)

**Response:**
```json
{
  "status": "ok",
  "profile": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "contact": "9876543210",
    "role": "student",
    "class": "B.Tech 3rd Year",
    "faculty_id": 5,
    "faculty_name": "Dr. Smith",
    "profile_photo": "/static/uploads/photo.jpg",
    "created_at": "2024-12-01T10:30:00"
  },
  "statistics": {
    "total_assessments": 15,
    "average_score": 72.5,
    "disorders_attempted": 3,
    "last_assessment_date": "2024-12-03"
  },
  "disorder_breakdown": [
    {
      "disorder": "dyslexia",
      "attempts": 5,
      "average_score": 68.5,
      "best_score": 82.0,
      "lowest_score": 55.0
    },
    {
      "disorder": "dyscalculia",
      "attempts": 5,
      "average_score": 75.0,
      "best_score": 88.0,
      "lowest_score": 62.0
    },
    {
      "disorder": "dysgraphia",
      "attempts": 5,
      "average_score": 74.0,
      "best_score": 85.0,
      "lowest_score": 60.0
    }
  ]
}
```

### 2. Update Student Profile
**Endpoint:** `PUT /api/student/profile`

**Authentication:** Required (student login)

**Request Body:**
```json
{
  "name": "Updated Name",
  "email": "newemail@example.com",
  "contact": "9876543210",
  "class": "B.Tech 3rd Year",
  "faculty_id": 5
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Profile updated successfully",
  "profile": {
    "id": 1,
    "name": "Updated Name",
    "email": "newemail@example.com",
    "contact": "9876543210",
    "role": "student",
    "class": "B.Tech 3rd Year",
    "faculty_id": 5,
    "faculty_name": "Dr. Smith"
  }
}
```

### 3. Upload Profile Photo
**Endpoint:** `POST /upload-profile-photo`

**Authentication:** Required (student login)

**Request:** Multipart form data with `photo` file
- Max size: 5MB
- Accepted formats: JPG, PNG, GIF, etc.

**Response:**
```json
{
  "status": "ok",
  "message": "Photo uploaded successfully",
  "photo_url": "/static/uploads/photo_hash.jpg"
}
```

### 4. Update Password
**Endpoint:** `POST /api/update-password`

**Authentication:** Required (student login)

**Request Body:**
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword123"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Password changed successfully"
}
```

### 5. Get Faculties
**Endpoint:** `GET /api/faculties`

**Authentication:** Required (student login)

**Response:**
```json
{
  "faculties": [
    {
      "id": 5,
      "name": "Dr. Smith"
    },
    {
      "id": 6,
      "name": "Prof. Johnson"
    }
  ]
}
```

## Profile Page

### Route
**URL:** `/student-profile`

**Access:** Students only (login required)

### Features

#### 1. Sidebar
- Profile photo display and upload capability
- Quick statistics (Total Assessments, Average Score, Disorders Attempted)
- Disorder breakdown with attempts and average scores

#### 2. Tabs

##### Personal Information Tab
- Full Name
- Email Address
- Contact Number
- Save/Cancel buttons

##### Academic Information Tab
- Class/Semester
- Faculty/Mentor selection
- Save/Cancel buttons

##### Security Tab
- Current Password
- New Password
- Confirm Password
- Password validation (min 8 characters)

#### 3. User Experience
- Real-time form validation
- Success/error message notifications
- Auto-loading of faculties from backend
- Responsive design for mobile devices
- Smooth tab switching with animations

## How to Use

### For Students
1. **Navigate to Profile:** Click on profile link or go to `/student-profile`
2. **View Information:** See all personal, academic, and statistical information
3. **Edit Information:**
   - Click the appropriate tab (Personal, Academic, or Security)
   - Update the fields
   - Click "Save Changes"
4. **Upload Photo:** Click "📷 Change Photo" button to upload a profile picture
5. **Change Password:** Go to Security tab and follow the same process

### For Frontend Integration
Add a profile link in the navigation:
```html
<a href="/student-profile" class="nav-link">My Profile</a>
```

Or use the API directly:
```javascript
// Get profile
fetch('/api/student/profile')
  .then(r => r.json())
  .then(data => console.log(data.profile));

// Update profile
fetch('/api/student/profile', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'New Name' })
})
  .then(r => r.json())
  .then(data => console.log('Updated!'));
```

## Error Handling

### Common Errors
- **401 Unauthorized:** Student is not logged in
- **404 Not Found:** Student profile does not exist
- **409 Conflict:** Email is already in use
- **400 Bad Request:** Required fields are missing or invalid
- **500 Server Error:** Internal server error

All endpoints return appropriate HTTP status codes and error messages.

## Security Features
- Login required for all endpoints
- Email uniqueness validation
- Password minimum length requirement (8 characters)
- File size validation for photo uploads (max 5MB)
- Secure session management
- CSRF protection (if enabled)

## Database Integration
The profile system uses the existing `users` table with the following relevant columns:
- `id` - User ID
- `name` - Full name
- `email` - Email address
- `contact` - Contact number
- `role` - User role (student/faculty)
- `class` - Class/Semester
- `faculty_id` - Associated faculty member
- `profile_photo` - Profile photo path

## Files Created/Modified
1. **API Endpoints** (app.py):
   - `GET /api/student/profile`
   - `PUT /api/student/profile`
   - `POST /upload-profile-photo`
   - `POST /api/update-password`

2. **Frontend Files**:
   - `templates/student-profile.html` - Profile page template
   - `static/student-profile.css` - Profile page styling
   - `static/student-profile.js` - Profile page functionality

3. **Routes** (app.py):
   - `GET /student-profile` - Render profile page

## Next Steps
1. Add profile link to navigation menu
2. Add profile option to user dropdown menu
3. Integrate with existing dashboard
4. Consider adding additional profile sections (achievements, certificates, etc.)
