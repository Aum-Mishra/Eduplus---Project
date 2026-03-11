# EDUPLUS REACT UI INTEGRATION - MASTER PROMPT

## PROJECT OVERVIEW

You are integrating an **EduPlus Placement Prediction System** backend (Python/Flask) with a **React Frontend**.

The system predicts:
- Placement probability
- Salary predictions (point estimate + 9 cumulative probability thresholds)
- Job role recommendations
- Company recommendations

All data is stored in **`data/Predicted_Data.csv`** (NOT in student_profiles_100.csv).

---

## SYSTEM ARCHITECTURE

### Backend (Python)
- **Framework**: Flask (or similar REST API)
- **Core Functions**:
  - `calculate_placement_probabilities()` - Generates all predictions
  - `save_predictions_to_csv()` - Stores predictions in Predicted_Data.csv
  - Data CSV files in `data/` folder

### Frontend (React)
- **Purpose**: Collect student data, trigger predictions, display results
- **Flow**: Sequential steps using modular components
- **Storage**: Display results from backend CSV responses

---

## REQUIRED REACT COMPONENTS

### 1. **StudentIdInput Component**
**Purpose**: Request and validate student ID

**Props**: 
```javascript
{
  onSubmit: (studentId) => void,
  isLoading: boolean,
  error: string | null
}
```

**Logic**:
- Input field for student ID (numbers only, e.g., 200001-200100)
- Validation: Check if student exists (call backend API)
- On valid ID: Show "Update Existing Record?" dialog
- On invalid ID: Display error message

**API Call**:
```
GET /api/student/{studentId}
Response: { exists: boolean, name: string, data: {...} }
```

---

### 2. **UpdateConfirmation Component**
**Purpose**: Ask if student wants to update existing record

**Props**:
```javascript
{
  studentId: number,
  studentName: string,
  existingData: object,
  onConfirm: (updateChoice) => void,
  onCancel: () => void
}
```

**Display**:
- Student name and ID
- Summary of last prediction (if exists)
- "Update Record?" with YES/NO buttons
- If NO: Cancel and return to StudentIdInput

**Logic**:
- If YES: Proceed to SkillsCollectionWizard
- If NO: End session or return to start

---

### 3. **SkillsCollectionWizard Component**
**Purpose**: Collect all student skills sequentially (like main.py multi-step flow)

**Sub-Components** (Sequential Tabs/Steps):

#### Step 1: LeetCode DSA Score
- Input: LeetCode username (optional)
- If provided: Fetch score from LeetCode API
- If not provided: Allow manual score input (0-100)
- Validation: Score must be 0-100
- Display message: "Fetching your LeetCode profile..."

#### Step 2: GitHub Project Score
- Input: GitHub username (optional)
- If provided: Analyze GitHub projects, count contributions, languages used
- If not provided: Manual input (0-100)
- Validation: Score must be 0-100

#### Step 3: Aptitude Test Score
- Input: Either manual score (0-100) or external aptitude test link
- Display: "Enter your aptitude test score"
- Validation: 0-100 range

#### Step 4: HR Round Score
- Input: Manual score (0-100)
- Display: "How did you perform in HR round? (0-100)"
- Validation: 0-100 range

#### Step 5: Resume ATS Score
- Input: Upload resume file (PDF/DOCX)
- Backend processes and calculates ATS score
- Display: "Uploading and analyzing your resume..."
- Response: ATS score (0-100)

#### Step 6: Resume/Project Score (CS Fundamentals)
- Input: Manual score (0-100)
- Display: "CS Fundamentals Score (0-100)"
- Validation: 0-100 range

#### Step 7: Hackathon Wins
- Input: Number of hackathons won (0-N)
- Display: "How many hackathons have you won?"
- Validation: Integer >= 0

#### Step 8: CGPA
- Input: CGPA score (0-10)
- Display: "Enter your CGPA"
- Validation: 0.0-10.0 range

**Component Structure**:
```javascript
<SkillsCollectionWizard
  studentId={studentId}
  existingData={previousData}
  onComplete={handleSkillsComplete}
  onCancel={handleCancel}
  currentStep={step}
/>
```

