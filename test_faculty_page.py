#!/usr/bin/env python3
"""
Comprehensive Faculty Page Test Suite
Tests all faculty page functionality including:
- Authentication and access control
- Faculty info retrieval and updates
- Profile form functionality
- Password change functionality
"""

import requests
import json
import time
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:5000"

class FacultyPageTester:
    def __init__(self):
        self.session = requests.Session()
        self.faculty_email = "testfaculty@neurobloom.com"
        self.faculty_password = "Test@123456"
        self.tests_passed = 0
        self.tests_failed = 0
        
    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def test_result(self, test_name, passed, details=""):
        if passed:
            print(f"✓ [PASSED] {test_name}")
            self.tests_passed += 1
        else:
            print(f"✗ [FAILED] {test_name}")
            if details:
                print(f"  Details: {details}")
            self.tests_failed += 1
    
    def test_1_faculty_login(self):
        """Test 1: Faculty login"""
        print("\n[TEST 1] Faculty Login")
        try:
            response = self.session.post(f"{BASE_URL}/login/faculty", 
                data={
                    'faculty_email': self.faculty_email,
                    'faculty_password': self.faculty_password
                },
                allow_redirects=False)
            
            passed = response.status_code == 302 and '/faculty' in response.headers.get('Location', '')
            self.test_result("Faculty login successful", passed, f"Status: {response.status_code}, Location: {response.headers.get('Location', '')}")
            return passed
        except Exception as e:
            self.test_result("Faculty login successful", False, str(e))
            return False
    
    def test_2_unauthenticated_api_access(self):
        """Test 2: Unauthenticated API access returns 401 with JSON"""
        print("\n[TEST 2] Unauthenticated API Access")
        try:
            new_session = requests.Session()
            response = new_session.get(f"{BASE_URL}/api/faculty-info")
            
            passed = response.status_code == 401
            try:
                data = response.json()
                has_json = True
            except:
                has_json = False
            
            self.test_result("API returns 401 JSON for unauthenticated", 
                           passed and has_json,
                           f"Status: {response.status_code}, Is JSON: {has_json}")
            return passed and has_json
        except Exception as e:
            self.test_result("API returns 401 JSON for unauthenticated", False, str(e))
            return False
    
    def test_3_faculty_page_access(self):
        """Test 3: Access faculty page after login"""
        print("\n[TEST 3] Faculty Page Access")
        try:
            response = self.session.get(f"{BASE_URL}/faculty")
            passed = response.status_code == 200 and 'faculty-dashboard' in response.text or 'faculty-container' in response.text
            self.test_result("Faculty page loads successfully", passed, f"Status: {response.status_code}")
            return passed
        except Exception as e:
            self.test_result("Faculty page loads successfully", False, str(e))
            return False
    
    def test_4_get_faculty_info_api(self):
        """Test 4: Get faculty info via API"""
        print("\n[TEST 4] Get Faculty Info API")
        try:
            response = self.session.get(f"{BASE_URL}/api/faculty-info")
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                has_profile = 'profile' in data
                has_stats = 'statistics' in data
                
                if has_profile:
                    profile = data['profile']
                    has_required_fields = all(k in profile for k in ['name', 'email', 'contact', 'class'])
                else:
                    has_required_fields = False
                
                passed = has_profile and has_stats and has_required_fields
                self.test_result("API returns proper structure", passed, 
                               f"Has profile: {has_profile}, Has stats: {has_stats}, Has fields: {has_required_fields}")
                
                if has_profile:
                    print(f"  Faculty Name: {profile.get('name')}")
                    print(f"  Faculty Email: {profile.get('email')}")
                    print(f"  Faculty Class: {profile.get('class')}")
            else:
                self.test_result("API returns proper structure", False, f"Status: {response.status_code}")
            
            return passed
        except Exception as e:
            self.test_result("API returns proper structure", False, str(e))
            return False
    
    def test_5_update_faculty_profile(self):
        """Test 5: Update faculty profile via API"""
        print("\n[TEST 5] Update Faculty Profile")
        try:
            # First get current data
            response = self.session.get(f"{BASE_URL}/api/faculty-info")
            current_data = response.json()['profile']
            
            # Update with new data
            update_data = {
                'name': current_data['name'],  # Keep same
                'email': current_data['email'],  # Keep same
                'contact': '9876543210',  # Update contact
                'class': current_data.get('class', 'Test Class')
            }
            
            response = self.session.put(f"{BASE_URL}/api/faculty-info",
                                       json=update_data)
            
            passed = response.status_code == 200
            self.test_result("Profile update successful", passed, f"Status: {response.status_code}")
            
            # Verify update
            if passed:
                response = self.session.get(f"{BASE_URL}/api/faculty-info")
                new_data = response.json()['profile']
                contact_updated = new_data.get('contact') == '9876543210'
                self.test_result("Contact updated correctly", contact_updated, 
                               f"New contact: {new_data.get('contact')}")
                return contact_updated
            return False
        except Exception as e:
            self.test_result("Profile update successful", False, str(e))
            return False
    
    def test_6_change_password(self):
        """Test 6: Change password via API"""
        print("\n[TEST 6] Change Password API")
        try:
            response = self.session.post(f"{BASE_URL}/api/update-password",
                                        json={
                                            'current_password': self.faculty_password,
                                            'new_password': 'TempPassword@123'
                                        })
            
            passed = response.status_code == 200
            self.test_result("Password change successful", passed, f"Status: {response.status_code}")
            
            if passed:
                # Change it back
                response = self.session.post(f"{BASE_URL}/api/update-password",
                                            json={
                                                'current_password': 'TempPassword@123',
                                                'new_password': self.faculty_password
                                            })
                reset_passed = response.status_code == 200
                self.test_result("Password reset to original", reset_passed)
                return reset_passed
            return False
        except Exception as e:
            self.test_result("Password change successful", False, str(e))
            return False
    
    def test_7_css_loaded(self):
        """Test 7: Faculty CSS is properly linked"""
        print("\n[TEST 7] Faculty CSS Loaded")
        try:
            response = self.session.get(f"{BASE_URL}/faculty")
            passed = 'faculty.css' in response.text
            self.test_result("Faculty CSS linked in page", passed)
            return passed
        except Exception as e:
            self.test_result("Faculty CSS linked in page", False, str(e))
            return False
    
    def test_8_javascript_functions(self):
        """Test 8: Required JavaScript functions present"""
        print("\n[TEST 8] JavaScript Functions")
        try:
            response = self.session.get(f"{BASE_URL}/faculty")
            html = response.text
            
            functions = [
                'loadFacultyProfile',
                'setupSectionNavigation',
                'setupProfileEditing',
                'setupPasswordChange'
            ]
            
            all_present = all(f in html for f in functions)
            self.test_result("All JS functions present", all_present,
                           f"Functions: {functions}")
            return all_present
        except Exception as e:
            self.test_result("All JS functions present", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        self.print_header("FACULTY PAGE COMPREHENSIVE TEST SUITE")
        
        print("Login Status: Attempting faculty login...")
        if not self.test_1_faculty_login():
            print("\n✗ Login failed. Cannot continue with authenticated tests.")
            return
        
        print("\nRunning authenticated tests...\n")
        self.test_2_unauthenticated_api_access()
        self.test_3_faculty_page_access()
        self.test_4_get_faculty_info_api()
        self.test_5_update_faculty_profile()
        self.test_6_change_password()
        self.test_7_css_loaded()
        self.test_8_javascript_functions()
        
        self.print_header("TEST SUMMARY")
        total = self.tests_passed + self.tests_failed
        print(f"Total Tests: {total}")
        print(f"Passed: {self.tests_passed} ✓")
        print(f"Failed: {self.tests_failed} ✗")
        
        if self.tests_failed == 0:
            print("\n✓ ALL TESTS PASSED!")
        else:
            print(f"\n✗ {self.tests_failed} test(s) failed")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    print("Waiting 2 seconds for server to be ready...")
    time.sleep(2)
    
    tester = FacultyPageTester()
    tester.run_all_tests()
