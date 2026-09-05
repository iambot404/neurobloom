# Neurobloom API Documentation

## Overview

This document provides detailed API endpoint specifications for the Neurobloom educational assessment system.

---

## 🔐 Authentication

All endpoints are protected with role-based authentication using Flask session management.

### Authentication Headers
```
Cookie: session=<session_id>
```

### Authentication Methods
1. **Login Route**: `/login` (POST) - Establishes session
2. **Session Verification**: Automatic on each request
3. **Role Validation**: Checked via decorator `@login_required('role')`

### Roles
- `student`: Can access student endpoints only
- `faculty`: Can access faculty endpoints and see class students only
- `admin`: Can access all endpoints (future)

---

## 📊 Student API Endpoints

### 1. Get Student Dashboard Data

**Endpoint**: `/api/student/dashboard`  
**Method**: `GET`  
**Authentication**: Required (student role)

**Response** (200 OK):
```json
{
  "status": "ok",
  "stats": {
    "total_assessments": 5,
    "average_score": 78.5,
    "overall_risk": "Low Risk"
  },
  "recent_assessments": [
    {
      "id": 1,
      "disorder_type": "dyslexia",
      "score": 85,
      "risk_level": "Low Risk",
      "date": "2024-01-15T10:30:00",
      "recommendations_count": 3
    }
  ],
  "assessment_history": [
    {
      "id": 1,
      "disorder_type": "dyslexia",
      "score": 85,
      "risk_level": "Low Risk",
      "date": "2024-01-15T10:30:00",
      "status": "completed"
    }
  ],
  "progress_by_disorder": [
    {
      "disorder": "dyslexia",
      "attempts": 3,
      "average_score": 80,
      "trend": "improving",
      "scores": [75, 78, 85]
    }
  ],
  "recommendations": [
    {
      "disorder": "dyslexia",
      "risk_level": "Low Risk",
      "category": "assessment",
      "text": "Continue with specialized reading interventions",
      "count": 2
    }
  ]
}
```

**Error Response** (500 Server Error):
```json
{
  "error": "Error message details"
}
```

---

### 2. Get Assessment Details

**Endpoint**: `/api/student/assessment/<assessment_id>`  
**Method**: `GET`  
**Authentication**: Required (student role)

**Path Parameters**:
- `assessment_id` (integer): ID of the assessment

**Response** (200 OK):
```json
{
  "assessment": {
    "id": 1,
    "disorder_type": "dyslexia",
    "score": 85,
    "risk_level": "Low Risk",
    "confidence": 92.5,
    "date": "2024-01-15T10:30:00",
    "status": "completed",
    "question_count": 30,
    "correct_answers": 25,
    "time_spent_seconds": 1200,
    "breakdown": {
      "reading": 85,
      "spelling": 78,
      "comprehension": 92
    },
    "recommendations": [
      "Continue with specialized reading interventions",
      "Practice weekly spelling exercises",
      "Use text-to-speech tools for long texts"
    ]
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Assessment not found"
}
```

---

## 👨‍🏫 Faculty API Endpoints

### 1. Get Faculty Dashboard Data

**Endpoint**: `/api/faculty/dashboard`  
**Method**: `GET`  
**Authentication**: Required (faculty role)

**Response** (200 OK):
```json
{
  "status": "ok",
  "stats": {
    "total_students": 25,
    "total_assessments": 75
  },
  "students": [
    {
      "id": 5,
      "name": "John Doe",
      "email": "john@example.com",
      "profile_photo": "/static/uploads/profile_5.jpg",
      "assessment_count": 3,
      "avg_score": 78.5,
      "overall_risk": "Low Risk",
      "disorder_risks": [
        {
          "disorder_type": "dyslexia",
          "risk_level": "Low Risk",
          "score": 78,
          "attempts": 2,
          "last_date": "2024-01-15"
        }
      ]
    }
  ],
  "analytics": {
    "performance": {
      "labels": ["Dyslexia", "Dyscalculia", "Dysgraphia"],
      "scores": [65, 72, 58]
    },
    "risk_distribution": {
      "no_risk": 5,
      "low_risk": 12,
      "medium_risk": 6,
      "high_risk": 2
    },
    "disorder_breakdown": {
      "dyslexia": 15,
      "dyscalculia": 10,
      "dysgraphia": 8
    }
  }
}
```

