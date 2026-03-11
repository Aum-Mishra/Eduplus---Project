# EDUPLUS REACT INTEGRATION - QUICK START REFERENCE

## ONE-PAGE OVERVIEW

### The Flow
```
Student ID Input
    ↓
Check if Update/New
    ↓
Skills Wizard (8 Steps)
    ├── LeetCode DSA Score
    ├── GitHub Project Score
    ├── Aptitude Score
    ├── HR Score
    ├── Resume ATS Score
    ├── CS Fundamentals Score
    ├── Hackathon Wins
    └── CGPA
    ↓
Calculate Predictions (Loading Screen)
    ↓
Display Results
    ├── Placement Probability
    ├── Salary Prediction + Range
    ├── 9 Salary Thresholds
    ├── Job Role
    └── Recommended Companies
    ↓
Save to Predicted_Data.csv (Automatic)
```

---

## KEY COMPONENTS TO BUILD

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| StudentIdInput | Validate & load student | onSubmit, error, isLoading |
| UpdateConfirmation | Ask update or new | studentName, onConfirm |
| SkillsCollectionWizard | Collect 8 scores | currentStep, onComplete |
| PredictionLoadingComponent | Show progress | isLoading, progress (0-100) |
| ResultsDisplay | Show all results | predictions, studentData |

---

## ESSENTIAL API ENDPOINTS

```
GET  /api/student/{id}                    → Check if student exists
POST /api/integrations/leetcode           → Fetch LeetCode score
POST /api/integrations/github             → Fetch GitHub score
POST /api/integrations/resume-ats         → Analyze resume
POST /api/predictions/generate            → Generate all predictions
POST /api/predictions/save                → Save to CSV
```

---

## PREDICTION DATA STRUCTURE

**Input to `/api/predictions/generate`:**
```json
{
  "studentId": 200015,
  "dsa_score": 85,
  "project_score": 78,
  "cs_fundamentals_score": 82,
  "aptitude_score": 88,
  "hr_score": 90,
  "resume_ats_score": 82,
  "hackathon_wins": 2,
  "cgpa": 8.5
}
```

**Output from API:**
```json
{
  "overall_placement_probability": 86.25,
  "predicted_salary_lpa": 29.46,
  "salary_range_min_lpa": 20.62,
  "salary_range_mid_lpa": 29.46,
  "salary_range_max_lpa": 38.30,
  "prob_salary_gt_2_lpa": 95.0,
  "prob_salary_gt_5_lpa": 95.0,
  "prob_salary_gt_10_lpa": 80.8,
  "prob_salary_gt_15_lpa": 62.5,
  "prob_salary_gt_20_lpa": 42.0,
  "prob_salary_gt_25_lpa": 32.5,
  "prob_salary_gt_30_lpa": 13.4,
  "prob_salary_gt_35_lpa": 7.2,
  "prob_salary_gt_40_lpa": 1.3,
  "predicted_job_role": "SDE",
  "recommended_companies": ["Mindtree", "Walmart", "Zoho", "Wipro", "Bosch"]
}
```

---

## STATE STRUCTURE (Context/Redux)

```javascript
{
  currentStep: 0,                    // 0-8
  studentId: null,
  studentName: null,
  isLoading: false,
  error: null,
  scores: {
    dsa_score: null,
    project_score: null,
    cs_fundamentals_score: null,
    aptitude_score: null,
    hr_score: null,
    resume_ats_score: null,
    hackathon_wins: 0,
    cgpa: null
  },
  predictions: null,                 // Full prediction object
  updateChoice: null                 // 'update' | 'new' | null
}
```

---

## IMPLEMENTATION PRIORITIES

**Phase 1 (MVP - Week 1):**
- [ ] StudentIdInput component
- [ ] SkillsCollectionWizard (basic inputs)
- [ ] Results display (static)
- [ ] Basic API integration

**Phase 2 (Week 2):**
- [ ] UpdateConfirmation logic
- [ ] LeetCode/GitHub integrations
- [ ] Loading states
- [ ] Error handling

**Phase 3 (Week 3):**
- [ ] Advanced visualizations (charts)
- [ ] PDF export
- [ ] Mobile responsiveness
- [ ] Caching/localStorage

**Phase 4 (Week 4):**
- [ ] Polish & optimization
- [ ] Testing
- [ ] Security hardening
- [ ] Deployment

---

## VALIDATION RULES

