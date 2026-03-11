# COPY THIS PROMPT TO AN AI TO INTEGRATE EDUPLUS BACKEND WITH REACT UI

---

## INSTRUCTION PROMPT FOR AI ASSISTANT

You are integrating a Python/Flask backend placement prediction system with a React frontend UI.

### SYSTEM REQUIREMENTS

**Backend System (Python):**
- Predicts: Placement probability, salary (point estimate + 9 cumulative probability thresholds), job role, company recommendations
- Stores results in: `data/Predicted_Data.csv`
- CSV columns:
  - student_id
  - overall_placement_probability
  - predicted_salary_lpa
  - salary_range_min_lpa, salary_range_mid_lpa, salary_range_max_lpa
  - prob_salary_gt_2_lpa through prob_salary_gt_40_lpa (9 columns for each threshold)
  - predicted_job_role
  - recommended_companies (comma-separated)

**Frontend System (React):**
- Collect student data sequentially
- Display results beautifully
- Integrate with backend APIs
- Mobile responsive
- Accessible (WCAG AA)

---

### USER FLOW (THIS IS CRITICAL)

1. **Page Load**: Show "Student ID Input"
   - User enters student ID (number 200000-200100)
   - Click "Check Student"

2. **Validation**: Call API `GET /api/student/{studentId}`
   - If exists:
     - Show "Update Existing Record?" dialog
     - If YES: Load existing data in wizard and continue
     - If NO: Cancel
   - If not exists: Continue to skills collection

3. **Skills Collection Wizard** (8 sequential steps with progress bar)
   - Step 1: LeetCode DSA Score
     - Option 1: Enter LeetCode username → API fetches score
     - Option 2: Enter score manually (0-100)
   - Step 2: GitHub Project Score
     - Option 1: Enter GitHub username → API fetches score
     - Option 2: Enter manually (0-100)
   - Step 3: Aptitude Score (0-100, manual)
   - Step 4: HR Round Score (0-100, manual)
   - Step 5: Resume ATS Score
     - Upload PDF/DOCX → API analyzes → Shows ATS score (0-100)
   - Step 6: CS Fundamentals Score (0-100, manual)
   - Step 7: Hackathon Wins (integer, 0+)
   - Step 8: CGPA (0.0-10.0)
   - Navigation: Previous/Next/Skip buttons
   - Show progress: "2 of 8" with visual progress bar

4. **Prediction Generation** (Show loading screen)
   - Display message: "Calculating your placement predictions..."
   - Show progress steps:
     - Loading ML models (20%)
     - Calculating placement probability (40%)
     - Predicting salary (60%)
     - Predicting job role (80%)
     - Recommending companies (100%)
   - API call: `POST /api/predictions/generate` with all scores
   - Backend calculates and returns predictions
   - Auto-save: `POST /api/predictions/save`

5. **Display Results** (Beautiful result cards)
   - Section 1: Placement Probability
     - Show: Circular progress 0-100%
     - Example: 86.25%
   
   - Section 2: Salary Predictions
     - Show: Predicted salary
     - Show: Salary range (min-max)
     - Example: 29.46 LPA, Range: 20.62 - 38.30 LPA
   
   - Section 3: Cumulative Salary Thresholds (9 bars)
     - >2 LPA:   95.0% ████████████████████
     - >5 LPA:   95.0% ████████████████████
     - >10 LPA:  80.8% ████████████████
     - >15 LPA:  62.5% █████████████
     - >20 LPA:  42.0% ████████
     - >25 LPA:  32.5% █████
     - >30 LPA:  13.4% ███
     - >35 LPA:  7.2%  █
     - >40 LPA:  1.3%
   
   - Section 4: Job Role
     - Show: SDE or other role
     - Display as badge
   
   - Section 5: Recommended Companies
     - Show top 5 companies
     - Display as cards with company names

6. **Action Buttons**
   - Download PDF
   - Export CSV
   - New Prediction (go back to Student ID Input)
   - Home

---

### REQUIRED REACT COMPONENTS

**Component 1: StudentIdInput**
```
Input: Student ID
Action: Validate with API
Output: Show "Update?" dialog or continue to wizard
```

**Component 2: UpdateConfirmation**
```
Show: Student name, last prediction date
Ask: Want to update? YES/NO
Output: Load data for update or start fresh
```

**Component 3: SkillsCollectionWizard**
```
8 Sequential steps with:
- Input fields (each step can have API integration)
- Progress bar (X of 8)
- Previous/Next/Skip buttons
- Validation before Next
- Error messages displayed
```

**Component 4: PredictionLoadingComponent**
```
Show: Spinner + progress steps
Progress: 0% → 100% with status messages
```

**Component 5: ResultsDisplay**
```
Show: All prediction sections
Visualizations: Bars, circles, cards
Actions: Download, Export, New, Home
```

---

### REQUIRED API ENDPOINTS