---

### 2. Get Filtered Students

**Endpoint**: `/api/faculty/students`  
**Method**: `GET`  
**Authentication**: Required (faculty role)

**Query Parameters**:
- `search` (optional, string): Search by student name or email
- `disorder` (optional, string): Filter by disorder type (dyslexia/dyscalculia/dysgraphia)
- `risk` (optional, string): Filter by risk level (No Risk/Low Risk/Medium Risk/High Risk)

**Example Request**:
```
GET /api/faculty/students?search=john&disorder=dyslexia&risk=Low%20Risk
```

**Response** (200 OK):
```json
{
  "students": [
    {
      "id": 5,
      "name": "John Doe",
      "email": "john@example.com",
      "profile_photo": "/static/uploads/profile_5.jpg",
      "assessment_count": 3,
      "avg_score": 78.5,
      "overall_risk": "Low Risk",
      "disorder_risks": [
        {
          "disorder_type": "dyslexia",
          "risk_level": "Low Risk"
        }
      ]
    }
  ]
}
```

---

### 3. Get Student Details

**Endpoint**: `/api/faculty/student/<student_id>`  
**Method**: `GET`  
**Authentication**: Required (faculty role)

**Path Parameters**:
- `student_id` (integer): ID of the student

**Response** (200 OK):
```json
{
  "student": {
    "id": 5,
    "name": "John Doe",
    "email": "john@example.com",
    "class": "10A",
    "assessment_count": 3,
    "avg_score": 78.5,
    "disorder_risks": [
      {
        "disorder_type": "dyslexia",
        "risk_level": "Low Risk",
        "score": 78.5,
        "attempts": 2,
        "last_date": "2024-01-15"
      }
    ]
  }
}
```

**Error Response** (403 Forbidden):
```json
{
  "error": "Unauthorized"
}
```

---

### 4. Get Student Assessments

**Endpoint**: `/api/faculty/student/<student_id>/assessments`  
**Method**: `GET`  
**Authentication**: Required (faculty role)

**Path Parameters**:
- `student_id` (integer): ID of the student

**Response** (200 OK):
```json
{
  "assessments": [
    {
      "id": 1,
      "disorder_type": "dyslexia",
      "score": 85,
      "risk_level": "Low Risk",
      "date": "2024-01-15T10:30:00"
    },
    {
      "id": 2,
      "disorder_type": "dyscalculia",
      "score": 72,
      "risk_level": "Medium Risk",
      "date": "2024-01-10T14:20:00"
    }
  ]
}
```

---

### 5. Get Assessment Details

**Endpoint**: `/api/faculty/assessment/<assessment_id>`  
**Method**: `GET`  
**Authentication**: Required (faculty role)

**Path Parameters**:
- `assessment_id` (integer): ID of the assessment

**Response** (200 OK):
```json
{
  "assessment": {
    "id": 1,
    "disorder_type": "dyslexia",
    "score": 85,
    "risk_level": "Low Risk",
    "date": "2024-01-15T10:30:00",
    "recommendations": [
      "Continue with specialized reading interventions",
      "Practice weekly spelling exercises",
      "Use text-to-speech tools for long texts"
    ]
  }
}
```

**Error Response** (403 Forbidden):
```json
{
  "error": "Unauthorized"
}
```

---

### 6. Export Class Data to CSV

**Endpoint**: `/api/faculty/export-csv`  
**Method**: `GET`  
**Authentication**: Required (faculty role)

**Response** (200 OK - CSV file):
```
Name,Email,Assessments,Average Score
John Doe,john@example.com,3,78.5%
Jane Smith,jane@example.com,2,82.0%
...
```

**Headers**:
```
Content-Type: text/csv
Content-Disposition: attachment; filename=class_report_10A.csv
```

---

## 📝 HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Successfully fetched data |
| 400 | Bad Request | Invalid query parameters |
| 403 | Forbidden | User not authorized for this resource |
| 404 | Not Found | Assessment or student not found |
| 500 | Server Error | Database error or unhandled exception |