**Features**:
- Progress bar showing current step (1/8, 2/8, etc.)
- "Previous" & "Next" buttons
- "Skip" option for optional fields
- Show validation errors inline
- Save incomplete progress to localStorage
- Loading spinner for API calls

---

### 4. **PredictionLoadingComponent**
**Purpose**: Display processing message while predictions are calculated

**Props**:
```javascript
{
  isLoading: boolean,
  progress: number // 0-100
}
```

**Display**:
- Animated spinner
- "Calculating placement predictions..."
- Progress steps:
  - "Loading ML models..." (20%)
  - "Calculating placement probability..." (40%)
  - "Predicting salary..." (60%)
  - "Recommending companies..." (80%)
  - "Finalizing..." (100%)

---

### 5. **ResultsDisplay Component**
**Purpose**: Show all prediction results in organized format

**Props**:
```javascript
{
  predictions: {
    overall_placement_probability: number,
    predicted_salary_lpa: number,
    salary_range_min_lpa: number,
    salary_range_mid_lpa: number,
    salary_range_max_lpa: number,
    prob_salary_gt_2_lpa: number,
    prob_salary_gt_5_lpa: number,
    ... (all 9 thresholds),
    predicted_job_role: string,
    recommended_companies: string[]
  },
  studentData: object
}
```

**Display Sections**:

**Section 1: Placement Probability**
```
[PLACEMENT PROBABILITY]
Overall Placement: 86.25%

Visual: Circular progress indicator (0-100%)
```

**Section 2: Salary Predictions**
```
[SALARY PREDICTIONS]
Predicted Salary: 29.46 LPA
Salary Range: 20.62 - 38.30 LPA (min-max range)

Visual: Horizontal salary bar showing range
```

**Section 3: Cumulative Salary Probability Thresholds**
```
[CUMULATIVE SALARY THRESHOLDS]

>2 LPA:   95.0% ████████████████████
>5 LPA:   95.0% ████████████████████
>10 LPA:  80.8% ████████████████
>15 LPA:  62.5% █████████████
>20 LPA:  42.0% ████████
>25 LPA:  32.5% █████
>30 LPA:  13.4% ███
>35 LPA:  7.2%  █
>40 LPA:  1.3%

Visual: Horizontal bar charts for each threshold
```

**Section 4: Job Role Prediction**
```
[PREDICTED JOB ROLE]
Role: SDE (Software Development Engineer)

Visual: Badge or tag display
```

**Section 5: Recommended Companies**
```
[RECOMMENDED COMPANIES]
1. Mindtree
2. Walmart Global Tech
3. Zoho
4. Wipro
5. Bosch

Visual: Card/list layout with company logos if available
```

**Additional UI Elements**:
- Download Results as PDF button
- Export to CSV button
- Share Results button
- New Prediction button
- Back to Home button

---

## API ENDPOINTS REQUIRED

### 1. Student Validation
```
GET /api/student/{studentId}
Response:
{
  "exists": true,
  "name": "John Doe",
  "lastPrediction": "2026-03-06",
  "data": {...}
}
```

### 2. LeetCode Integration
```
POST /api/integrations/leetcode
Body: { username: string }
Response:
{
  "score": 85,
  "problems_solved": 450,
  "level": "Advanced",
  "timestamp": "2026-03-07T10:30:00Z"
}
```

### 3. GitHub Integration
```
POST /api/integrations/github
Body: { username: string }
Response:
{
  "score": 75,
  "repositories": 15,
  "contributions": 1200,
  "languages": ["Python", "JavaScript"],
  "timestamp": "2026-03-07T10:31:00Z"
}
```

### 4. Resume ATS Analysis
```
POST /api/integrations/resume-ats
Body: FormData { resume: File }
Response:
{
  "atsScore": 82,
  "keywordsFound": ["Python", "ML", "DSA"],
  "keywordsMissing": ["Docker", "Kubernetes"],
  "timestamp": "2026-03-07T10:32:00Z"
}
```

