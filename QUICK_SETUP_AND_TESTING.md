# Quick Setup & Testing Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Ensure Database is Running
```bash
# Start MySQL (XAMPP, Docker, or native MySQL)
# Database should be: neurobloom
# User: root
# Password: (empty or your password)
```

### Step 2: Run Flask Application
```bash
cd "d:\BTech Project\Project"
python app.py
```

The application will start at `http://localhost:5000`

### Step 3: Access the System
- **Student Dashboard**: `http://localhost:5000/student-dashboard`
- **Faculty Dashboard**: `http://localhost:5000/faculty-dashboard`

---

## 🧪 Testing the System

### Test Scenario 1: Student Dashboard Flow

#### Prerequisites
- Student must be logged in
- Student must have completed at least one assessment

#### Steps
1. Login with student credentials
2. Navigate to Student Dashboard (`/student-dashboard`)
3. **Verify**:
   - [ ] Welcome message displays with student name
   - [ ] Quick stats cards show data
   - [ ] Can see total assessments count
   - [ ] Can see average score
   - [ ] Can see overall risk level

#### Test Tabs
1. **Overview Tab**
   - [ ] Performance chart displays
   - [ ] Recent assessments listed
   - [ ] Last assessment date shown

2. **History Tab**
   - [ ] All past assessments visible
   - [ ] Can filter by disorder
   - [ ] Can search assessments
   - [ ] Click on assessment opens detail modal

3. **Progress Tab**
   - [ ] Progress cards for each disorder
   - [ ] Mini-charts show trends
   - [ ] Risk levels color-coded correctly

4. **Recommendations Tab**
   - [ ] Recommendations displayed
   - [ ] Can filter by category
   - [ ] Color-coded by risk level

---

### Test Scenario 2: Faculty Dashboard Flow

#### Prerequisites
- Faculty must be logged in
- Faculty must have students assigned
- Students must have assessments

#### Steps
1. Login with faculty credentials
2. Navigate to Faculty Dashboard (`/faculty-dashboard`)
3. **Verify**:
   - [ ] Faculty dashboard loads
   - [ ] Total students shown in header
   - [ ] Total assessments shown in header
   - [ ] Student cards display

#### Test Student Cards
- [ ] Student name and email visible
- [ ] Profile photo displays
- [ ] Assessment count shown
- [ ] Average score shown
- [ ] Overall risk level displayed
- [ ] Disorder badges visible

#### Test Search & Filter
1. **Search** by student name
   - [ ] Results filter correctly
   - [ ] No matches show empty state

2. **Filter** by disorder
   - [ ] Only students with that disorder shown
   - [ ] "All Disorders" shows everyone

3. **Filter** by risk level
   - [ ] Only students with that risk shown
   - [ ] "All Risk Levels" shows everyone

#### Test Tabs

1. **Students Tab**
   - [ ] All students display
   - [ ] Filters work correctly
   - [ ] Search works

2. **Analytics Tab**
   - [ ] Class Performance chart renders
   - [ ] Risk Distribution chart renders
   - [ ] Disorder Breakdown radar chart renders

3. **Reports Tab**
   - [ ] "Generate Class Report" button works
   - [ ] "Export Data (CSV)" downloads file

#### Test Student Details
1. Click "View Details" on any student
2. **Verify Modal Shows**:
   - [ ] Student name
   - [ ] Email
   - [ ] Class
   - [ ] Total assessments
   - [ ] Average score
   - [ ] Disorder progress sections
   - [ ] Progress bars display correctly

---

### Test Scenario 3: API Endpoints

#### Student APIs
```bash
# Get student dashboard data
curl http://localhost:5000/api/student/dashboard

# Get specific assessment
curl http://localhost:5000/api/student/assessment/1
```

**Expected Response**: JSON with stats, assessments, progress, recommendations

#### Faculty APIs
```bash
# Get faculty dashboard
curl http://localhost:5000/api/faculty/dashboard

# Get filtered students
curl "http://localhost:5000/api/faculty/students?search=john&disorder=dyslexia&risk=High%20Risk"

# Get student details
curl http://localhost:5000/api/faculty/student/5

# Get student assessments
curl http://localhost:5000/api/faculty/student/5/assessments

# Get assessment details
curl http://localhost:5000/api/faculty/assessment/1

# Export CSV
curl http://localhost:5000/api/faculty/export-csv > class_data.csv
```

---

### Test Scenario 4: Security & Access Control

#### Test 1: Student Can't See Other Students
1. Login as student A
2. Try to access `/api/student/dashboard` - should work
3. Try to access another student's assessment - should fail
4. **Expected**: 403 Forbidden or filtered data

#### Test 2: Faculty Can Only See Own Class
1. Login as faculty
2. Faculty dashboard shows only their class
3. Assign student to different class
4. **Expected**: Student not visible to faculty

#### Test 3: Logout Works
1. Login as any user
2. Click logout
3. Try to access dashboard directly
4. **Expected**: Redirected to login page

---

## 📝 Sample Data for Testing

### Student Test Account
```
Email: student@example.com
Password: StudentPass123
Role: student
Class: 10A
```