---

## 🔄 Data Flow Examples

### Example 1: Student Checking Progress

```
1. GET /api/student/dashboard
   ↓
2. Returns:
   - Total assessments: 5
   - Average score: 78.5%
   - Overall risk: Low Risk
   - Recent assessments with details
   - Progress by disorder
   - Recommendations

3. Frontend renders:
   - Stats cards with numbers
   - Chart of performance trends
   - Recommendation list
```

### Example 2: Faculty Monitoring Class

```
1. GET /api/faculty/dashboard
   ↓
2. Returns:
   - Student roster with stats
   - Class analytics and charts
   - Risk distribution data

3. GET /api/faculty/students?risk=High%20Risk
   ↓
4. Returns:
   - Only students with high risk

5. GET /api/faculty/student/5
   ↓
6. Returns:
   - Student details and progress

7. GET /api/faculty/student/5/assessments
   ↓
8. Returns:
   - All assessments for this student

9. GET /api/faculty/assessment/1
   ↓
10. Returns:
    - Detailed recommendations
```

---

## 💾 Response Data Types

### Assessment Object
```
{
  "id": number,
  "disorder_type": string (dyslexia|dyscalculia|dysgraphia),
  "score": number (0-100),
  "risk_level": string (No Risk|Low Risk|Medium Risk|High Risk),
  "date": ISO8601 datetime,
  "status": string (completed|pending)
}
```

### Student Object
```
{
  "id": number,
  "name": string,
  "email": string,
  "class": string,
  "profile_photo": string (URL),
  "assessment_count": number,
  "avg_score": number,
  "overall_risk": string,
  "disorder_risks": [DisorederRisk]
}
```

### DisorderRisk Object
```
{
  "disorder_type": string,
  "risk_level": string,
  "score": number,
  "attempts": number,
  "last_date": date string
}
```

---

## 🔍 Filtering Examples

### Filter by Multiple Criteria
```
GET /api/faculty/students?search=john&disorder=dyslexia&risk=High%20Risk
```

Returns only students named John with dyslexia and high risk.

### Filter by Disorder Only
```
GET /api/faculty/students?disorder=dyscalculia
```

Returns all students with dyscalculia.

### Search by Name
```
GET /api/faculty/students?search=smith
```

Returns all students with "smith" in name or email.

---

## ⚠️ Error Handling

All error responses follow this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

### Common Errors

**403 Forbidden**
- User not logged in
- User trying to access data outside their role
- Faculty trying to view student from different class

**404 Not Found**
- Assessment doesn't exist
- Student doesn't exist
- Student doesn't belong to faculty's class

**500 Server Error**
- Database connection failed
- Unhandled exception in code

---

## 🔐 Security Considerations

1. **Authentication**: All endpoints require valid session
2. **Authorization**: Faculty can only see students in their class
3. **Data Isolation**: Students only see their own data
4. **SQL Injection Protection**: Using parameterized queries
5. **Session Management**: Automatic timeout after inactivity

---

## 📊 Performance Notes

- Endpoints include database query optimization
- Results are paginated for large datasets (future enhancement)
- Charts data is aggregated on backend for performance
- CSV exports generate on-the-fly

---

## 🚀 Rate Limiting

Currently no rate limiting implemented. For production deployment, consider adding:
- IP-based rate limiting
- Per-user rate limiting
- Request throttling

---

## 📚 Related Documentation

- [Educational Infrastructure Guide](./EDUCATIONAL_INFRASTRUCTURE_GUIDE.md)
- [Quick Setup & Testing](./QUICK_SETUP_AND_TESTING.md)
- [Assessment Integration](./ASSESSMENT_INTEGRATION.md)

---

## 🆘 Troubleshooting

### API returns 403 Forbidden
- Verify user is logged in
- Check user role matches endpoint
- For faculty, verify student is in same class

### API returns 404 Not Found
- Verify resource ID exists in database
- Check spelling in URL

### API returns 500 Server Error
- Check server logs
- Verify database is running
- Check for database connection errors

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-20 | Initial API release |

---

This API is designed for educational institutions to manage student learning disorder assessments and track progress effectively.