| Field | Type | Range | Required | Notes |
|-------|------|-------|----------|-------|
| Student ID | Number | 200000-200100 | Yes | Must exist in DB |
| DSA Score | Number | 0-100 | Yes | Can fetch from LeetCode |
| Project Score | Number | 0-100 | Yes | Can fetch from GitHub |
| CS Fundamentals | Number | 0-100 | Yes | Manual entry |
| Aptitude | Number | 0-100 | Yes | Manual entry |
| HR Score | Number | 0-100 | Yes | Manual entry |
| Resume ATS | Number | 0-100 | Yes | Upload & analyze |
| Hackathon Wins | Number | 0+ | Yes | Integer only |
| CGPA | Decimal | 0.0-10.0 | Yes | Two decimals |

---

## UI DISPLAY SPECS

### Placement Probability
- Circular progress indicator
- Size: 200px diameter
- Show: 86.25%
- Color: Green if > 70%, Yellow if 40-70%, Red if < 40%

### Salary Predictions
- Draw horizontal bar showing range
- Min (70% of predicted), Mid (predicted), Max (130% of predicted)
- Example: 20.62 ←→ 29.46 ←→ 38.30 LPA

### Salary Thresholds
- 9 horizontal bars
- Each bar: [Threshold] [Percentage] [Bar Visual]
- Example: ">15 LPA  62.5%  ████████████"
- Bars decrease in length from top to bottom

### Job Role
- Badge/chip display
- Icon if available
- Example: 🔧 SDE

### Companies
- 5 company cards
- Logo, name, brief info
- Clickable to view more details

---

## ERROR MESSAGES

```javascript
const ERROR_MESSAGES = {
  INVALID_ID: "Student ID not found. Please check and try again.",
  API_TIMEOUT: "Connection timeout. Please check your network.",
  LEETCODE_NOT_FOUND: "LeetCode username not found. Try manual entry.",
  GITHUB_NOT_FOUND: "GitHub username not found. Try manual entry.",
  RESUME_UPLOAD_FAILED: "File upload failed. Try again.",
  VALIDATION_ERROR: "Please fill all required fields correctly.",
  PREDICTION_FAILED: "Could not generate predictions. Try again.",
}
```

---

## LOADING STATES

```javascript
const LOADING_STATES = {
  'Initializing': 10,
  'Loading ML models': 20,
  'Calculating placement': 40,
  'Predicting salary': 60,
  'Analyzing job role': 80,
  'Recommending companies': 90,
  'Finalizing': 100,
}
```

Show these messages with progress bar in PredictionLoadingComponent

---

## LOCAL STORAGE KEYS

```javascript
const STORAGE_KEYS = {
  WIZARD_PROGRESS: 'eduplus_wizard_progress_',     // + studentId
  RECENT_STUDENTS: 'eduplus_recent_students',
  CACHED_PREDICTIONS: 'eduplus_predictions_',      // + studentId
  USER_PREFERENCES: 'eduplus_preferences',
}
```

Cache predictions for 24 hours to avoid redundant API calls.

---

## DOWNLOAD EXPORTS

**PDF Export:**
- Include all predictions
- Formatted results
- Student name & ID
- Timestamp
- Company logos if available

**CSV Export:**
- Single row matching Predicted_Data.csv columns
- All 9 salary thresholds in separate columns
- Recommended companies as comma-separated string

---

## RESPONSIVE BREAKPOINTS

```javascript
const BREAKPOINTS = {
  mobile: '640px',      // <= 640px: Single column
  tablet: '1024px',     // 641-1024px: Two columns
  desktop: '1025px+',   // > 1024px: Full layout
}
```

---

## ACCESSIBILITY CHECKLIST

- [ ] All inputs have labels
- [ ] Error messages in color + text
- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Focus indicators visible
- [ ] ARIA labels on dynamic content
- [ ] Color contrast >= 4.5:1 (WCAG AA)
- [ ] Screen reader tested

---

## PERFORMANCE TARGETS

- Page load: < 3 seconds
- API response: < 1 second
- Results display: < 500ms
- PDF generation: < 2 seconds
- Mobile Lighthouse score: > 80

---

## ENVIRONMENT VARIABLES (.env.local)

```
REACT_APP_API_BASE_URL=http://localhost:5000/api
REACT_APP_LEETCODE_API=https://leetcode.com/graphql
REACT_APP_GITHUB_API=https://api.github.com
REACT_APP_ENV=development
```

---

## GIT COMMIT MESSAGE FORMAT

```
[FEATURE] StudentIdInput component - validate and load student
[REFACTOR] Extract API calls to separate service
[BUGFIX] Fix validation error message display
[STYLE] Update colors to match design system
[TEST] Add unit tests for predictions calculation
```

---

**Next Step**: Use the full REACT_INTEGRATION_MASTER_PROMPT.md with an AI to build the complete implementation.