### 5. Generate Predictions
```
POST /api/predictions/generate
Body:
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
Response:
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

### 6. Save Prediction
```
POST /api/predictions/save
Body:
{
  "studentId": 200015,
  "predictions": {...}
}
Response:
{
  "success": true,
  "message": "Prediction saved to Predicted_Data.csv",
  "timestamp": "2026-03-07T10:33:00Z"
}
```

---

## REACT COMPONENT TREE

```
App.tsx
├── MainLayout
│   ├── Navbar
│   └── MainContainer
│       ├── StudentIdInput
│       │   ├── Input Field
│       │   └── Validate Button
│       │
│       ├── UpdateConfirmation (conditional)
│       │   ├── Student Summary
│       │   ├── Yes Button
│       │   └── No Button
│       │
│       ├── SkillsCollectionWizard
│       │   ├── Step 1: LeetCode
│       │   ├── Step 2: GitHub
│       │   ├── Step 3: Aptitude
│       │   ├── Step 4: HR Round
│       │   ├── Step 5: Resume ATS
│       │   ├── Step 6: CS Fundamentals
│       │   ├── Step 7: Hackathon
│       │   ├── Step 8: CGPA
│       │   ├── Progress Bar
│       │   └── Navigation (Prev/Next/Skip)
│       │
│       ├── PredictionLoadingComponent (conditional)
│       │   └── Progress Indicators
│       │
│       └── ResultsDisplay (conditional)
│           ├── Placement Probability Card
│           ├── Salary Predictions Card
│           ├── Cumulative Thresholds Card
│           ├── Job Role Card
│           ├── Companies Card
│           └── Action Buttons
```

---

## STATE MANAGEMENT

Use React Context or Redux:

```javascript
{
  // Current Step
  currentStep: 0, // 0-8 (9 steps total)
  
  // Student Info
  studentId: null,
  studentName: null,
  
  // Collected Scores
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
  
  // Predictions
  predictions: null,
  
  // UI State
  isLoading: false,
  error: null,
  loadingProgress: 0,
  updateChoice: null, // null | 'update' | 'new'
}
```

---

## DATA FLOW (SEQUENTIAL)

1. **User enters Student ID**
   - API call: GET `/api/student/{studentId}`
   - If exists: Show "Update?" dialog
   - If not exists: Start new prediction

2. **User chooses to update or create new**
   - If update: Load existing scores as defaults in wizard
   - If new: Start with blank form

3. **User completes Skills Wizard (8 steps)**
   - Step 1-8: Collect scores with validation
   - Each step can have API calls (LeetCode, GitHub, Resume)
   - Progress bar shows completion
   - Validate all required fields before Next button

4. **Generate Predictions**
   - Show loading screen with progress indicators
   - API call: POST `/api/predictions/generate` with all scores
   - Backend calculates predictions
   - Auto-save: POST `/api/predictions/save`

5. **Display Results**
   - Show comprehensive results card
   - Chart visualizations for salary probabilities
   - Company recommendations list
   - Action buttons: Download, Export, Share, New Prediction

6. **Save to Predicted_Data.csv**
   - Automatically done in step 4
   - Student can also manually download CSV export

---

## ERROR HANDLING

**Handle these scenarios**:

1. **Invalid Student ID**
   - Message: "Student ID not found. Please check and try again."
   - Action: Allow retry

2. **API Failures**
   - LeetCode not found: "Username not found. Try manual entry."
   - GitHub not found: "Username not found. Try manual entry."
   - Resume upload failed: "File upload failed. Try again."

3. **Validation Errors**
   - Score out of range: "Score must be between 0-100"
   - Missing required field: "This field is required"
   - Invalid CGPA: "CGPA must be between 0-10"

4. **Network Errors**
   - Timeout: "Connection timeout. Please check your network."
   - API unavailable: "Server unavailable. Try again later."

5. **Prediction Errors**
   - ML model not found: "Models not initialized. Admin action needed."
   - Calculation failure: "Could not calculate predictions. Try again."

---

## STYLING & UX GUIDELINES

### Color Scheme
- **Primary**: Professional blue (#2563EB)
- **Success**: Green (#10B981)
- **Warning**: Yellow (#F59E0B)
- **Error**: Red (#EF4444)
- **Background**: Light gray (#F9FAFB)

### Typography
- **Headings**: Bold, 20-24px
- **Labels**: Regular, 14-16px
- **Values**: Bold, 18-20px for important numbers

### Cards
- Rounded corners (8-12px)
- Subtle shadow
- Padding: 20px
- Border: 1px light gray

### Buttons
- Primary: Solid blue background
- Secondary: Outline style
- Disabled: Grayed out
- Hover: Color transition effect

### Progress Indicators
- Step 1 of 8, 2 of 8, etc.
- Visual progress bar (0-100%)
- Show estimated time remaining

### Data Visualization
- Horizontal bar charts for salary thresholds
- Circular progress for placement probability
- Company cards with logos
- Salary range visualization with min-mid-max

---

## LOCAL STORAGE / CACHING

Cache for 24 hours:
```javascript
{
  'studentId_predictions_200015': {
    data: {...},
    timestamp: '2026-03-07T10:33:00Z'
  }
}
```

Use for:
- Quick re-display of results
- Incomplete wizard progress (save form state)
- Recent students list

---

## MOBILE RESPONSIVENESS

- Mobile-first design
- Touch-friendly buttons (44px minimum)
- Stacked layout on small screens
- Full-width cards
- Readable font sizes (14px+ on mobile)

---

## ACCESSIBILITY REQUIREMENTS

- ARIA labels for all inputs
- Keyboard navigation (Tab, Enter, Escape)
- Color contrast WCAG AA compliant
- Focus indicators visible
- Error messages descriptive
- Screen reader friendly
- Alt text for all images/logos

---

## PERFORMANCE OPTIMIZATION

- Lazy load company logos
- Memoize components with React.memo()
- Code split wizard steps
- Debounce API calls
- Cache API responses
- Compress CSV export
- Optimize chart renders

---

## SECURITY

- Validate all inputs server-side
- Sanitize user data before display
- HTTPS only for API calls
- Rate limit API endpoints
- Authentication: Only logged-in users can predict
- Authorization: Users can only view their own predictions
- CORS properly configured
- No sensitive data in console logs

---

## TESTING CHECKLIST

**Component Tests**:
- [ ] StudentIdInput validates numbers only
- [ ] UpdateConfirmation shows existing data
- [ ] SkillsCollectionWizard steps sequential
- [ ] All validations trigger error messages
- [ ] PredictionLoading shows progress
- [ ] ResultsDisplay renders all sections

**Integration Tests**:
- [ ] End-to-end flow: ID → Skills → Results
- [ ] API calls work correctly
- [ ] Data persists across components
- [ ] Error handling works for all scenarios
- [ ] CSV download works

**API Tests**:
- [ ] All endpoints return correct structure
- [ ] Rate limiting works
- [ ] Error responses properly formatted
- [ ] LeetCode/GitHub integrations work

---

## DEPLOYMENT

1. **Frontend (React)**
   - Build: `npm run build`
   - Deploy to: Vercel/Netlify/S3
   - Environment: `.env.production`

2. **Backend (Flask/API)**
   - Deploy to: Heroku/AWS/GCP
   - Environment variables configured
   - Predicted_Data.csv storage configured

3. **Database**
   - CSV stored in: `/data/Predicted_Data.csv`
   - Backup strategy implemented

---

## SUMMARY OF KEY INTEGRATIONS

### Backend Integration Points:
1. Flask/FastAPI to expose all required endpoints
2. CSV storage to `data/Predicted_Data.csv`
3. ML model loading and predictions
4. Third-party API integrations (LeetCode, GitHub)

### React Integration:
1. Call backend APIs via axios/fetch
2. State management for multi-step form
3. Error handling and user feedback
4. Result visualization and export
5. Responsive mobile-friendly UI

### Data Flow:
Student ID → Skills Collection → Prediction Generation → Results Display → CSV Storage

---

## ADDITIONAL REQUIREMENTS

- Add timestamp to all predictions
- Track prediction history for each student
- Export predictions as PDF with formatting
- Email results option
- Dark mode toggle (optional)
- Internationalization (i18n) if needed
- Analytics tracking for predictions made
- Admin dashboard to view all predictions

---

**END OF MASTER PROMPT**

Use this prompt to instruct the AI on implementing the complete React integration. Be specific about which features to prioritize first.