### Faculty Test Account
```
Email: faculty@example.com
Password: FacultyPass123
Role: faculty
Class: 10A
```

### Sample Assessment Data
To create sample data, run assessments for test students:
1. Login as student
2. Go to `/assessments`
3. Select an assessment type
4. Complete the assessment
5. Data will be saved to database

---

## 🐛 Common Issues & Solutions

### Issue: Dashboard shows "No students found"
**Solution**: 
- Ensure faculty and students are assigned to same class
- Check database has student records
- Verify student has completed at least one assessment

### Issue: Charts not rendering
**Solution**:
- Check browser console for errors
- Verify Chart.js library loaded (check network tab)
- Ensure API is returning data
- Clear browser cache and reload

### Issue: API returns 403 Forbidden
**Solution**:
- Verify user is logged in
- Check user role matches endpoint (student vs faculty)
- For faculty, verify student is in same class
- Check session hasn't expired

### Issue: Assessment history empty
**Solution**:
- Ensure student has completed assessments
- Check database for student_assessments records
- Verify assessment status is "completed"

### Issue: Profile photo not showing
**Solution**:
- Check file was uploaded correctly
- Verify file path in database
- Check static/uploads directory exists
- Clear browser cache

---

## 📊 Database Verification

### Check if data exists
```sql
-- Check users
SELECT COUNT(*) FROM users WHERE role = 'student';
SELECT COUNT(*) FROM users WHERE role = 'faculty';

-- Check assessments
SELECT COUNT(*) FROM student_assessments;
SELECT * FROM student_assessments LIMIT 5;

-- Check predictions
SELECT COUNT(*) FROM ml_predictions;

-- Check by class
SELECT class, COUNT(*) FROM users GROUP BY class;
```

---

## 🔍 Debugging Tips

### Enable detailed logging
In `app.py`, ensure debug mode is on:
```python
if __name__ == '__main__':
    app.run(debug=True)  # Shows detailed errors
```

### Check API responses
Use browser Developer Tools:
1. Open Network tab (F12)
2. Make requests
3. Check Response tab to see JSON
4. Check Console for JavaScript errors

### Server logs
Watch terminal where Flask is running:
```
* Running on http://127.0.0.1:5000
* Debug mode: on
```

---

## ✅ Deployment Checklist

Before deploying to production:

- [ ] Database is set up and populated
- [ ] MySQL service is running
- [ ] All API endpoints tested and working
- [ ] Student dashboard displays correctly
- [ ] Faculty dashboard shows all features
- [ ] Search and filter work
- [ ] CSV export works
- [ ] Charts render properly
- [ ] Role-based access control verified
- [ ] Student data privacy confirmed
- [ ] Session management tested
- [ ] Error pages configured
- [ ] Logging configured
- [ ] Performance tested

---

## 📞 Support Resources

1. **Check Logs**: Look for error messages in server terminal
2. **Browser Console**: F12 → Console tab for JavaScript errors
3. **Network Tab**: F12 → Network tab to inspect API calls
4. **Database**: Verify data exists in MySQL
5. **Documentation**: Review EDUCATIONAL_INFRASTRUCTURE_GUIDE.md

---

## 🎯 Success Criteria

System is working correctly when:

✅ Students can login and view their dashboard  
✅ Students can see assessment history  
✅ Students can view progress trends  
✅ Students can read recommendations  
✅ Faculty can login and see student roster  
✅ Faculty can search and filter students  
✅ Faculty can view individual student progress  
✅ Faculty can export class data  
✅ All charts render correctly  
✅ All modals display detailed information  
✅ Role-based access control works  
✅ No console errors  

---

## 📋 Quick Reference

| Feature | URL | User Role |
|---------|-----|-----------|
| Student Dashboard | `/student-dashboard` | Student |
| Faculty Dashboard | `/faculty-dashboard` | Faculty |
| Take Assessment | `/assessments` | Student |
| Student API | `/api/student/dashboard` | Student |
| Faculty API | `/api/faculty/dashboard` | Faculty |
| Export CSV | `/api/faculty/export-csv` | Faculty |

---

## 🎓 Educational Use Case

### For Teachers
- Monitor class performance
- Identify at-risk students
- Track progress over time
- Export reports for documentation
- Make informed instructional decisions

### For Students
- Review past assessments
- Track personal progress
- Understand learning recommendations
- Prepare for interventions
- Advocate for accommodations

### For Administrators
- Monitor school-wide data (future)
- Generate reports for stakeholders
- Allocate resources effectively
- Support professional development

---

## 🏆 System Capabilities

✅ **Assessment Management**: Take and track multiple assessments  
✅ **Progress Tracking**: Visual trends and progress monitoring  
✅ **Risk Assessment**: AI-powered learning disability prediction  
✅ **Recommendations**: Evidence-based intervention suggestions  
✅ **Data Analytics**: Class and individual performance analytics  
✅ **Reporting**: CSV export for documentation  
✅ **Access Control**: Role-based permission management  
✅ **Privacy**: Data isolation by class and user  

---

This system is ready for educational deployment!