Create these endpoints in your backend (Flask/FastAPI):

1. `GET /api/student/{studentId}`
   - Returns: `{ exists: bool, name: string, data: object }`

2. `POST /api/integrations/leetcode`
   - Body: `{ username: string }`
   - Returns: `{ score: number, ... }`

3. `POST /api/integrations/github`
   - Body: `{ username: string }`
   - Returns: `{ score: number, ... }`

4. `POST /api/integrations/resume-ats`
   - Body: `FormData { resume: File }`
   - Returns: `{ atsScore: number, ... }`

5. `POST /api/predictions/generate`
   - Body: `{ studentId, dsa_score, project_score, cs_fundamentals_score, aptitude_score, hr_score, resume_ats_score, hackathon_wins, cgpa }`
   - Returns: Full prediction object with all 17 fields

6. `POST /api/predictions/save`
   - Body: `{ studentId, predictions: object }`
   - Returns: `{ success: bool, message: string }`

---

### STATE MANAGEMENT

Use React Context or Redux:

```javascript
{
  currentStep: 0,                    // 0-8 for wizard
  studentId: null,
  studentName: null,
  isLoading: false,
  error: null,
  scores: {
    dsa_score, project_score, cs_fundamentals_score,
    aptitude_score, hr_score, resume_ats_score,
    hackathon_wins, cgpa
  },
  predictions: null,                 // Full prediction object from API
  updateChoice: null                 // 'update' | 'new'
}
```

---

### KEY FEATURES

**Validation:**
- Student ID: 200000-200100, must exist
- Scores: 0-100 (CGPA: 0-10)
- All fields required
- Show error messages inline

**Error Handling:**
- API failure: Show friendly message + Retry button
- Validation: Show which fields are wrong
- Network: Show connection error

**UX:**
- Show progress bar (current step / total)
- Disable Next until all fields valid
- Allow Skip for optional fields
- Show loading spinner during API calls
- Responsive mobile design

**Performance:**
- Cache predictions for 24 hours
- Lazy load company logos
- Memoize components
- Debounce API calls

**Accessibility:**
- ARIA labels on all inputs
- Keyboard navigation (Tab, Enter)
- Color contrast WCAG AA
- Screen reader friendly

---

### DESIGN SPECS

**Colors:**
- Primary: #2563EB (blue)
- Success: #10B981 (green)
- Error: #EF4444 (red)
- Background: #F9FAFB (light gray)

**Typography:**
- Headings: Bold 20-24px
- Labels: Regular 14-16px
- Values: Bold 18-20px

**Components:**
- Cards: Rounded 8-12px, shadow, padding 20px
- Buttons: Primary (solid blue), Secondary (outline)
- Progress: Visual bar 0-100%

**Responsive:**
- Mobile: Single column
- Tablet: Two columns
- Desktop: Full layout

---

### TESTING

Test these scenarios:
1. New student (no existing predictions)
2. Existing student (show update dialog)
3. LeetCode/GitHub API failures (fallback to manual)
4. Resume upload (success + failure)
5. All validations (scores out of range, etc.)
6. PDF download
7. CSV export
8. Mobile responsive

---

### DELIVERY CHECKLIST

- [ ] All 5 components built
- [ ] All 6 API endpoints created
- [ ] State management working
- [ ] 8-step wizard complete
- [ ] Results displaying correctly
- [ ] 9 salary thresholds showing
- [ ] Mobile responsive
- [ ] Accessibility tested
- [ ] Error handling complete
- [ ] PDF export working
- [ ] CSV export working

---

### START HERE

1. **Setup React Project**
   - Create: `npx create-react-app eduplus-ui`
   - Or use existing project

2. **Create Components Directory**
   ```
   src/components/
   ├── StudentIdInput/
   ├── UpdateConfirmation/
   ├── SkillsCollectionWizard/
   ├── PredictionLoadingComponent/
   └── ResultsDisplay/
   ```

3. **Setup State Management**
   - Create Context or Redux store

4. **Create API Service**
   - File: `src/services/api.js`
   - Functions for all 6 endpoints

5. **Build Components** (in this order)
   1. StudentIdInput
   2. SkillsCollectionWizard
   3. ResultsDisplay
   4. UpdateConfirmation
   5. PredictionLoadingComponent

6. **Integrate Backend APIs**
   - Connect to Flask endpoint
   - Handle responses
   - Error handling

7. **Test & Polish**
   - Mobile responsive
   - Accessibility
   - Performance

---

### QUESTIONS TO ASK IF BUILDING

- Should we use Tailwind CSS or custom CSS?
- Redux or React Context for state?
- TypeScript or JavaScript?
- Next.js or Create React App?
- Testing library (Jest, React Testing Library)?

---

**READY TO BUILD?**

Copy this prompt and the full REACT_INTEGRATION_MASTER_PROMPT.md to your AI assistant.
They will have all context needed to build the complete integration.

Good luck! 🚀
